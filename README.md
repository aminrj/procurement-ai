# Procurement Intelligence AI

> Automated tender analysis and bid generation using AI

**Status**: ✅ MVP Ready | 🚀 TED Scraper Working | 🤖 AI Agents Tested

---

## What This Does

Analyzes EU procurement tenders and generates professional bid proposals using AI.

### Key Features

- **Web Scraping**: Automatic tender collection from TED Europa (EU procurement portal)
- Filters procurement tenders for relevance (cybersecurity, AI, software)
- Rates business attractiveness with multi-dimensional scoring
- Generates structured bid document content
- Enforces reliable structured outputs using Pydantic
- Works with local LLMs (LM Studio) and cloud APIs (Groq)

**Tech Stack:**

- **LLM Runtime:** LM Studio (local development) / Groq (production)
- **Models:** Llama 3.1 8B and similar
- **Framework:** Pure Python with Pydantic for validation
- **Data Sources:** TED Europa API (EU public procurement)
- **Storage:** PostgreSQL with multi-tenant support
- **Architecture:** Multi-agent pipeline with explicit orchestration

---

## Architecture

Simple, explicit pipeline:

```
TED API → Scraper → Database
           ↓
       Filter Agent → Rating Agent → Document Generator
           ↓
       Bid Proposals
```

### Components

```
src/procurement_ai/
├── agents/          # AI agents (filter, rating, generator)
├── services/        # LLM service wrapper
├── scrapers/        # TED Europa scraper
├── storage/         # Database layer
├── models.py        # Data models
└── config.py        # Settings
```

- Multi-tenant PostgreSQL storage
- Repository pattern for clean data access
- Alembic migrations for schema evolution
- Docker Compose for local development
- Ready for containerized deployment

See [docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md) for complete setup guide.

---

## Quick Start

**Prerequisites:**

- Python 3.9+
- Docker and Docker Compose
- LM Studio running locally (or Groq API key)

**Setup (5 minutes):**

```bash
# Clone and install
git clone https://github.com/yourusername/procurement-ai.git
cd procurement-ai
pip install -r requirements.txt
pip install -e .

# Start database
docker-compose up -d postgres

# Run migrations and seed data
alembic upgrade head
python examples/seed_database.py

# Test it works
python examples/database_usage.py
```

**Expected output:**

```
✓ Filtered tender: Relevant
✓ Rating: 8.5/10 (High confidence)
✓ Generated bid document with 3 sections
```

**Next Steps:**

- [Follow the learning path](docs/LEARNING_PATH.md) to understand how it works
- [Run batch processing example](examples/batch_processing.py) for multiple tenders
- [Explore experiments](experiments/) to see prompt engineering iterations

---

## Learning Path

This project is designed as a learning artifact following the fast.ai philosophy: learn by building real things.

**Progressive Learning:**

| Resource                                                   | Type          | Focus                              |
| ---------------------------------------------------------- | ------------- | ---------------------------------- |
| [Hello LLM](learn/01_hello_llm.ipynb)                      | Notebook      | First API call, structured outputs |
| [Learning Path Guide](docs/LEARNING_PATH.md)               | Documentation | Complete curriculum outline        |
| [Prompt Variations](experiments/01_prompt_varations.py)    | Experiment    | Prompt engineering iterations      |
| [Temperature Impact](experiments/02_temperature_impact.py) | Experiment    | Parameter optimization             |

**Key Learnings:**

- How to structure LLM outputs with Pydantic
- Prompt engineering for classification and generation tasks
- Multi-agent orchestration patterns
- Retry strategies for production reliability
- Local vs cloud LLM tradeoffs

---

## Examples

### Quickstart Demo

```python
from procurement_ai import ProcurementOrchestrator
from procurement_ai.models import Tender

orchestrator = ProcurementOrchestrator()
tender = Tender(
    id="DEMO-001",
    title="AI-Powered Threat Detection System",
    description="Government agency seeks vendor for cybersecurity platform...",
    organization="National Cybersecurity Agency",
    value=2500000.0,
    deadline="2024-12-31"
)

result = await orchestrator.process_tender(tender)
print(f"Relevant: {result.is_relevant}")
print(f"Rating: {result.rating}/10")
```

### Web Scraping

Fetch real tenders from TED Europa (EU procurement portal):

