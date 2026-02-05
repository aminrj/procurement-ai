#!/bin/bash
# Quick start script.

set -e

echo "================================"
echo "PROCUREMENT AI QUICK START"
echo "================================"

export PYTHONPATH="$(pwd)/src:${PYTHONPATH}"

echo "Step 1: Fetching tenders from TED Europa"
python scripts/fetch_and_store.py

echo ""
echo "Step 2: Viewing database contents"
python scripts/view_database.py

echo ""
echo "================================"
echo "Ready"
echo "================================"
echo ""
echo "Next steps:"
echo "  - Run AI analysis: python procurement_mvp.py"
echo "  - Start API server: uvicorn procurement_ai.api.main:app --reload"
