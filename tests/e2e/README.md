# E2E Tests

These tests validate the running system end-to-end against real services.

## Prerequisites

1. API server running at `http://localhost:8000`
2. PostgreSQL reachable by the API
3. LLM endpoint configured and reachable by the API
4. Test organization exists with API key `test-org-key` (or set `API_KEY` in tests)

## Run

```bash
pytest tests/e2e/ -v -s -m e2e
```

## Covered flows

- Submit a suitable tender and poll until processing finishes
- Submit an unsuitable tender and verify filter behavior
- Validate tender listing and pagination contract
- Validate API validation/not-found behavior
