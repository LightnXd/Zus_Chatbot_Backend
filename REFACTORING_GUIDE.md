# Refactored API Server Architecture

## Overview
The `start.py` (formerly `api_server_chroma.py`) has been refactored into a modular architecture for better maintainability and code organization.

## New Directory Structure

```
Zus_Chatbot_Backend/
├── config/
│   └── app_config.py          # Configuration and service initialization
│
├── services/
│   ├── search_routing.py      # Search decision logic (fuzzy matching)
│   ├── outlet_service.py      # Outlet retrieval and formatting
│   └── product_service.py     # Product retrieval and formatting
│
├── routes/
│   ├── chat_routes.py         # /api/chat endpoint handler
│   ├── product_routes.py      # /products endpoint handler
│   ├── outlet_routes.py       # /outlets endpoint handler
│   ├── calculator_routes.py   # /calculate endpoint handler
│   └── utility_routes.py      # /health and /api/stats handlers
│
└── start.py                   # Main entry point (simplified)
```

## Module Responsibilities

### 1. **config/app_config.py**
**Purpose:** Central configuration and service initialization

**Contains:**
- Environment variable loading
- CORS configuration
- `initialize_groq_llm()` - Initialize Groq LLM
- `initialize_chroma_vectorstore()` - Initialize vector store
- `initialize_supabase()` - Initialize database connections
- `SYSTEM_TEMPLATE` - System prompt template

**Key Functions:**
```python
def initialize_groq_llm() -> ChatGroq
def initialize_chroma_vectorstore() -> tuple[Chroma, Retriever]
def initialize_supabase() -> tuple[OutletQueries, OutletTextToSQL]
```

---

### 2. **services/search_routing.py**
**Purpose:** Determine search routing based on user query

**Contains:**
- `fuzzy_match()` - Fuzzy string matching with threshold
- `should_search_products()` - Product search detection
- `should_search_outlets()` - Outlet search detection

**Key Functions:**
```python
def should_search_products(question: str) -> bool
def should_search_outlets(question: str) -> bool
```

---

### 3. **services/outlet_service.py**
**Purpose:** Outlet information retrieval and formatting

**Contains:**
- `get_outlet_info()` - Main outlet retrieval using text-to-SQL
- `get_outlet_info_fallback()` - Fallback search strategies
- `count_outlets_from_response()` - Extract outlet count from formatted response

**Key Functions:**
```python
def get_outlet_info(query: str, text_to_sql, outlet_queries) -> str
def count_outlets_from_response(outlet_info: str) -> int
```

---

### 4. **services/product_service.py**
**Purpose:** Product retrieval and AI summary generation

**Contains:**
- `format_product()` - Format product documents with metadata
- `retrieve_products()` - Vector search for products
- `generate_product_summary()` - AI-generated product summaries

**Key Functions:**
```python
def retrieve_products(question: str, retriever) -> tuple[str, int]
def generate_product_summary(query: str, raw_products: list, model, k: int) -> str
```

---

### 5. **routes/chat_routes.py**
**Purpose:** Main chat endpoint with conversation memory and agentic planning

**Contains:**
- `ChatRequest` model
- `ChatResponse` model
- `handle_chat()` - Complete chat flow with memory, planning, and LLM

**Responsibilities:**
- Session management
- Conversation memory integration
- Agentic planner integration
- Calculator integration
- Product/outlet retrieval orchestration
- Response generation

---

### 6. **routes/product_routes.py**
**Purpose:** Product vector search endpoint

**Contains:**
- `handle_products_search()` - Vector search and AI summary

**Features:**
- Documentation when no query provided
- Semantic similarity search
- AI-generated summaries

---

### 7. **routes/outlet_routes.py**
**Purpose:** Outlet text-to-SQL endpoint

**Contains:**
- `handle_outlets_search()` - Natural language to SQL translation

**Features:**
- Documentation when no query provided
- Text-to-SQL query execution
- Structured outlet data return

