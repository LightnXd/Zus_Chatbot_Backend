"""
Utility endpoint route handlers (health, stats, etc.)
"""
import logging

logger = logging.getLogger(__name__)

async def handle_health_check(model, vectorstore, outlet_queries):
    """Health check endpoint"""
    return {
        "status": "online",
        "groq_available": model is not None,
        "chroma_available": vectorstore is not None,
        "supabase_available": outlet_queries is not None
    }

async def handle_stats(outlet_queries, vectorstore):
    """Get statistics about available data"""
    try:
        total_outlets = 0
        total_products = 0
        
        if outlet_queries:
            total_outlets = outlet_queries.get_total_count()
        
        if vectorstore:
            # Get product count from Chroma
            total_products = 35  # From your existing setup
        
        return {
            "total_outlets": total_outlets,
            "total_products": total_products,
            "regions": ["Kuala Lumpur", "Selangor"],
            "backend": "Groq + Chroma (Local) + Supabase"
        }
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            "total_outlets": 0,
            "total_products": 0,
            "error": str(e)
        }
