"""
Product retrieval and formatting service
"""
import logging
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

def format_product(doc) -> str:
    """Format product document with metadata"""
    text = getattr(doc, "page_content", str(doc))
    meta = getattr(doc, "metadata", {}) or {}
    
    try:
        price = meta.get("price") if isinstance(meta, dict) else None
        capacity = meta.get("capacity") if isinstance(meta, dict) else None
    except Exception:
        price = capacity = None
    
    parts = [text]
    if price and price != "None":
        parts.append(f"Price: RM{price}")
    if capacity and capacity != "None":
        parts.append(f"Capacity: {capacity}")
    return " | ".join(parts)

def retrieve_products(question: str, retriever) -> tuple[str, int]:
    """Retrieve products using vector search and return pre-formatted response"""
    import time
    if not retriever:
        return "Not requested", 0
    
    try:
        logger.info(f"🔍 Starting product search for: {question}")
        start_time = time.time()
        
        raw_products = retriever.invoke(question)
        
        search_time = time.time() - start_time
        logger.info(f"⏱️ Vector search completed in {search_time:.2f}s")
        
        if isinstance(raw_products, list):
            products_found = len(raw_products)
            
            # Pre-format like outlet service for faster LLM processing
            if products_found > 0:
                # Parse products into structured data
                products_data = []
                for d in raw_products:
                    text = getattr(d, "page_content", str(d))
                    meta = getattr(d, "metadata", {}) or {}
                    
                    price = meta.get("price") if isinstance(meta, dict) else None
                    capacity = meta.get("capacity") if isinstance(meta, dict) else None
                    
                    # Convert price to float for sorting
                    try:
                        price_float = float(price) if price and price != "None" else 9999999
                    except:
                        price_float = 9999999
                    
                    # Convert capacity to int for sorting (extract number)
                    try:
                        import re
                        capacity_match = re.search(r'(\d+)', capacity) if capacity else None
                        capacity_int = int(capacity_match.group(1)) if capacity_match else 0
                    except:
                        capacity_int = 0
                    
                    products_data.append({
                        'name': text,
                        'price': price,
                        'price_float': price_float,
                        'capacity': capacity,
                        'capacity_int': capacity_int
                    })
                
                # Smart sorting based on query intent
                question_lower = question.lower()
                sort_note = ""
                
                # Price sorting
                if any(kw in question_lower for kw in ['cheap', 'affordable', 'budget', 'inexpensive']):
                    products_data.sort(key=lambda x: x['price_float'])  # Cheapest first
                    sort_note = " (sorted by price, cheapest first)"
                elif any(kw in question_lower for kw in ['expensive', 'pricey', 'premium', 'most expensive', 'priciest']):
                    products_data.sort(key=lambda x: x['price_float'], reverse=True)  # Most expensive first
                    sort_note = " (sorted by price, most expensive first)"
                
                # Capacity sorting
                elif any(kw in question_lower for kw in ['large', 'largest', 'biggest', 'big capacity', 'most capacity']):
                    products_data.sort(key=lambda x: x['capacity_int'], reverse=True)  # Largest first
                    sort_note = " (sorted by capacity, largest first)"
                elif any(kw in question_lower for kw in ['small', 'smallest', 'compact', 'mini', 'least capacity']):
                    products_data.sort(key=lambda x: x['capacity_int'])  # Smallest first
                    sort_note = " (sorted by capacity, smallest first)"
                
                # Generic price mention (default to cheapest)
                elif 'price' in question_lower:
                    products_data.sort(key=lambda x: x['price_float'])
                    sort_note = " (sorted by price, cheapest first)"
                
                # Format products
                product_list = []
                for i, p in enumerate(products_data, 1):
                    parts = [f"{i}. **{p['name']}**"]
                    if p['price'] and p['price'] != "None":
                        parts.append(f"Price: RM{p['price']}")
                    if p['capacity'] and p['capacity'] != "None":
                        parts.append(f"Capacity: {p['capacity']}")
                    product_list.append(" | ".join(parts))
                
                # Build intro with appropriate sort note
                intro = f"We have {products_found} drinkware products available{sort_note}:\n\n"
                
                drinkware = intro + "\n".join(product_list)
            else:
                drinkware = "No products found matching your query."
        else:
            drinkware = f"1. {format_product(raw_products)}"
            products_found = 1
            
        logger.info(f"✅ Products retrieved: {products_found}")
        return drinkware, products_found
    except Exception as e:
        logger.error(f"Error retrieving products: {e}")
        return "Error retrieving products", 0

def generate_product_summary(query: str, raw_products: list, model, k: int = 5) -> str:
    """Generate AI summary for product search results"""
    if not raw_products:
        return "No products found matching your query. Please try different keywords."
    
    # Format products
    products_text = []
    for doc in raw_products:
        content = getattr(doc, "page_content", str(doc))
        meta = getattr(doc, "metadata", {}) or {}
        
        parts = [content]
        if meta.get("price") and meta.get("price") != "None":
            parts.append(f"Price: RM{meta['price']}")
        if meta.get("capacity") and meta.get("capacity") != "None":
            parts.append(f"Capacity: {meta['capacity']}")
        products_text.append(" | ".join(parts))
    
    # Generate AI summary
    summary_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful product recommendation assistant for ZUS Drinkware.

Your task is to summarize the retrieved products in a friendly, informative way.

Guidelines:
- Highlight key features, prices, and capacities
- Group similar products together
- Mention price ranges if applicable
- Suggest which products are best for specific use cases
- Be concise but informative
- Use bullet points for clarity

Retrieved products:
{products}

User question: {question}

Provide a helpful summary of the products that answers the user's question."""),
        ("human", "{question}")
    ])
    
    chain = summary_prompt | model
    result = chain.invoke({
        "products": "\n\n".join([f"{i+1}. {p}" for i, p in enumerate(products_text)]),
        "question": query
    })
    
    summary = result.content if hasattr(result, 'content') else str(result)
    logger.info(f"✅ AI summary generated ({len(summary)} characters)")
    
    return summary