---

### 8. **routes/calculator_routes.py**
**Purpose:** Calculator arithmetic operations

**Contains:**
- `handle_calculate()` - Expression and natural language calculation

**Features:**
- Direct expression mode
- Natural language mode
- Documentation when no input provided

---

### 9. **routes/utility_routes.py**
**Purpose:** Health check and statistics

**Contains:**
- `handle_health_check()` - Service availability check
- `handle_stats()` - Database statistics

---

### 10. **start.py** (Main Entry Point)
**Purpose:** Simplified FastAPI application setup

**Now Contains:**
- FastAPI app initialization
- CORS middleware setup
- Service initialization calls
- Endpoint definitions (delegated to route handlers)
- Server startup logic

**Reduced from ~600 lines to ~100 lines**

---

## Benefits of Refactoring

### 1. **Separation of Concerns**
- Each module has a single, well-defined responsibility
- Configuration separate from business logic
- Routes separate from services

### 2. **Improved Maintainability**
- Easier to find and fix bugs
- Changes to one feature don't affect others
- Clear module boundaries

### 3. **Better Testability**
- Each function can be tested independently
- Mock dependencies easily
- Unit tests per module

### 4. **Code Reusability**
- Services can be reused across different routes
- Shared utilities in dedicated modules
- DRY (Don't Repeat Yourself) principle

### 5. **Scalability**
- Easy to add new endpoints
- Easy to add new services
- Clear pattern to follow

### 6. **Readability**
- Smaller, focused files
- Clear naming conventions
- Logical organization

---

## Migration Guide

### Old Code Pattern:
```python
# Everything in api_server_chroma.py (~600 lines)
@app.post("/api/chat")
async def chat(request: ChatRequest):
    # 200 lines of chat logic here...
    pass
```

### New Code Pattern:
```python
# start.py
from routes.chat_routes import handle_chat, ChatRequest

@app.post("/api/chat")
async def chat(request: ChatRequest):
    return await handle_chat(request, model, retriever, text_to_sql, outlet_queries)

# routes/chat_routes.py
async def handle_chat(request, model, retriever, text_to_sql, outlet_queries):
    # 200 lines of chat logic here...
    pass
```

---

## Dependencies Between Modules

```
start.py
├── config/app_config.py
├── routes/chat_routes.py
│   ├── services/product_service.py
│   ├── services/outlet_service.py
│   ├── conversation_memory.py
│   ├── agentic_planner.py
│   └── calculator_tool.py
├── routes/product_routes.py
│   └── services/product_service.py
├── routes/outlet_routes.py
├── routes/calculator_routes.py
│   └── calculator_tool.py
└── routes/utility_routes.py
```

---

## Running the Server

**No changes required!** The server runs with the new entry point:

```powershell
python start.py
```

The refactoring is **backwards compatible** - all endpoints work exactly as before, just with cleaner code organization.

---

## Future Enhancements

With this modular structure, it's now easy to:

1. **Add new endpoints:** Create a new file in `routes/`
2. **Add new services:** Create a new file in `services/`
3. **Add middleware:** Create a new file in `middleware/`
4. **Add tests:** Mirror structure in `tests/` directory
5. **Add database models:** Create `models/` directory
6. **Add validators:** Create `validators/` directory

---

## Testing Recommendations

```
tests/
├── test_config/
│   └── test_app_config.py
├── test_services/
│   ├── test_search_routing.py
│   ├── test_outlet_service.py
│   └── test_product_service.py
└── test_routes/
    ├── test_chat_routes.py
    ├── test_product_routes.py
    └── test_calculator_routes.py
```

---

## Summary

✅ **Before:** 1 file with 600+ lines
✅ **After:** 10 modular files averaging 50-200 lines each
✅ **Result:** Clean, maintainable, scalable architecture

The main `start.py` is now a **thin orchestration layer** that delegates to specialized modules, making the codebase much easier to understand and maintain.
