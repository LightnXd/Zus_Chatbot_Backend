"""
Application configuration and initialization
"""
import os

# Disable ChromaDB telemetry (anonymous usage analytics)
os.environ["CHROMA_TELEMETRY_ENABLED"] = "0"

import logging
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Load environment variables from .env.backend
env_path = Path(__file__).parent.parent / ".env.backend"
load_dotenv(dotenv_path=env_path, override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
logger.info(f"CORS allowed origins: {cors_origins}")

def initialize_groq_llm():
    """Initialize Groq LLM (Llama 3.3 70B)"""
    try:
        model = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.7,
            max_retries=2
        )
        logger.info("✅ Groq LLM initialized (Llama 3.3 70B)")
        return model
    except Exception as e:
        logger.error(f"❌ Failed to initialize Groq: {e}")
        return None

def initialize_chroma_vectorstore():
    """Initialize Chroma Vector Store with HuggingFace embeddings"""
    try:
        # Use HuggingFace embeddings (fast, works everywhere)
        logger.info("🚀 Using HuggingFace embeddings (sentence-transformers/all-MiniLM-L6-v2)")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Load local Chroma database
        vectorstore = Chroma(
            collection_name="drinkware_collection",
            persist_directory="./chroma_db",
            embedding_function=embeddings
        )
        
        # Check if collection is empty and populate if needed
        try:
            collection = vectorstore._collection
            count = collection.count()
            logger.info(f"📊 ChromaDB collection has {count} items")
            
            if count == 0:
                logger.warning("⚠️ ChromaDB collection is empty! Running setup to populate...")
                import subprocess
                import sys
                result = subprocess.run(
                    [sys.executable, "setup_backend.py"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode == 0:
                    logger.info("✅ ChromaDB populated successfully")
                    # Reload the collection
                    vectorstore = Chroma(
                        collection_name="drinkware_collection",
                        persist_directory="./chroma_db",
                        embedding_function=embeddings
                    )
                else:
                    logger.error(f"❌ Setup failed: {result.stderr}")
        except Exception as setup_error:
            logger.warning(f"⚠️ Could not check/populate ChromaDB: {setup_error}")
        
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        logger.info("✅ Chroma vector store initialized (LOCAL)")
        return vectorstore, retriever
    except Exception as e:
        logger.error(f"❌ Failed to initialize Chroma: {e}")
        return None, None

def initialize_supabase():
    """Initialize Supabase with Text-to-SQL"""
    try:
        import sys
        from pathlib import Path
        # Add current directory to path if not already there
        current_dir = Path(__file__).parent.parent
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        
        from database.outlet_queries import OutletQueries
        from database.text_to_sql import OutletTextToSQL
        
        outlet_queries = OutletQueries()
        text_to_sql = OutletTextToSQL()
        logger.info("✅ Supabase outlet queries initialized (with text-to-SQL)")
        return outlet_queries, text_to_sql
    except Exception as e:
        logger.error(f"⚠️  Failed to initialize Supabase: {e}")
        return None, None

# System prompt template
SYSTEM_TEMPLATE = """You are a helpful and friendly assistant for ZUS Drinkware - a Malaysian drinkware brand known for tumblers, cups, and reusable products.

You can help users with:
- Product information (tumblers, cups, straws, lids, sleeves)
- Outlet locations across Kuala Lumpur and Selangor
- Google Maps URLs for outlet locations
- Pricing and availability
- General conversation about drinkware

Previous conversation:
{conversation_history}

Relevant drinkware products:
{drinkware}

Relevant outlet locations:
{outlet}

User question: {question}

IMPORTANT INSTRUCTIONS:
- ALWAYS use the information provided in "Relevant outlet locations" and "Relevant drinkware products"
- When outlet information includes Google Maps URLs (📍 Map: ...), present them clearly to users
- When outlet information states "There are X outlets", use this exact information in your response
- When outlet information includes "Found X outlets total" with a sample list, relay this information EXACTLY as provided
- When listing outlets or products, include ALL items provided, do not skip any
- Use bullet points or numbered lists for multiple items
- For price-based queries (cheap, cheapest, budget, affordable), SORT products by price and recommend the LOWEST priced option first
- Be conversational and engaging - ask relevant follow-up questions to help users narrow down their search
- For outlet count queries, offer to help find specific locations by city, area, or mall name
- For product queries, suggest complementary items or ask about specific needs (capacity, price range, etc.)
- DO NOT suggest product listings when the user is asking ONLY about outlet locations or counts
- If you don't have specific information, acknowledge it gracefully and offer alternatives
- USE the previous conversation history to provide context-aware responses and avoid repeating information
- If the user refers to "that" or "it" or "there", check the conversation history for context
"""
