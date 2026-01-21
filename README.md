# Procurement Intelligence MVP – Learning LLM Engineering by Building

This repository documents my journey learning **LLM engineering** by building real, working applications instead of isolated prompt experiments.

The first milestone is a **one-file, end-to-end LLM-powered application** that:

- filters public procurement tenders,
- rates their business attractiveness,
- generates structured bid document content,

all while enforcing **reliable structured outputs** using **Pydantic**.

This repo is intentionally designed as a **learning artifact**:
each important step is captured as a **stable version** that matches an article or explanation.

---

## What this version demonstrates (v0.1)

This version corresponds to the article:

> **“I Built a One-File Procurement ‘AI Analyst’ to Learn LLM Engineering (and It Actually Works)”**

Key concepts illustrated:

- LLMs as **software components**, not chatbots
- Structured JSON outputs enforced with **Pydantic**
- Prompt patterns for classification, scoring, and generation
- Multi-agent pipeline:
  - Filter agent (relevance)
  - Rating agent (business evaluation)
  - Document generator (proposal drafting)
- Explicit orchestration and branching logic
- Retry and validation strategy for unreliable LLM outputs
- Local inference using **LM Studio** (OpenAI-compatible API)

Everything is contained in **one Python file** on purpose, to make the learning flow easy to follow.

---

## High-level architecture

The application follows a simple, explicit pipeline:

1. **Input**: a procurement tender
2. **Filter Agent**  
   → Is this tender relevant to cybersecurity, AI, or software?
3. **Rating Agent**  
   → Is it worth pursuing? What are the risks and chances?
4. **Document Generator**  
   → Generate structured bid content _only if_ the opportunity is strong
5. **Output**: a validated, structured result object

The LLM is wrapped behind a single service that:

- enforces JSON output,
- cleans malformed responses,
- validates everything with Pydantic,
- retries on failure.

---

## Versioning strategy (important)

This repository uses a **learning-friendly versioning strategy**:

- `main` always contains the **latest stable, runnable code**
- **Git tags** are used to capture **immutable snapshots** that correspond to articles or learning milestones

### Why tags?

- Tags never move → readers always see the _exact_ code used in an article
- `main` can continue evolving without breaking older explanations
- No long-lived maintenance branches needed

For this article, you should check out the tag:

```bash
git checkout v0.1-article-procurement-mvp
```
