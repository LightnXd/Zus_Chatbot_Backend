"""
Text-to-SQL for Outlet Queries

Converts natural language questions to SQL queries for the outlets table.
Uses Groq LLM to generate SQL and Supabase to execute queries.

Example:
    "Show me outlets in malls" → SELECT * FROM outlets WHERE location_category ILIKE '%mall%'
    "Find outlets in Shah Alam" → SELECT * FROM outlets WHERE city ILIKE 'Shah Alam'
    "How many outlets are in Selangor?" → SELECT COUNT(*) FROM outlets WHERE state ILIKE 'Selangor'
"""

import os
import logging
from typing import List, Dict, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

class OutletTextToSQL:
    """Convert natural language to SQL queries for outlets"""
    
    def __init__(self):
        """Initialize the text-to-SQL system"""
        # Get Groq LLM
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=groq_api_key,
            temperature=0.0,  # Use 0 for deterministic SQL generation
            max_retries=2
        )
        
        # Get Supabase client for direct query execution
        from .supabase_schema import get_supabase_client
        self.supabase = get_supabase_client()
        # Optional: prefer a direct Postgres connection for Text->SQL execution
        # Set `TEXTSQL_DATABASE_URL` in server-side env to make Text->SQL use a restricted DB role
        self.textsql_dsn = os.getenv("TEXTSQL_DATABASE_URL")
        self._have_psycopg = False
        if self.textsql_dsn:
            try:
                import psycopg
                self.psycopg = psycopg
                self._have_psycopg = True
            except Exception as e:
                logger.warning("TEXTSQL_DATABASE_URL is set but psycopg is not available: %s", e)
        
        # Create a custom prompt for SQL generation
        self.sql_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a SQL expert. Convert natural language questions to PostgreSQL queries for the 'outlets' table.

