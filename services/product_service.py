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
    """Retrieve products using vector search"""
    if not retriever:
        return "Not requested", 0
    
    try:
        raw_products = retriever.invoke(question)
        if isinstance(raw_products, list):
            drinkware = "\n".join([format_product(d) for d in raw_products])
            products_found = len(raw_products)
        else:
            drinkware = format_product(raw_products)
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
