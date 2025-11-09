"""
Outlet search endpoint route handlers
"""
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

async def handle_outlets_search(query: str, text_to_sql, outlet_queries):
    """
    Text-to-SQL endpoint for ZUS outlets
    
    Translates natural language queries to SQL, executes them, and returns results.
    """
    # If no query provided, return documentation with examples
    if not query:
        return {
            "message": "ZUS Coffee Outlets - Text-to-SQL Endpoint",
            "description": "Translate natural language queries to SQL and get outlet information",
            "usage": "/outlets?query=<your_natural_language_question>",
            "examples": [
                {
                    "query": "how many outlets in Shah Alam",
                    "description": "Count outlets in a specific city",
                    "sample_sql": "SELECT COUNT(*) as count FROM outlets WHERE city ILIKE 'Shah Alam'",
                    "sample_result": {"count": 29}
                },
                {
                    "query": "show me outlets in malls",
                    "description": "Find outlets by location category",
                    "sample_sql": "SELECT * FROM outlets WHERE location_category ILIKE '%mall%' LIMIT 50",
                    "sample_result": {"results": "List of mall outlets with name, address, city, state"}
                },
                {
                    "query": "give me map links for outlets in Subang",
                    "description": "Get Google Maps URLs for outlets",
                    "sample_sql": "SELECT name, address, city, maps_url FROM outlets WHERE city ILIKE '%Subang%' LIMIT 50",
                    "sample_result": {"results": "List of outlets with Google Maps URLs"}
                },
                {
                    "query": "find outlets in Petaling Jaya",
                    "description": "Search outlets by city name",
                    "sample_sql": "SELECT * FROM outlets WHERE city ILIKE '%Petaling Jaya%' LIMIT 50",
                    "sample_result": {"results": "List of Petaling Jaya outlets"}
                }
            ],
            "available_fields": [
                "id", "name", "location_category", "address", "postal_code", 
                "city", "state", "maps_url", "created_at", "updated_at"
            ],
            "total_outlets": outlet_queries.get_total_count() if outlet_queries else 252,
            "source": "https://zuscoffee.com/category/store/kuala-lumpur-selangor/"
        }
    
    # Execute text-to-SQL query
    try:
        if not text_to_sql:
            raise HTTPException(status_code=500, detail="Text-to-SQL service not available")
        
        logger.info("=" * 80)
        logger.info("🔵 /outlets ENDPOINT CALLED")
        logger.info(f"📝 Query parameter: {query}")
        logger.info("=" * 80)
        
        result = text_to_sql.query(query)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to process query"))
        
        return {
            "query": query,
            "sql": result["sql"],
            "results": result["results"],
            "count": result["count"],
            "success": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /outlets endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
