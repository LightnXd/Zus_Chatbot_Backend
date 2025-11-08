"""
Supabase Outlets Query Interface

Provides functions to query outlets from Supabase:
- Find by city, state, postal code
- Search by name
- Paginated results
- Nearby outlets (with coordinates)

Usage:
    from database.outlet_queries import OutletQueries
    
    queries = OutletQueries()
    outlets = queries.find_by_city("Shah Alam")
    print(f"Found {len(outlets)} outlets in Shah Alam")
"""

import logging
from typing import List, Dict, Optional
from .supabase_schema import get_supabase_client

logger = logging.getLogger(__name__)

class OutletQueries:
    """Query interface for outlets"""
    
    def __init__(self):
        self.client = get_supabase_client()
    
    def get_by_id(self, outlet_id: int) -> Optional[Dict]:
        """Get outlet by ID"""
        try:
            response = self.client.table('outlets').select('*').eq('id', outlet_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting outlet by ID {outlet_id}: {e}")
            return None
    
    def find_by_state(self, state: str, limit: int = None) -> List[Dict]:
        """Get all outlets in a specific state"""
        try:
            query = self.client.table('outlets').select('*').eq('state', state)
            if limit:
                query = query.limit(limit)
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Error finding outlets in state {state}: {e}")
            return []
    
    def find_by_city(self, city: str) -> List[Dict]:
        """Get all outlets in a specific city"""
        try:
            response = self.client.table('outlets').select('*').eq('city', city).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error finding outlets in city {city}: {e}")
            return []
    
    def find_by_postal_code(self, postal_code: str) -> List[Dict]:
        """Get outlets in a specific postal code"""
        try:
            response = self.client.table('outlets').select('*').eq('postal_code', postal_code).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error finding outlets in postal {postal_code}: {e}")
            return []
    
    def search_by_name(self, search_term: str) -> List[Dict]:
        """Search outlets by name (case-insensitive partial match)"""
        try:
            response = self.client.table('outlets').select('*').ilike('name', f'%{search_term}%').execute()
            return response.data
        except Exception as e:
            logger.error(f"Error searching outlets by name '{search_term}': {e}")
            return []
    
    def search_by_address(self, search_term: str) -> List[Dict]:
        """Search outlets by address (case-insensitive partial match)"""
        try:
            response = self.client.table('outlets').select('*').ilike('address', f'%{search_term}%').execute()
            return response.data
        except Exception as e:
            logger.error(f"Error searching outlets by address '{search_term}': {e}")
            return []
    
    def get_all_paginated(self, page: int = 1, per_page: int = 20) -> Dict:
        """Get paginated results"""
        try:
            offset = (page - 1) * per_page
            
            # Get total count
            count_response = self.client.table('outlets').select('id', count='exact').execute()
            total = count_response.count if hasattr(count_response, 'count') else len(count_response.data)
            
            # Get paginated data
            response = self.client.table('outlets').select('*').range(offset, offset + per_page - 1).execute()
            
            return {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page,
                'outlets': response.data
            }
        except Exception as e:
            logger.error(f"Error getting paginated results (page {page}): {e}")
            return {
                'page': page,
                'per_page': per_page,
                'total': 0,
                'pages': 0,
                'outlets': []
            }
    
    def get_total_count(self) -> int:
        """Get total number of outlets"""
        try:
            response = self.client.table('outlets').select('id', count='exact').execute()
            return response.count if hasattr(response, 'count') else len(response.data)
        except Exception as e:
            logger.error(f"Error getting total count: {e}")
            return 0
    
    def get_outlets_by_location_category(self, category: str) -> List[Dict]:
        """Get outlets by location category"""
        try:
            response = self.client.table('outlets').select('*').eq('location_category', category).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error finding outlets by category {category}: {e}")
            return []
    
    def get_cities(self) -> List[str]:
        """Get list of all unique cities"""
        try:
            response = self.client.table('outlets').select('city').execute()
            cities = sorted(list(set([o['city'] for o in response.data if o.get('city')])))
            return cities
        except Exception as e:
            logger.error(f"Error getting cities list: {e}")
            return []
    
    def get_outlets_stats(self) -> Dict:
        """Get statistics about outlets"""
        try:
            outlets = self.client.table('outlets').select('*').execute().data
            
            stats = {
                'total': len(outlets),
                'states': len(set(o.get('state') for o in outlets if o.get('state'))),
                'cities': len(set(o.get('city') for o in outlets if o.get('city'))),
                'by_state': {},
                'by_city': {},
            }
            
            for outlet in outlets:
                state = outlet.get('state', 'Unknown')
                city = outlet.get('city', 'Unknown')
                
                stats['by_state'][state] = stats['by_state'].get(state, 0) + 1
                stats['by_city'][city] = stats['by_city'].get(city, 0) + 1
            
            return stats
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'total': 0, 'error': str(e)}

def demo():
    """Demo the query interface"""
    print("\n" + "="*80)
    print("OUTLET QUERIES - DEMO")
    print("="*80 + "\n")
    
    queries = OutletQueries()
    
    # Get total count
    total = queries.get_total_count()
    print(f"✅ Total outlets in database: {total}")
    
    # Get by state
    selangor = queries.find_by_state("Selangor")
    print(f"✅ Outlets in Selangor: {len(selangor)}")
    
    # Get cities
    cities = queries.get_cities()
    print(f"✅ Unique cities: {len(cities)}")
    if cities:
        print(f"   Cities: {', '.join(cities[:5])}{'...' if len(cities) > 5 else ''}")
    
    # Get first city
    if cities:
        first_city = cities[0]
        city_outlets = queries.find_by_city(first_city)
        print(f"✅ Outlets in {first_city}: {len(city_outlets)}")
        if city_outlets:
            print(f"   Example: {city_outlets[0]['name']}")
    
    # Get paginated
    page = queries.get_all_paginated(page=1, per_page=5)
    print(f"✅ Paginated (first 5): {len(page['outlets'])} of {page['total']} total")
    
    # Get stats
    stats = queries.get_outlets_stats()
    print(f"✅ Statistics: {stats['total']} outlets, {stats['states']} states, {stats['cities']} cities")
    
    print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    demo()
