"""
Backend API Server for ZUS Drinkware Chatbot
Uses Groq (Llama 3.3 70B) + Local Chroma + Supabase

Refactored modular architecture - main entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

# Import configuration and initialization
from config.app_config import (
    cors_origins,
    initialize_groq_llm,
    initialize_chroma_vectorstore,
    initialize_supabase
)

# Import route handlers
from routes.chat_routes import handle_chat, ChatRequest
from routes.product_routes import handle_products_search
from routes.outlet_routes import handle_outlets_search
from routes.calculator_routes import handle_calculate
from routes.utility_routes import handle_health_check, handle_stats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="ZUS Drinkware Chatbot API")

# Add CORS middleware for Vue frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
logger.info("🚀 Initializing services...")
model = initialize_groq_llm()
vectorstore, retriever = initialize_chroma_vectorstore()
outlet_queries, text_to_sql = initialize_supabase()

# ============================================================================
# API Endpoints - Delegated to route handlers
# ============================================================================

@app.get("/health")
async def health():
    """Health check endpoint"""
    return await handle_health_check(model, vectorstore, outlet_queries)

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Main chat endpoint with conversation memory and agentic planning"""
    return await handle_chat(request, model, retriever, text_to_sql, outlet_queries)

@app.get("/products")
async def products_vector_search(query: str = None, k: int = 5):
    """Vector search endpoint for ZUS drinkware products"""
    return await handle_products_search(query, k, vectorstore, model)

@app.get("/outlets")
async def outlets_text_to_sql(query: str = None):
    """Text-to-SQL endpoint for ZUS outlets"""
    return await handle_outlets_search(query, text_to_sql, outlet_queries)

@app.get("/api/stats")
async def stats():
    """Get statistics about available data"""
    return await handle_stats(outlet_queries, vectorstore)

@app.get("/calculate")
async def calculate_endpoint(expression: str = None, text: str = None):
    """Calculator API endpoint for arithmetic operations"""
    return await handle_calculate(expression, text)

# ============================================================================
# Server Entry Point
# ============================================================================


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    # Railway provides PORT env var, fallback to 8000
    port = int(os.getenv("PORT", os.getenv("API_PORT", 8000)))
    
    logger.info(f"🚀 Starting API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

