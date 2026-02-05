#!/bin/bash
# Start the Procurement AI web application.

set -e

echo "Starting Procurement AI web application"

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

export PYTHONPATH="src:${PYTHONPATH}"
export DATABASE_URL="${DATABASE_URL:-postgresql://procurement:procurement@localhost:5432/procurement}"

echo "Web UI: http://localhost:8000/web/"
echo "API Docs: http://localhost:8000/api/docs"
echo "Press Ctrl+C to stop"

uvicorn procurement_ai.api.main:app --reload --port 8000
