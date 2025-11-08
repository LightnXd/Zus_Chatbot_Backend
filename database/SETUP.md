# Task #7: Outlets Database - Supabase Setup Guide

## 🚀 Quick Start

### 1. Create Supabase Project

1. Go to https://app.supabase.com
2. Click "New Project"
3. Fill in:
   - Project name: `zus-outlets` (or your choice)
   - Database password: (generate a strong one)
   - Region: Choose closest to you (e.g., `Singapore` for Malaysia)
4. Click "Create new project" and wait (~2 minutes)

### 2. Get API Keys

1. Go to Project Settings → API
2. Copy these two values:
   - **Project URL** (looks like: `https://xxxxx.supabase.co`)
   - **anon key** (public key under "Project API keys")

### 3. Create .env File

Create file: `c:\Users\User\mini_proj\test\.env`

```
SUPABASE_URL=https://your-project-url.supabase.co
SUPABASE_KEY=your-anon-key-here
```

### 4. Create Database Schema

Option A: Using Python
```bash
cd C:\Users\User\mini_proj\test
python ingestion/supabase_schema.py
```

Option B: Manual SQL
1. In Supabase dashboard, go to SQL Editor
2. Click "New Query"
3. Copy this SQL and paste:

```sql
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
```

4. Click "Run"

### 5. Load Outlets Data

```bash
cd C:\Users\User\mini_proj\test
python ingestion/load_outlets.py
```

Expected output:
```
OUTLETS LOADING COMPLETE
================================================================================
Total records processed: 253
Successfully inserted:   253
Successfully updated:    0
Duplicates found:        0
Errors encountered:      0
================================================================================
```

### 6. Test Queries

```bash
python ingestion/outlet_queries.py
```

Expected output:
```
OUTLET QUERIES - DEMO
================================================================================

✅ Total outlets in database: 253
✅ Outlets in Selangor: 253
✅ Unique cities: 9
   Cities: Ampang, Bandar Menjalara, Bandar Kinrara, Cyberjaya, Klang...
✅ Outlets in Ampang: 3
   Example: ZUS Coffee – Spectrum Shopping Mall
✅ Paginated (first 5): 5 of 253 total
✅ Statistics: 253 outlets, 1 states, 9 cities
```

---

## 📁 Files Created

1. **ingestion/supabase_schema.py** (80 lines)
   - Supabase connection setup
   - SQL schema definition
   - Database initialization

2. **ingestion/load_outlets.py** (140 lines)
   - Load JSONL → Supabase
   - Duplicate detection
   - Progress tracking

3. **ingestion/outlet_queries.py** (200 lines)
   - Query interface
   - 10+ query functions
   - Demo function

---

## 🔧 Available Query Functions

```python
from ingestion.outlet_queries import OutletQueries

queries = OutletQueries()

# Get single outlet
outlet = queries.get_by_id(1)

# Find by location
outlets = queries.find_by_state("Selangor")      # 253 outlets
outlets = queries.find_by_city("Shah Alam")      # 2 outlets
outlets = queries.find_by_postal_code("40150")   # 3 outlets

# Search
outlets = queries.search_by_name("Spectrum")     # 1 outlet
outlets = queries.search_by_address("Jalan")     # Many outlets

# Get paginated results
page = queries.get_all_paginated(page=1, per_page=20)
# Returns: {page, per_page, total, pages, outlets}

# Get statistics
stats = queries.get_outlets_stats()
# Returns: {total, states, cities, by_state, by_city}

# Get all cities
cities = queries.get_cities()
```

---

## 🔐 Security Notes

- Never commit `.env` to Git
- Keep `SUPABASE_KEY` secret
- Add `.env` to `.gitignore`
- For production, use separate keys/roles

---

## ✅ Success Checklist

- [ ] Supabase project created
- [ ] API keys copied to `.env`
- [ ] Database schema created
- [ ] 253 outlets loaded successfully
- [ ] Query demo runs without errors
- [ ] Can search outlets by city/state

---

## 🎯 Next Steps

1. **Integrate with main.py** - Add outlet queries to RAG chatbot
2. **Build web interface** - List, search, filter outlets
3. **Add geolocation** - Find nearby outlets
4. **Add product integration** - Link outlets with products

---

## 📞 Troubleshooting

### "Missing SUPABASE_URL or SUPABASE_KEY"
- Create `.env` file in project root
- Copy API keys from Supabase dashboard

### "Connection refused"
- Check SUPABASE_URL is correct
- Check internet connection
- Verify project is active on Supabase

### "Table does not exist"
- Run schema setup: `python ingestion/supabase_schema.py`
- Or manually run SQL from Supabase dashboard

### "Auth error"
- Verify `SUPABASE_KEY` is correct
- Check it's the `anon` key, not the service role key

---

**Created:** 2025-11-03  
**Task:** #7 Outlets DB & Loader  
**Status:** ✅ Complete