```python
from procurement_ai.scrapers import TEDScraper

# Search for IT tenders from last 7 days
with TEDScraper() as scraper:
    tenders = scraper.search_tenders(
        days_back=7,
        cpv_codes=TEDScraper.IT_CPV_CODES,
        limit=20
    )
    
    for tender in tenders:
        print(f"{tender['title']} - €{tender['estimated_value']:,.0f}")
```

Or run the example script:

```bash
python examples/scrape_tenders.py
```

See [docs/SCRAPER_IMPLEMENTATION.md](docs/SCRAPER_IMPLEMENTATION.md) for complete guide.

**More Examples:**

- [quickstart.py](examples/quickstart.py) - 5-minute demo
- [scrape_tenders.py](examples/scrape_tenders.py) - Fetch real tenders from TED Europa
- [batch_processing.py](examples/batch_processing.py) - Process multiple tenders
- [sample_data.py](examples/sample_data.py) - Test data generator

---

## Installation

**As a library:**

```bash
pip install git+https://github.com/yourusername/procurement-ai.git
```

**For development:**

```bash
git clone https://github.com/yourusername/procurement-ai.git
cd procurement-ai
pip install -e ".[dev]"
```

**Requirements:**

- Python 3.9+
- httpx >= 0.25 (for API requests)
- pydantic >= 2.0 (for structured outputs)
- tenacity >= 8.2 (for retry logic)
- PostgreSQL >= 13 (for data storage)

---

## Project Structure

```
procurement-ai/
├── src/procurement_ai/       # Main package
│   ├── agents/              # Filter, rating, generator agents
│   ├── services/            # LLM service abstraction
│   ├── scrapers/            # Web scraping (TED Europa)
│   ├── orchestration/       # Workflow coordination
│   ├── storage/             # Database repositories
│   ├── models.py            # Pydantic data models
│   └── config.py            # Configuration
├── examples/                # Runnable examples
│   └── scrape_tenders.py    # Fetch tenders from TED Europa
├── experiments/             # Research and optimization
├── learn/                   # Learning notebooks
├── tests/                   # Test suite (78 tests passing)
├── docs/                    # Documentation
│   └── SCRAPER_IMPLEMENTATION.md  # Web scraping guide
└── benchmarks/              # Performance data
```

---

## Configuration

Configure via environment variables or `config.py`:

```python
from procurement_ai import Config

config = Config(
    llm_base_url="http://localhost:1234/v1",
    llm_model="llama-3.1-8b-instruct",
    max_retries=3,
    timeout=30.0
)
```

**Environment variables:**

- `LLM_BASE_URL` - LLM API endpoint (default: <http://localhost:1234/v1>)
- `LLM_MODEL` - Model name (default: llama-3.1-8b-instruct)
- `LLM_API_KEY` - API key for cloud providers

---

## Testing

### Quick Test Suite (Fast)

```bash
# Run unit + integration tests (excludes E2E)
pytest

# With coverage
pytest --cov=procurement_ai --cov-report=html

# Fast tests only
pytest -m "not slow"
```

**Current**: 60 tests pass in 0.70s ✓

### End-to-End Tests (Requires LLM)

Full workflow validation with real LLM:

```bash
# Prerequisites:
# 1. Start: docker-compose up -d db && ./scripts/setup_api_test.sh
# 2. Start: LM Studio on http://localhost:1234
# 3. Start: uvicorn procurement_ai.api.main:app --reload

# Run E2E tests (~90s)
pytest tests/e2e/ -v -s -m e2e
```

**Validates**: Complete tender submission → LLM processing → results retrieval

See [tests/e2e/README.md](tests/e2e/README.md) for setup details.

---

## Roadmap

**Current (v0.1):**

- Multi-agent pipeline
- LM Studio support
- Structured outputs with Pydantic
- Basic orchestration

**Planned (v0.2+):**

- Cloud LLM support (Groq, OpenAI)
- Web scraping for real tender data
- Streamlit UI
- Benchmarking suite
- Multi-language support

---

## Contributing

This is a learning project, but contributions are welcome:

- Bug reports and fixes
- Documentation improvements
- New examples or experiments
- Performance optimizations

---

## License

MIT License - See LICENSE file for details

---

## About

Built as a learning project to transition from traditional ML to LLM engineering. Focus is on clean architecture, structured outputs, and practical production patterns rather than research novelty.
