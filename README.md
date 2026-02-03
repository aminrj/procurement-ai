# Procurement Intelligence AI

> Automated tender monitoring and bid generation using local LLMs

[Quick Start](#quick-start) | [Learning Path](#learning-path) | [Architecture](#architecture) | [Examples](#examples)

---

## What This Does

Automatically monitors procurement sites, filters opportunities, rates them, and generates professional bid documents using local LLMs.

**Key Features:**

- Filters procurement tenders for relevance (cybersecurity, AI, software)
- Rates business attractiveness with multi-dimensional scoring
- Generates structured bid document content
- Enforces reliable structured outputs using Pydantic
- Works with local LLMs (LM Studio) and cloud APIs (Groq)

**Tech Stack:**

- **LLM Runtime:** LM Studio (local development) / Groq (production)
- **Models:** Llama 3.1 8B and similar
- **Framework:** Pure Python with Pydantic for validation
- **Architecture:** Multi-agent pipeline with explicit orchestration

---

## Architecture

The application follows a clean, explicit pipeline:

1. **Filter Agent** - Classifies tender relevance
2. **Rating Agent** - Evaluates business opportunity
3. **Document Generator** - Creates structured bid content
4. **Orchestrator** - Manages workflow and error handling

**Design Principles:**

- LLMs as software components, not chatbots
- Structured JSON outputs validated with Pydantic
- Retry logic for unreliable LLM responses
- Clean separation between agents, models, and services

```
src/procurement_ai/
├── agents/          # Filter, rating, and generator agents
├── services/        # LLM service abstraction
├── orchestration/   # Workflow coordination
├── storage/         # Database layer (PostgreSQL + SQLAlchemy)
├── models.py        # Pydantic data models
└── config.py        # Configuration management
```

**Production Database Layer**

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

See [examples/](examples/) directory for more:

- [quickstart.py](examples/quickstart.py) - 5-minute demo
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
- httpx >= 0.25
- pydantic >= 2.0

---

## Project Structure

```
procurement-ai/
├── src/procurement_ai/       # Main package
│   ├── agents/              # Filter, rating, generator agents
│   ├── services/            # LLM service abstraction
│   ├── orchestration/       # Workflow coordination
│   ├── models.py            # Pydantic data models
│   └── config.py            # Configuration
├── examples/                # Runnable examples
├── experiments/             # Research and optimization
├── learn/                   # Learning notebooks
├── tests/                   # Test suite
├── docs/                    # Documentation
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
