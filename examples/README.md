# Getting Started with Real Data

## Quick Start (3 steps)

### 1. Check Your Data
```bash
python check_db.py
```
See what tenders are already in your database. You likely have test data to work with!

### 2. Analyze with AI (The Real Value!)
```bash
python examples/quickstart.py
```
Runs your AI agents (filter → rate → generate) on the tenders in your database.

**Prerequisites:**
- LLM running (LM Studio or Groq)
- Database with tenders

### 3. Try Web Scraping (Optional)
```bash
python examples/scrape_tenders.py
```

**Note:** TED Europa API endpoint may need updates or authentication. The scraper infrastructure is ready, but for MVP purposes, you can focus on AI analysis with test data.

---

## What Each Script Does

| Script | Purpose | Needs DB? | Needs LLM? | Status |
|--------|---------|-----------|------------|--------|
| `check_db.py` | View database tenders | Yes | No | ✅ Works |
| `quickstart.py` | AI analysis demo | Yes | Yes | ✅ Works |
| `sample_data.py` | Generate test data | No | No | ✅ Works |
| `scrape_tenders.py` | View TED tenders | No | No | ⚠️ API issues |
| `scrape_and_save.py` | Fetch and save | Yes | No | ⚠️ API issues |

---

## Tips

**No tenders found?**
- TED API might have no IT tenders in last 7 days
- Try increasing `days_back` parameter
- Or check TED Europa website directly

**Getting started without real data?**
- Use `sample_data.py` to generate test tenders
- Or use `seed_database.py` to populate sample data

**Focus on AI value:**
1. Get initial data (step 1-2 above)
2. Focus on improving your agents' accuracy
3. Experiment with prompts and parameters
4. Refine scoring and filtering logic

The scraper just provides data - the real value is in the AI analysis!
