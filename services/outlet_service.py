"""
Outlet information retrieval service
"""
import logging
import re

logger = logging.getLogger(__name__)

def get_outlet_info(query: str, text_to_sql, outlet_queries) -> str:
    """Retrieve outlet information using text-to-SQL"""
    if not text_to_sql:
        logger.warning("⚠️  text_to_sql is None, returning default message")
        return "Outlets available across Kuala Lumpur and Selangor regions"
    
    try:
        result = text_to_sql.query(query)
        if result["success"] and result["results"]:
            results = result["results"]
            
            if len(results) == 1 and 'count' in results[0]:
                count = results[0]['count']
                sql_lower = result['sql'].lower()
                
                if 'where' in sql_lower:
                    if 'selangor' in sql_lower:
                        return f"There are {count} outlets in Selangor."
                    elif 'kuala lumpur' in sql_lower or 'kl' in sql_lower:
                        return f"There are {count} outlets in Kuala Lumpur."
                    elif any(city_kw in sql_lower for city_kw in ['shah alam', 'petaling jaya', 'subang', 'klang']):
                        return f"There are {count} outlets matching your location."
                    else:
                        return f"There are {count} outlets matching your criteria."
                return f"There are {count} outlets in total."
            
            sql_lower = result['sql'].lower()
            is_maps_request = 'maps_url' in sql_lower or 'map' in query.lower() or 'google' in query.lower() or 'location link' in query.lower()
            
            if len(results) > 10:
                if is_maps_request:
                    outlet_list = "\n".join([
                        f"• {o.get('name', 'N/A')} - {o.get('address', 'N/A')} ({o.get('city', 'N/A')}, {o.get('state', 'N/A')})\n  📍 Map: {o.get('maps_url', 'Not available')}"
                        for o in results[:5]
                    ])
                else:
                    outlet_list = "\n".join([
                        f"• {o.get('name', 'N/A')} - {o.get('address', 'N/A')} ({o.get('city', 'N/A')}, {o.get('state', 'N/A')})"
                        for o in results[:5]
                    ])
                return (f"Found {len(results)} outlets total. Here are the first 5:\n\n{outlet_list}\n\n"
                       f"For more specific results, please provide additional details like city, area, or mall name.")
            
            if is_maps_request:
                outlet_text = "\n".join([
                    f"• {o.get('name', 'N/A')} - {o.get('address', 'N/A')} ({o.get('city', 'N/A')}, {o.get('state', 'N/A')})\n  📍 Map: {o.get('maps_url', 'Not available')}"
                    for o in results
                ])
            else:
                outlet_text = "\n".join([
                    f"• {o.get('name', 'N/A')} - {o.get('address', 'N/A')} ({o.get('city', 'N/A')}, {o.get('state', 'N/A')})"
                    for o in results
                ])
            
            return outlet_text if outlet_text else "No outlets found matching your criteria"
        else:
            logger.warning("⚠️  Text-to-SQL failed, falling back to keyword search")
            return get_outlet_info_fallback(query, outlet_queries)
            
    except Exception as e:
        logger.error(f"❌ Error in text-to-SQL outlet query: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return get_outlet_info_fallback(query, outlet_queries)

def get_outlet_info_fallback(query: str, outlet_queries) -> str:
    """Fallback outlet search using hardcoded methods"""
    if not outlet_queries:
        return "Outlets available across Kuala Lumpur and Selangor regions"
    
    try:
        # Strategy 1: Search by name
        results = outlet_queries.search_by_name(query)
        if results:
            outlet_text = "\n".join([
                f"• {o.get('name', 'N/A')} - {o.get('address', 'N/A')} ({o.get('city', 'N/A')}, {o.get('state', 'N/A')})"
                for o in results[:5]
            ])
            return outlet_text or "No outlets found"
        
        # Strategy 2: Search by address
        results = outlet_queries.search_by_address(query)
        if results:
            outlet_text = "\n".join([
                f"• {o.get('name', 'N/A')} - {o.get('address', 'N/A')} ({o.get('city', 'N/A')}, {o.get('state', 'N/A')})"
                for o in results[:5]
            ])
            return outlet_text or "No outlets found"
        
        # Strategy 3: Extract each word and try as search terms
        words = query.lower().split()
        significant_words = [w for w in words if len(w) > 3]
        
        for word in significant_words:
            results = outlet_queries.search_by_name(word)
            if results:
                outlet_text = "\n".join([
                    f"• {o.get('name', 'N/A')} - {o.get('address', 'N/A')} ({o.get('city', 'N/A')}, {o.get('state', 'N/A')})"
                    for o in results[:5]
                ])
                return outlet_text or "No outlets found"
        
        # Strategy 4: Look for known cities
        all_cities = outlet_queries.get_cities()
        query_lower = query.lower()
        for city in all_cities:
            if city.lower() in query_lower:
                results = outlet_queries.find_by_city(city)
                if results:
                    outlet_text = "\n".join([
                        f"• {o.get('name', 'N/A')} - {o.get('address', 'N/A')} ({o.get('city', 'N/A')}, {o.get('state', 'N/A')})"
                        for o in results[:5]
                    ])
                    return outlet_text or "No outlets found"
        
        return "Outlets available across Kuala Lumpur and Selangor regions"
    except Exception as e:
        logger.error(f"Error querying outlets: {e}")
        return "Outlets available across Kuala Lumpur and Selangor regions"

def count_outlets_from_response(outlet_info: str) -> int:
    """Count outlets from formatted outlet response"""
    # Count outlets from bullet points, or extract from count messages
    if '•' in outlet_info:
        return len([x for x in outlet_info.split('\n') if x.startswith('•')])
    elif 'Found' in outlet_info and 'outlets' in outlet_info:
        match = re.search(r'Found (\d+) outlets', outlet_info)
        if match:
            return int(match.group(1))
    elif 'There are' in outlet_info and 'outlets' in outlet_info:
        match = re.search(r'There are (\d+) outlets', outlet_info)
        if match:
            return int(match.group(1))
    return 0
