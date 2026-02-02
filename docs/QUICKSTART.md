# 🚀 Quick Start Guide - Procurement AI API

## Prerequisites

- Python 3.12+ with virtual environment activated
- PostgreSQL running (Docker or local)
- LLM service running (e.g., LM Studio on http://localhost:1234)

## 1. Start Database

```bash
# Start PostgreSQL container
docker-compose up -d postgres

# Wait for database to be ready (about 5 seconds)
docker-compose ps postgres
```

## 2. Setup Database & Test Organization

```bash
# Run setup script (creates tables + test organization)
./setup_api_test.sh
```

This creates:
- All database tables via Alembic migrations
- Test organization with slug `test-org`
- API Key for testing: `test-org`

## 3. Start API Server

```bash
# Set environment variables and start server
export DATABASE_URL="postgresql://procurement:procurement@localhost:5432/procurement"
export PYTHONPATH=src

# Start API with hot reload
venv/bin/uvicorn procurement_ai.api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: **http://localhost:8000**

## 4. Test the API

### Option A: Run Test Script

```bash
./test_api.sh
```

### Option B: Interactive Documentation

Open in your browser:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Option C: Manual cURL Testing

```bash
# Health check
curl http://localhost:8000/health | python3 -m json.tool

# Submit a tender
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-org" \
  -d '{
    "title": "Cloud Migration Project",
    "description": "Large enterprise needs cloud migration services for 500+ servers including security assessment, data migration, and training.",
    "organization_name": "Tech Corp",
    "deadline": "2026-08-15",
    "estimated_value": "$1,200,000"
  }' | python3 -m json.tool

# List all tenders
curl -H "X-API-Key: test-org" \
  http://localhost:8000/api/v1/tenders | python3 -m json.tool

# Get specific tender (replace {id} with actual ID)
curl -H "X-API-Key: test-org" \
  http://localhost:8000/api/v1/tenders/1 | python3 -m json.tool
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/analyze` | Submit tender for analysis |
| GET | `/api/v1/tenders` | List tenders (paginated) |
| GET | `/api/v1/tenders/{id}` | Get tender with analysis |

## Authentication

All endpoints (except `/health`) require API key authentication:

```bash
-H "X-API-Key: test-org"
```

For testing, use: `test-org`

## Troubleshooting

### Database connection issues

```bash
# Check database is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Verify connection
docker exec procurement-ai-db psql -U procurement -d procurement -c "SELECT 1"
```

### Module not found errors

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=src

# Or use absolute path
export PYTHONPATH=/Users/ARAJI/git/ai_projects/procurement-ai/src
```

### Port already in use

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
venv/bin/uvicorn procurement_ai.api.main:app --port 8001
```

## Environment Variables

Create a `.env` file (optional):

```env
DATABASE_URL=postgresql://procurement:procurement@localhost:5432/procurement
LLM_BASE_URL=http://localhost:1234/v1
LLM_MODEL=local-model
LLM_API_KEY=not-needed
```

## Next Steps

1. **Test with real LLM:** Start LM Studio and test actual tender analysis
2. **Create more organizations:** Add different API keys for testing multi-tenancy
3. **Monitor background tasks:** Check database for analysis results
4. **Load testing:** Use tools like `ab` or `locust` to test performance
5. **Review logs:** Check uvicorn output for processing information

## Notes

- Background processing runs for each submitted tender
- Analysis takes 3-10 seconds depending on LLM response time
- Poll GET `/tenders/{id}` endpoint to check processing status
- Status changes: `processing` → `analyzed` / `rejected` / `error`