Table schema:
CREATE TABLE outlets (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    location_category TEXT,  -- e.g., 'Mall', 'Stand Alone', 'Petrol Station'
    address TEXT NOT NULL,
    postal_code TEXT,
    city TEXT,               -- e.g., 'Shah Alam', 'Petaling Jaya'
    state TEXT,              -- e.g., 'Selangor', 'Kuala Lumpur'
    maps_url TEXT,
    fetched_at TIMESTAMP,
    source TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

Rules:
1. Use ILIKE for case-insensitive text search
2. Use % wildcards for partial matches
3. Always limit results to 50 unless counting
4. Only return SELECT queries
5. For location queries, search city, state, or address
6. For category queries, use location_category field
7. For map/URL requests, include maps_url field in SELECT or use it in WHERE
8. Return ONLY raw SQL - no markdown, no code blocks, no explanations

Examples:
Q: "Show me outlets in malls"
A: SELECT * FROM outlets WHERE location_category ILIKE '%mall%' LIMIT 50

Q: "Find outlets in Shah Alam"
A: SELECT * FROM outlets WHERE city ILIKE 'Shah Alam' LIMIT 50

Q: "How many outlets in Selangor?"
A: SELECT COUNT(*) as count FROM outlets WHERE state ILIKE 'Selangor'

Q: "Outlets near KLCC"
A: SELECT * FROM outlets WHERE address ILIKE '%KLCC%' OR address ILIKE '%Kuala Lumpur City Centre%' LIMIT 50

Q: "Give me the map location for outlets in Subang"
A: SELECT name, address, city, maps_url FROM outlets WHERE city ILIKE '%Subang%' LIMIT 50

Q: "Show map URL for Temu Business Centre"
A: SELECT name, address, maps_url FROM outlets WHERE name ILIKE '%Temu Business Centre%' LIMIT 50

Q: "Get Google Maps link for outlets in Shah Alam malls"
A: SELECT name, address, maps_url FROM outlets WHERE city ILIKE '%Shah Alam%' AND location_category ILIKE '%mall%' LIMIT 50

Return ONLY the SQL query, no explanations."""),
            ("human", "{question}")
        ])
    
    def generate_sql(self, question: str) -> Optional[str]:
        """
        Generate SQL query from natural language question
        
        Args:
            question: Natural language question about outlets
            
        Returns:
            SQL query string or None if generation fails
        """
        try:
            # Use LLM with custom prompt
            chain = self.sql_prompt | self.llm
            response = chain.invoke({"question": question})
            sql_query = response.content.strip()
            
            # Clean up the SQL
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            return sql_query
                
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            return None
    
    def execute_sql(self, sql_query: str) -> List[Dict]:
        """
        Execute SQL query using Supabase PostgREST API
        
        Args:
            sql_query: SQL query string
            
        Returns:
            List of result dictionaries
        """
        try:
            # If a direct Postgres DSN is configured and psycopg is available, prefer executing there
            if self.textsql_dsn and self._have_psycopg:
                logger.info("TEXTSQL_DATABASE_URL present — attempting direct Postgres execution (will not log DSN)")
                try:
                    return self._execute_with_textsql_conn(sql_query)
                except Exception as e:
                    logger.warning("Direct TEXTSQL execution failed, falling back to Supabase: %s", e)

            # Fallback to Supabase PostgREST API
            logger.info("Using Supabase PostgREST fallback for SQL execution")
            return self._execute_with_postgrest(sql_query)

        except Exception as e:
            logger.error(f"Error executing SQL: {e}")
            return []

    def _execute_with_textsql_conn(self, sql_query: str) -> List[Dict]:
        """
        Execute SQL directly using the DSN provided in `TEXTSQL_DATABASE_URL`.
        This runs the query as the DB role contained in that DSN (e.g., the restricted `agent` role).
        Returns list of dict rows or count for COUNT queries.
        """
        conn = None
        try:
            conn = self.psycopg.connect(self.textsql_dsn)
            with conn.cursor() as cur:
                # Log current DB user (confirm which role the DSN is using)
                try:
                    cur.execute("SELECT current_user;")
                    user_row = cur.fetchone()
                    logger.info("Connected to Postgres as user: %s", user_row[0] if user_row else "(unknown)")
                except Exception:
                    # non-fatal — continue
                    logger.debug("Could not read current_user from Postgres")

                cur.execute(sql_query)

                # If COUNT(*) single-column result
                if cur.description and len(cur.description) == 1 and cur.description[0].name.lower() in ("count", "count(*)"):
                    row = cur.fetchone()
                    return [{"count": int(row[0]) if row and row[0] is not None else 0}]

                # No columns (e.g., DDL) — return empty
                if not cur.description:
                    return []

                cols = [d.name for d in cur.description]
                rows = cur.fetchall()
                results = [dict(zip(cols, row)) for row in rows]
                return results

        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    
    def _execute_with_postgrest(self, sql_query: str) -> List[Dict]:
        """
        Parse SQL and use Supabase PostgREST API
        
        Args:
            sql_query: SQL query string
            
        Returns:
            List of result dictionaries
        """
        sql_lower = sql_query.lower()
        
        # Handle COUNT queries
        if 'count(*)' in sql_lower:
            query = self.supabase.table('outlets').select('*', count='exact')
            
            # Parse WHERE clauses for count
            if 'where' in sql_lower:
                query = self._parse_where_clause(query, sql_query)
            
            response = query.execute()
            count = response.count if hasattr(response, 'count') else 0
            return [{"count": count}]
        
        # Regular SELECT queries
        query = self.supabase.table('outlets').select('*')
        
        # Parse WHERE clauses
        if 'where' in sql_lower:
            query = self._parse_where_clause(query, sql_query)
        
        # Parse LIMIT
        if 'limit' in sql_lower:
            try:
                limit_part = sql_query.split('LIMIT', 1)[1].strip()
                limit = int(limit_part.split()[0])
                query = query.limit(limit)
            except:
                query = query.limit(50)  # Default limit
        else:
            query = query.limit(50)  # Always limit
        
        # Execute
        response = query.execute()
        result = response.data if response.data else []
        return result
    
    def _parse_where_clause(self, query, sql_query: str):
        """
        Parse WHERE clause and apply filters to Supabase query
        
        Args:
            query: Supabase query builder
            sql_query: Original SQL query
            
        Returns:
            Updated query builder
        """
        # Extract WHERE part
        where_part = sql_query.split('WHERE', 1)[1]
        where_part = where_part.split('LIMIT')[0].strip() if 'LIMIT' in where_part else where_part.strip()
        
        # Handle OR conditions
        if ' OR ' in where_part.upper():
            conditions = where_part.split(' OR ')
            or_filters = []
            
            for condition in conditions:
                field, value = self._parse_condition(condition)
                if field and value:
                    or_filters.append(f'{field}.ilike.%{value}%')
            
            if or_filters:
                query = query.or_(','.join(or_filters))
        
        # Handle AND conditions
        elif ' AND ' in where_part.upper():
            conditions = where_part.split(' AND ')
            
            for condition in conditions:
                field, value = self._parse_condition(condition)
                if field and value:
                    query = query.ilike(field, f'%{value}%')
        
        # Single condition
        else:
            field, value = self._parse_condition(where_part)
            if field and value:
                query = query.ilike(field, f'%{value}%')
        
        return query
    
    def _parse_condition(self, condition: str) -> tuple:
        """
        Parse a single WHERE condition
        
        Args:
            condition: WHERE condition (e.g., "city ILIKE 'Shah Alam'")
            
        Returns:
            Tuple of (field, value)
        """
        try:
            if 'ILIKE' in condition.upper():
                parts = condition.split('ILIKE')
                field = parts[0].strip()
                value = parts[1].strip().strip("'").strip('"').replace('%', '')
                return field, value
            elif '=' in condition:
                parts = condition.split('=')
                field = parts[0].strip()
                value = parts[1].strip().strip("'").strip('"')
                return field, value
        except:
            pass
        
        return None, None
    
    def query(self, question: str) -> Dict:
        """
        Full text-to-SQL pipeline: generate SQL and execute
        
        Args:
            question: Natural language question
            
        Returns:
            Dictionary with sql, results, and metadata
        """
        # Generate SQL
        sql_query = self.generate_sql(question)
        
        if not sql_query:
            logger.warning("❌ Failed to generate SQL query")
            return {
                "success": False,
                "error": "Failed to generate SQL query",
                "sql": None,
                "results": []
            }
        
        # Execute SQL
        results = self.execute_sql(sql_query)
        return {
            "success": True,
            "sql": sql_query,
            "results": results,
            "count": len(results) if isinstance(results, list) else 0
        }


def demo():
    """Demo the text-to-SQL system"""
    print("\n" + "="*80)
    print("TEXT-TO-SQL FOR OUTLETS - DEMO")
    print("="*80 + "\n")
    
    try:
        text_to_sql = OutletTextToSQL()
        
        # Test questions
        questions = [
            "Show me outlets in malls",
            "Find outlets in Shah Alam",
            "How many outlets are in Selangor?",
            "Outlets near KLCC",
        ]
        
        for question in questions:
            print(f"\n📝 Question: {question}")
            result = text_to_sql.query(question)
            
            if result["success"]:
                print(f"✅ SQL: {result['sql']}")
                print(f"📊 Results: {result['count']} rows")
                if result['results']:
                    print(f"   First result: {result['results'][0] if isinstance(result['results'], list) else result['results']}")
            else:
                print(f"❌ Error: {result['error']}")
            print("-" * 80)
    
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    demo()
