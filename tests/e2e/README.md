# End-to-End Tests

E2E tests that validate the complete workflow using a real local LLM.

## Quick Start

```bash
# 1. Start services
docker-compose up -d db
./scripts/setup_api_test.sh

# 2. Start LM Studio on http://localhost:1234

# 3. Start API (separate terminal)
uvicorn procurement_ai.api.main:app --reload

# 4. Run E2E tests
pytest tests/e2e/ -v -s
```

## Prerequisites

### Local LLM

**LM Studio (Recommended):**

- Download from [lmstudio.ai](https://lmstudio.ai/)
- Download model: `mistral-7b-instruct` or similar
- Start server on `http://localhost:1234`

**Ollama (Alternative):**

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull mistral
ollama serve  # runs on http://localhost:11434
```

### Configure LLM

Edit `.env`:
```bash
# For LM Studio
LLM_BASE_URL=http://localhost:1234/v1
LLM_MODEL=local-model

# For Ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=mistral
```

## What Gets Tested

### ✅ test_full_workflow_with_suitable_tender
- Submits realistic IT tender
- Waits for async processing
- Validates filter, rating, bid document generation
- **Time**: ~30-60s

### ✅ test_unsuitable_tender_filtering
- Submits non-IT tender (construction)
- Validates filter correctly rejects it
- **Time**: ~20-40s

### ✅ test_pagination_and_listing
- Tests GET /tenders endpoint
- Validates pagination
- **Time**: <1s

### ✅ test_api_error_handling
- Tests 422 validation errors
- Tests 404 not found
- **Time**: <1s

## Configuration

Adjust timing in `test_end_to_end.py`:
```python
MAX_WAIT_TIME = 60   # Max seconds for processing
POLL_INTERVAL = 2    # Seconds between checks
```

For slower models:
```python
MAX_WAIT_TIME = 120  # Give more time
POLL_INTERVAL = 3    # Check less frequently
```

## Troubleshooting

### API Not Available
```
Error: API not available
```
**Fix**: `uvicorn procurement_ai.api.main:app --reload`

### LLM Not Configured
```
AssertionError: LLM not configured
```
**Fix**: Check `.env` has correct LLM settings and LM Studio is running

### Processing Timeout
```
TimeoutError: Tender processing timeout
```
**Causes**:
- LLM not responding (check LM Studio)
- LLM too slow (increase `MAX_WAIT_TIME`)
- Background task error (check API logs)

### Database Not Healthy
```
AssertionError: Database not healthy
```
**Fix**:
```bash
docker-compose up -d db
./scripts/setup_api_test.sh
```

## Expected Results

```
tests/e2e/test_end_to_end.py::test_full_workflow_with_suitable_tender PASSED
tests/e2e/test_end_to_end.py::test_unsuitable_tender_filtering PASSED
tests/e2e/test_end_to_end.py::test_pagination_and_listing PASSED
tests/e2e/test_end_to_end.py::test_api_error_handling PASSED

======================== 4 passed in ~90s ========================
```

**Note**: These tests require running services and take ~90 seconds. They are designed to run before major releases or when validating LLM integration changes.
