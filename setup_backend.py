"""
Backend Setup Script
Initializes Chroma vector DB and loads Supabase outlets
Run this ONCE during backend deployment or first-time setup
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment (optional - Railway provides env vars directly)
env_path = Path(__file__).parent / ".env.backend"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment from {env_path}")
else:
    print("ℹ️  Using system environment variables (Railway/production mode)")

print("=" * 60)
print("  ZUS DRINKWARE BACKEND SETUP")
print("=" * 60)
print()

# Check data files exist
data_dir = Path(__file__).parent / "data"
products_file = data_dir / "products_drinkware.jsonl"
outlets_file = data_dir / "outlets_kuala_lumpur_selangor.jsonl"

if not data_dir.exists():
    print("❌ ERROR: data/ folder not found!")
    print("   Copy data from scraping repo:")
    print("   cp -r ../scraping/data/ ./data/")
    sys.exit(1)

if not products_file.exists():
    print(f"❌ ERROR: {products_file} not found!")
    sys.exit(1)

if not outlets_file.exists():
    print(f"❌ ERROR: {outlets_file} not found!")
    sys.exit(1)

print(f"✅ Found data files:")
print(f"   - {products_file}")
print(f"   - {outlets_file}")
print()

# Step 1: Initialize Chroma Vector DB
print("Step 1: Building Chroma Vector Database...")
print("-" * 60)

try:
    from langchain_ollama import OllamaEmbeddings
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    import json
    
    # Initialize embeddings
    print("Connecting to Ollama (nomic-embed-text)...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    # Create vector store
    db_location = "./chroma_db"
    collection_name = "drinkware_collection"
    
    print(f"Creating Chroma collection: {collection_name}")
    vector_store = Chroma(
        collection_name=collection_name,
        persist_directory=db_location,
        embedding_function=embeddings
    )
    
    # Load products
    print(f"Loading products from {products_file}...")
    documents = []
    ids = []
    
    with open(products_file, 'r', encoding='utf-8') as f:
        for index, line in enumerate(f):
            try:
                product = json.loads(line)
                
                name = str(product.get("name", ""))
                description = str(product.get("description", ""))
                capacity = str(product.get("capacity", "") or "")
                price = str(product.get("price_min", ""))
                
                # Generate a unique ID for this document
                doc_id = str(product.get("id", f"doc_{index}"))
                
                document = Document(
                    page_content=" ".join([name, description, capacity, price]).strip(),
                    metadata={
                        "name": name,
                        "price": price,
                        "capacity": capacity,
                        "url": product.get("url", ""),
                        "vendor": product.get("vendor", ""),
                        "product_type": product.get("product_type", ""),
                        "created_at": product.get("created_at", ""),
                    }
                )
                
                documents.append(document)
                ids.append(doc_id)
            except json.JSONDecodeError as e:
                print(f"⚠️  Error parsing line {index + 1}: {e}")
                continue
    
    if documents:
        print(f"Adding {len(documents)} products to Chroma...")
        try:
            vector_store.add_documents(documents=documents, ids=ids)
            print(f"✅ Chroma DB created with {len(documents)} products")
        except Exception as e:
            print(f"❌ Error adding documents: {e}")
            import traceback
            traceback.print_exc()
            raise
    else:
        print("⚠️  No documents to add")
    
except ImportError as e:
    print(f"❌ ERROR: Missing dependencies - {e}")
    print("   Run: pip install -r requirements-backend.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: Failed to build Chroma DB - {e}")
    sys.exit(1)

print()

# Step 2: Load Outlets to Supabase
print("Step 2: Loading Outlets to Supabase...")
print("-" * 60)

try:
    from supabase import create_client
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("⚠️  WARNING: SUPABASE_URL or SUPABASE_KEY not set")
        print("   Skipping Supabase load")
        print("   Set in .env.backend to enable")
    else:
        print(f"Connecting to Supabase...")
        supabase = create_client(supabase_url, supabase_key)
        
        # Load outlets from JSONL file
        print(f"Loading outlets from {outlets_file}...")
        outlets = []
        with open(outlets_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    outlet = json.loads(line)
                    outlets.append(outlet)
        
        print(f"Found {len(outlets)} outlets")
        
        # Check if table exists and has data
        try:
            response = supabase.table('outlets').select('id').limit(1).execute()
            existing_count = len(response.data)
            
            if existing_count > 0:
                print(f"ℹ️  Outlets table already has data")
                print("   To reload, delete existing data in Supabase first")
            else:
                # Batch insert
                batch_size = 100
                for i in range(0, len(outlets), batch_size):
                    batch = outlets[i:i+batch_size]
                    supabase.table('outlets').insert(batch).execute()
                    print(f"   Inserted {i+len(batch)}/{len(outlets)} outlets")
                
                print(f"✅ Loaded {len(outlets)} outlets to Supabase")
        except Exception as e:
            print(f"❌ ERROR loading to Supabase: {e}")
            print("   Make sure 'outlets' table exists")
            print("   Run database/supabase_schema.py to create table")
            
except ImportError:
    print("⚠️  WARNING: supabase package not installed")
    print("   Run: pip install supabase")
except Exception as e:
    print(f"❌ ERROR: {e}")

print()
print("=" * 60)
print("  SETUP COMPLETE")
print("=" * 60)
print()
print("Next steps:")
print("1. Start Ollama: ollama serve")
print("2. Start backend: python start.py")
print("3. Test: curl http://localhost:8000/health")
print()
