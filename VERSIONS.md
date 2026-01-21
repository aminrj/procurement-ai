# Versions – Learning Milestones

This file is the **navigation map** for this repository.

Each version corresponds to a **stable snapshot** of the code that matches:

- a Medium article,
- a tutorial,
- or a specific learning milestone.

Versions are implemented as **Git tags**, not branches.
Tags are immutable and guarantee reproducibility for readers.

---

## Versioning strategy (simple and intentional)

n application

- Local LLM inference via LM Studio (OpenAI-compatible API)
- Three-agent pipeline:

  - Filter agent (relevance classification)
  - Rating agent (business evaluation)
  - Document generator (bid drafting)

- Structured JSON outputs enforced with Pydantic
- Explicit retry and validation logic
- Simple, linear orchestration with early exits
- Sample tenders for demonstration

### What this version intentionally does NOT include

- Web UI
- Database or persistence
- Scraping or PDF ingestion
- Evaluation metrics
- Advanced agent routing

This version is meant to be:

> **The smallest complete LLM application that behaves like real software**

---

## Planned future milestones (indicative)

These versions do not exist yet, but outline the learning path:

### v0.2 – Structured output hardening

- Improved JSON repair strategies
- Better logging and diagnostics
- Output stability analysis

### v0.3 – Real tender ingestion

- Scraping public procurement portals
- PDF and HTML parsing
- Normalization into domain models

### v0.4 – Evaluation & testing

- Labeled tender dataset
- Filtering accuracy metrics
- Scoring stability checks

### v0.5 – Modular architecture

- Split into packages (agents, services, models)
- Same logic, cleaner structure
- Comparison with graph-based orchestration

Each milestone will be:

- merged into `main`,
- tagged,
- documented,
- and referenced from an article or tutorial.

---

## How to use this file

If you’re:

- **new to the repo** → start with the latest article and its tag
- **following a tutorial** → check out the exact version listed
- **exploring freely** → use `main`, but expect more complexity

This file is the authoritative index for the learning journey.
