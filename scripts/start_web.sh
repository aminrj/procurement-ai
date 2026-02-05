#!/bin/bash
# Start the Procurement AI web application

echo "🚀 Starting Procurement AI SaaS Application..."
echo ""

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export PYTHONPATH=src:$PYTHONPATH
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/procurement_ai"

# Start the server
echo "📡 Server will be available at:"
echo "   → Web UI:  http://localhost:8000"
echo "   → API Docs: http://localhost:8000/api/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uvicorn src.procurement_ai.api.main:app --reload --port 8000
