"""
Product search endpoint route handlers
"""
import logging
from fastapi import HTTPException
from services.product_service import generate_product_summary

logger = logging.getLogger(__name__)

async def handle_products_search(query: str, k: int, vectorstore, model):
    """
    Vector search endpoint for ZUS drinkware products
    
    Retrieves top-k similar products from vector store and returns AI-generated summary.
    """
    # If no query provided, return documentation with examples
    if not query:
        return {
            "message": "ZUS Coffee Products - Vector Search Endpoint",
            "description": "Search drinkware products using semantic similarity and get AI-generated summaries",
            "usage": "/products?query=<user_question>&k=<number_of_results>",
            "parameters": {
                "query": "Natural language question about products (required)",
                "k": "Number of similar products to retrieve (default: 5, max: 20)"
            },
            "examples": [
                {
                    "query": "tumblers for hot drinks",
                    "description": "Find tumblers suitable for hot beverages",
                    "sample_response": "AI-generated summary of top matching tumblers with features and prices"
                },
                {
                    "query": "affordable water bottles under RM50",
                    "description": "Search for budget-friendly water bottles",
                    "sample_response": "Curated list of affordable water bottles with pricing"
                },
                {
                    "query": "large capacity cups for all-day use",
                    "description": "Find large capacity drinkware",
                    "sample_response": "Summary of high-capacity tumblers and bottles"
                },
                {
                    "query": "gift sets or merchandise",
                    "description": "Browse gift options and merchandise",
                    "sample_response": "Overview of available gift sets and accessories"
                }
            ],
            "total_products": 35,
            "source": "https://shop.zuscoffee.com/",
            "vector_store": "Chroma DB with nomic-embed-text embeddings"
        }
    
    # Validate k parameter
    if k < 1 or k > 20:
        raise HTTPException(status_code=400, detail="Parameter 'k' must be between 1 and 20")
    
    # Execute vector search
    try:
        if not vectorstore or not model:
            raise HTTPException(status_code=500, detail="Vector search or LLM service not available")
        
        logger.info("=" * 80)
        logger.info("🔵 /products ENDPOINT CALLED")
        logger.info(f"📝 Query: {query}")
        logger.info(f"🔢 Top-k: {k}")
        logger.info("=" * 80)
        
        # Retrieve top-k products
        retriever_temp = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )
        raw_products = retriever_temp.invoke(query)
        
        logger.info(f"📊 Vector Search Results: {len(raw_products)} products retrieved")
        
        if not raw_products:
            return {
                "query": query,
                "summary": "No products found matching your query. Please try different keywords.",
                "products": [],
                "count": 0,
                "success": True
            }
        
        # Format products list
        products_list = []
        for doc in raw_products:
            content = getattr(doc, "page_content", str(doc))
            meta = getattr(doc, "metadata", {}) or {}
            
            product_info = {
                "description": content,
                "price": meta.get("price") if isinstance(meta, dict) else None,
                "capacity": meta.get("capacity") if isinstance(meta, dict) else None
            }
            products_list.append(product_info)
        
        # Generate AI summary
        summary = generate_product_summary(query, raw_products, model, k)
        
        logger.info("=" * 80)
        
        return {
            "query": query,
            "summary": summary,
            "products": products_list,
            "count": len(products_list),
            "k": k,
            "success": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /products endpoint: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
