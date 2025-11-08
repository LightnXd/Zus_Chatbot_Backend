"""
Database package for ZUS Coffee data

Modules:
  - supabase_schema: Supabase connection and schema setup
  - load_outlets: Load outlets from JSONL into Supabase
  - outlet_queries: Query interface for outlets

Usage:
    from database.outlet_queries import OutletQueries
    
    queries = OutletQueries()
    outlets = queries.find_by_city("Shah Alam")
"""

from .supabase_schema import get_supabase_client, setup_database
from .outlet_queries import OutletQueries
from ...scraping.load_outlets import OutletsLoader

__all__ = ['get_supabase_client', 'setup_database', 'OutletQueries', 'OutletsLoader']
