# Scripts

Operational scripts for local development and validation.

## Core Setup

1. Initialize database schema:
```bash
./scripts/init_db.sh
```

2. Create test organization/API key:
```bash
./scripts/setup_api_test.sh
```

3. Start API and web UI:
```bash
./scripts/start_web.sh
```

## Data Utilities

Fetch and store recent TED tenders:
```bash
PYTHONPATH=src:$PYTHONPATH python scripts/fetch_and_store.py
```

View stored tenders:
```bash
PYTHONPATH=src:$PYTHONPATH python scripts/view_database.py
```

## Smoke Tests

API smoke test:
```bash
./scripts/test_api.sh
```

Web UI endpoint smoke test:
```bash
./scripts/test_web_ui.sh
```

## Environment

- `DATABASE_URL` default:
  - `postgresql://procurement:procurement@localhost:5432/procurement`
- `API_KEY` default for `test_api.sh`:
  - `test-org-key`
- `PYTHONPATH` should include `src` when running Python scripts directly.
