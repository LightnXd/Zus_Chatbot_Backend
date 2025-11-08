OUTLETS_TABLE_SQL = """
-- Create outlets table
CREATE TABLE IF NOT EXISTS outlets (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    location_category TEXT,
    address TEXT NOT NULL,
    postal_code TEXT,
    city TEXT,
    state TEXT,
    maps_url TEXT,
    fetched_at TIMESTAMP,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_outlets_state ON outlets(state);
CREATE INDEX IF NOT EXISTS idx_outlets_city ON outlets(city);
CREATE INDEX IF NOT EXISTS idx_outlets_postal_code ON outlets(postal_code);
CREATE INDEX IF NOT EXISTS idx_outlets_name ON outlets(name);

-- Create a full-text search index
CREATE INDEX IF NOT EXISTS idx_outlets_name_fts ON outlets USING gin(to_tsvector('english', name));
"""

def get_supabase_client():
    """Initialize Supabase client from environment variables"""
    from supabase import create_client
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        raise ValueError(
            "Missing SUPABASE_URL or SUPABASE_KEY environment variables.\n"
            "Create a .env file with:\n"
            "  SUPABASE_URL=your supabase url\n"
            "  SUPABASE_KEY=your-anon-key"
        )
    
    return create_client(supabase_url, supabase_key)

def setup_database():
    print("📋 To create the database schema, follow these steps:\n")
    print("1. Go to https://app.supabase.com")
    print("2. Select your project")
    print("3. Click 'SQL Editor' in the left sidebar")
    print("4. Click '+ New Query'")
    print("5. Paste the SQL code below and click 'Run':\n")
    print("=" * 40)
    print(OUTLETS_TABLE_SQL)
    return True

if __name__ == "__main__":
    setup_database()
