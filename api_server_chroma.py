"""
Backend API Server for ZUS Drinkware Chatbot
Uses Groq (Llama 3.3 70B) + Local Chroma + Supabase
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma
import os
from dotenv import load_dotenv
import logging
from pathlib import Path

# Load environment variables from .env.backend
env_path = Path(__file__).parent / ".env.backend"
load_dotenv(dotenv_path=env_path, override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="ZUS Drinkware Chatbot API")

# CORS configuration - supports multiple origins
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
logger.info(f"CORS allowed origins: {cors_origins}")

# Add CORS middleware for Vue frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # From environment variable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq LLM (Llama 3.3 70B)
try:
    model = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.7,
        max_retries=2
    )
    logger.info("✅ Groq LLM initialized (Llama 3.3 70B)")
except Exception as e:
    logger.error(f"❌ Failed to initialize Groq: {e}")
    model = None

# Initialize Chroma Vector Store (LOCAL)
try:
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    # Load local Chroma database
    vectorstore = Chroma(
        collection_name="drinkware_collection",
        persist_directory="./chroma_db",
        embedding_function=embeddings
    )
    
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}
    )
    logger.info("✅ Chroma vector store initialized (LOCAL)")
except Exception as e:
    logger.error(f"❌ Failed to initialize Chroma: {e}")
    vectorstore = None
    retriever = None

# Initialize Supabase
try:
    from database import OutletQueries
    outlet_queries = OutletQueries()
    logger.info("✅ Supabase outlet queries initialized")
except Exception as e:
    logger.error(f"⚠️  Failed to initialize Supabase: {e}")
    outlet_queries = None

# System prompt
SYSTEM_TEMPLATE = """You are a helpful assistant for ZUS Drinkware - a Malaysian drinkware brand known for tumblers, cups, and reusable products.

You can help users with:
- Product information (tumblers, cups, straws, lids, sleeves)
- Outlet locations across Kuala Lumpur and Selangor
- Pricing and availability
- General conversation about drinkware

Relevant drinkware products:
{drinkware}

Relevant outlet locations:
{outlet}

User question: {question}

