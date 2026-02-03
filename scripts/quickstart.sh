#!/bin/bash
# Quick start script - fetch tenders and you're ready to go!

set -e

echo "================================"
echo "PROCUREMENT AI - QUICK START"
echo "================================"
echo ""

# Add src to PYTHONPATH
export PYTHONPATH="/Users/ARAJI/git/ai_projects/procurement-ai/src:$PYTHONPATH"

echo "Step 1: Fetching tenders from TED Europa..."
python scripts/fetch_and_store.py

echo ""
echo "Step 2: Viewing database contents..."
python scripts/view_database.py

echo ""
echo "================================"
echo "✅ READY!"
echo "================================"
echo ""
echo "You now have 50 real tenders in your database."
echo ""
echo "Next steps:"
echo "  • Run AI analysis: python procurement_mvp.py"
echo "  • Start API server: python -m uvicorn src.procurement_ai.api.main:app"
echo "  • Or use the Python API directly"
echo ""
