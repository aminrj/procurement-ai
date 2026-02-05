# Procurement AI

Procurement AI is a compact, production-focused project for LLM-based tender analysis.

It is designed for two goals:
- Learn and iterate quickly on prompt engineering and orchestration.
- Demonstrate production delivery patterns (API, persistence, migrations, tests, scripts).

## Architecture

Core runtime modules:
- `src/procurement_ai/agents/`: Filter, Rating, and Document Generator agents.
- `src/procurement_ai/orchestration/simple_chain.py`: Sequential pipeline with early-stop conditions.
- `src/procurement_ai/services/llm.py`: OpenAI-compatible structured-output client.
- `src/procurement_ai/storage/`: SQLAlchemy models, DB session management, repositories.
- `src/procurement_ai/api/`: FastAPI REST endpoints and server-side web views.

Pipeline:
1. Filter tender relevance.
2. Rate strategic value and effort.
3. Generate bid document only when score threshold is met.
4. Persist analysis and status updates.

## Requirements

- Python 3.11+
- PostgreSQL (local container is supported)
- Optional local or remote LLM endpoint compatible with OpenAI chat completions

## Quick Start

1. Install dependencies in your environment:
```bash
pip install -r requirements.txt
pip install -e .
```

2. Start database and run migrations:
```bash
docker-compose up -d postgres
alembic upgrade head
```

3. Create test organization and API key:
```bash
./scripts/setup_api_test.sh
```

4. Start API:
```bash
./scripts/start_web.sh
```

5. Open:
- Web UI: `http://localhost:8000/web/`
- API docs: `http://localhost:8000/api/docs`

## API Usage

Analyze a tender:
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-org-key" \
  -d '{
    "title": "AI Security Platform",
    "description": "Government agency needs AI threat detection",
    "organization_name": "National Cyber Agency"
  }'
```

List tenders:
```bash
curl -H "X-API-Key: test-org-key" http://localhost:8000/api/v1/tenders
```

## Data Ingestion

Fetch and store TED tenders:
```bash
PYTHONPATH=src:$PYTHONPATH python scripts/fetch_and_store.py
```

## Testing

Use your virtual environment:
```bash
source venv/bin/activate
pytest tests/ -v
```

Run smoke scripts:
```bash
./scripts/test_api.sh
./scripts/test_web_ui.sh
```

## Configuration

Primary environment variables:
- `DATABASE_URL` (default: `postgresql://procurement:procurement@localhost:5432/procurement`)
- `LLM_BASE_URL` (default: `http://localhost:1234/v1`)
- `LLM_MODEL` (default: `openai/gpt-oss-20b`)
- `CORS_ORIGINS` (comma-separated)
- `WEB_ORGANIZATION_SLUG` (default: `demo-org`)

## Notes

- API authentication uses `X-API-Key` per organization.
- Web UI resolves organization by `WEB_ORGANIZATION_SLUG` and falls back to the first available org.
- Status values are normalized to: `pending`, `processing`, `filtered_out`, `rated_low`, `complete`, `error`.
