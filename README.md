# Procurement AI

**LLM-powered tender analysis with multi-agent orchestration**

🎯 **Focus**: Improve LLM prompts → Test with real data → Visualize results

---

## Quick Start

```bash
# Test LLM analysis
python procurement_mvp.py

# (Optional) Start web UI for visualization
./scripts/start_web.sh
open http://localhost:8000
```

---

## What This Is

LLM experimentation platform for procurement analysis:
- **3 AI agents** - Filter, Rating, Generator (the core value)
- **Web UI** - Visualize LLM outputs, test prompts
- **Database** - Persist results, compare iterations

**Not a SaaS app** - it's an AI research tool with supporting infrastructure.

---

## Core: LLM Agents

**1. Filter Agent** ([filter.py](src/procurement_ai/agents/filter.py))
- Binary classification: relevant or not?
- Temperature: 0.1 (precise)
- Output: relevance + confidence + categories + reasoning

**2. Rating Agent** ([rating.py](src/procurement_ai/agents/rating.py))
- Multi-dimensional scoring (6 dimensions)
- Temperature: 0.3 (balanced)
- Output: strategic fit, win probability, complexity, risk, urgency, effort

**3. Generator Agent** ([generator.py](src/procurement_ai/agents/generator.py))
- Professional bid document creation
- Temperature: 0.5 (creative)
- Output: structured proposal with intro, solution, differentiators

**Orchestrator** ([simple_chain.py](src/procurement_ai/orchestration/simple_chain.py))
- Sequential pipeline with early stopping
- Low-rated tenders skip document generation

---

## Project Structure

**Core (LLM work):**
```
src/procurement_ai/
├── agents/          # 🎯 Edit prompts here
│   ├── filter.py
│   ├── rating.py
│   └── generator.py
├── orchestration/   # Pipeline logic
└── services/llm.py  # LLM abstraction
```

**Supporting:**
```
├── api/       # Web UI (HTMX + Tailwind)
├── storage/   # Database (PostgreSQL)
└── scrapers/  # Data collection
```

---

## Installation

```bash
# 1. Install
pip install -r requirements.txt
pip install -e .

# 2. Configure LLM
# Option A: LM Studio (local)
# - Start LM Studio on port 1234

# Option B: Groq (cloud)
export GROQ_API_KEY="your-key"
export USE_GROQ=true

# 3. Test immediately
python procurement_mvp.py
```

**Optional:** Database + Web UI

```bash
# Start PostgreSQL
docker-compose up -d postgres
alembic upgrade head

# Fetch sample data
python scripts/fetch_and_store.py

# Start web UI
./scripts/start_web.sh
```

---

## Usage

**Direct Python (fastest iteration):**
```python
from procurement_ai.orchestration.simple_chain import ProcurementOrchestrator
from procurement_ai.models import Tender

orchestrator = ProcurementOrchestrator()
tender = Tender(
    id="test",
    title="AI Cybersecurity Platform",
    description="Advanced threat detection...",
    organization="Government Agency"
)

result = await orchestrator.process_tender(tender)
print(f"Relevant: {result.filter_result.is_relevant}")
print(f"Score: {result.rating_result.overall_score}/10")
```

**Web UI (best for visualization):**
- View all tenders: http://localhost:8000
- Click "Analyze with AI" to test agents
- Compare results across iterations

**REST API:**
```bash
curl -X POST http://localhost:8000/api/v1/tenders/analyze \\
  -H "Content-Type: application/json" \\
  -d '{"title": "AI Security", "description": "..."}'
```

---

## Improving the LLM

**Workflow:**
1. Edit prompts in `src/procurement_ai/agents/*.py`
2. Test: `python procurement_mvp.py` or web UI
3. Compare results
4. Iterate

**What to improve:**
- Filter: Better category detection, few-shot examples
- Rating: Scoring calibration, weighting adjustments
- Generator: More persuasive language, better structure

**Experiments:**
- `experiments/01_prompt_variations.py` - Test different prompts
- `experiments/02_temperature_impact.py` - Find optimal temperature

---

## Tech Stack

**Core:**
- Python 3.9+ with async/await
- LM Studio (local) or Groq (cloud)
- Pydantic for structured outputs

**Supporting:**
- FastAPI + HTMX (web UI)
- PostgreSQL + SQLAlchemy (data)
- TED Europa scraper (source)

---

## Tests

```bash
# Run core agent tests
pytest tests/unit/test_agents.py -v

# Run all tests
pytest tests/ -v

# Skip slow integration tests
pytest tests/unit/ -v
```

**Test Coverage:**
- ✅ All 3 agents (filter, rating, generator)
- ✅ Orchestration pipeline
- ✅ LLM service abstraction
- ✅ Database repositories
- ❌ TED scraper (14 tests failing - not core to LLM work)

---

## Documentation

- [Web UI Guide](docs/WEB_UI_GUIDE.md) - Using the visualization interface
- [Code Review](CODE_REVIEW_IMPROVEMENTS.md) - Recent improvements
- [API Docs](http://localhost:8000/api/docs) - Interactive API reference

---

## License

MIT