IMPORTANT INSTRUCTIONS:
- When listing outlets or products, include ALL items provided, do not skip any
- Use bullet points or numbered lists for multiple items
- Be concise but complete
- If you don't have specific information, acknowledge it gracefully
"""

# Request/Response models
class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    response: str
    products_found: int
    outlets_found: int
    search_info: dict

# Helper functions
def fuzzy_match(text: str, keywords: list, threshold: float = 0.6) -> bool:
    """Check if any keyword fuzzy matches the text"""
    from difflib import SequenceMatcher
    
    text_lower = text.lower()
    
    # Exact substring match first
    for keyword in keywords:
        if keyword in text_lower:
            return True
    
    # Fuzzy matching for misspellings
    words = text_lower.split()
    for word in words:
        for keyword in keywords:
            ratio = SequenceMatcher(None, word, keyword).ratio()
            if ratio >= threshold:
                return True
    
    return False

def should_search_products(question: str) -> bool:
    """Check if question is about products"""
    product_keywords = [
        'tumbler', 'cup', 'drinkware', 'bottle', 'price', 'cost', 
        'product', 'item', 'capacity', 'size', 'design', 'color', 'material',
        'recommend', 'suggest', 'best', 'water', 'coffee', 'drink', 'hot', 'cold',
        'all day', 'frozee', 'buddy', 'zus', 'merchandise'
    ]
    return fuzzy_match(question, product_keywords)

def should_search_outlets(question: str) -> bool:
    """Check if question is about outlets/locations"""
    outlet_keywords = [
        'outlet', 'location', 'store', 'shop', 'address', 'where', 'near', 
        'nearest', 'branch', 'city', 'area', 'zone', 'kuala lumpur', 'selangor',
        'mall', 'visit', 'open', 'hours', 'available', 'find', 'buy', 'purchase'
    ]
    return fuzzy_match(question, outlet_keywords)

def get_outlet_info(query: str) -> str:
    """Retrieve outlet information from Supabase"""
    if not outlet_queries:
        return "Outlets available across Kuala Lumpur and Selangor regions"
    
    try:
        # Strategy 1: Search by name
        results = outlet_queries.search_by_name(query)
        if results:
            outlet_text = "\n".join([
                f"• {o.get('name', 'N/A')} - {o.get('address', 'N/A')} ({o.get('city', 'N/A')})"
                for o in results[:5]
            ])
            return outlet_text or "No outlets found"
        
        # Strategy 2: Search by address
        results = outlet_queries.search_by_address(query)
        if results:
            outlet_text = "\n".join([
                f"• {o.get('name', 'N/A')} - {o.get('address', 'N/A')} ({o.get('city', 'N/A')})"
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
                    f"• {o.get('name', 'N/A')} - {o.get('address', 'N/A')} ({o.get('city', 'N/A')})"
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
                        f"• {o.get('name', 'N/A')} - {o.get('address', 'N/A')}"
                        for o in results[:5]
                    ])
                    return outlet_text or "No outlets found"
        
        return "Outlets available across Kuala Lumpur and Selangor regions"
    except Exception as e:
        logger.error(f"Error querying outlets: {e}")
        return "Outlets available across Kuala Lumpur and Selangor regions"

def format_product(doc) -> str:
    """Format product document with metadata"""
    text = getattr(doc, "page_content", str(doc))
    meta = getattr(doc, "metadata", {}) or {}
    
    try:
        price = meta.get("price") if isinstance(meta, dict) else None
        capacity = meta.get("capacity") if isinstance(meta, dict) else None
    except Exception:
        price = capacity = None
    
    parts = [text]
    if price and price != "None":
        parts.append(f"Price: RM{price}")
    if capacity and capacity != "None":
        parts.append(f"Capacity: {capacity}")
    return " | ".join(parts)

# API Endpoints
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "online",
        "groq_available": model is not None,
        "chroma_available": vectorstore is not None,
        "supabase_available": outlet_queries is not None
    }

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Main chat endpoint"""
    try:
        if not model:
            raise HTTPException(status_code=500, detail="LLM not initialized")
        
        question = request.question.strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Smart routing
        search_products = should_search_products(question)
        search_outlets = should_search_outlets(question)
        
        # Retrieve products
        drinkware = "Not requested"
        products_found = 0
        if search_products and retriever:
            try:
                raw_products = retriever.invoke(question)
                if isinstance(raw_products, list):
                    drinkware = "\n".join([format_product(d) for d in raw_products])
                    products_found = len(raw_products)
                else:
                    drinkware = format_product(raw_products)
                    products_found = 1
            except Exception as e:
                logger.error(f"Error retrieving products: {e}")
                drinkware = "Error retrieving products"
        
        # Retrieve outlets
        outlet_info = "Not requested"
        outlets_found = 0
        if search_outlets:
            outlet_info = get_outlet_info(question)
            outlets_found = len([x for x in outlet_info.split('\n') if x.startswith('•')])
        
        # Conversational mode - no searches
        if not search_products and not search_outlets:
            drinkware = "Not requested"
            outlet_info = "Not requested"
        
        # Create prompt and chain
        prompt = ChatPromptTemplate.from_template(SYSTEM_TEMPLATE)
        chain = prompt | model
        
        # Generate response
        result = chain.invoke({
            "drinkware": drinkware or "No products found",
            "outlet": outlet_info or "No outlets found",
            "question": question,
        })
        
        # Extract response content
        response_text = result.content if hasattr(result, 'content') else str(result)
        
        return ChatResponse(
            response=response_text,
            products_found=products_found,
            outlets_found=outlets_found,
            search_info={
                "searched_products": search_products,
                "searched_outlets": search_outlets,
                "mode": "product" if search_products else ("outlet" if search_outlets else "conversational")
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def stats():
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

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8001))  # Changed default to 8001
    
    logger.info(f"🚀 Starting API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
