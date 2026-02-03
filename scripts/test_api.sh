#!/bin/bash
# Test script for Procurement AI API

set -e

API_URL="http://localhost:8000"
API_KEY="test-org"

echo "🧪 Testing Procurement AI REST API"
echo "=================================="
echo ""

# Wait for API to be ready
echo "⏳ Waiting for API to start..."
for i in {1..10}; do
    if curl -s "$API_URL/health" > /dev/null 2>&1; then
        echo "✅ API is ready"
        break
    fi
    sleep 1
    if [ $i -eq 10 ]; then
        echo "❌ API did not start in time"
        exit 1
    fi
done
echo ""

# Test 1: Health Check
echo "1️⃣  Testing Health Check"
echo "GET /health"
HEALTH=$(curl -s "$API_URL/health")
echo "$HEALTH" | python3 -m json.tool
echo ""

# Test 2: Submit a tender
echo "2️⃣  Testing Tender Submission"
echo "POST /api/v1/analyze"
TENDER_JSON='{
  "title": "AI Cybersecurity Platform Development",
  "description": "Government agency seeks experienced vendor to develop an AI-powered cybersecurity platform for real-time threat detection and automated response. Must include machine learning capabilities, integration with existing security infrastructure, and comprehensive training for 50+ staff members. Budget includes hardware, software licenses, and 2-year support contract.",
  "organization_name": "National Cyber Defense Agency",
  "deadline": "2026-08-15",
  "estimated_value": "$2,500,000"
}'

RESPONSE=$(curl -s -X POST "$API_URL/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d "$TENDER_JSON")

echo "$RESPONSE" | python3 -m json.tool
TENDER_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['tender']['id'])")
echo ""
echo "📝 Tender ID: $TENDER_ID"
echo ""

# Test 3: List tenders
echo "3️⃣  Testing List Tenders"
echo "GET /api/v1/tenders"
TENDERS=$(curl -s -H "X-API-Key: $API_KEY" "$API_URL/api/v1/tenders")
echo "$TENDERS" | python3 -m json.tool
echo ""

# Test 4: Get specific tender (wait a bit for processing)
echo "4️⃣  Testing Get Specific Tender"
echo "GET /api/v1/tenders/$TENDER_ID"
echo "⏳ Waiting 3 seconds for background processing..."
sleep 3

TENDER_DETAIL=$(curl -s -H "X-API-Key: $API_KEY" "$API_URL/api/v1/tenders/$TENDER_ID")
echo "$TENDER_DETAIL" | python3 -m json.tool
echo ""

# Test 5: Check OpenAPI docs
echo "5️⃣  Testing OpenAPI Documentation"
echo "GET /docs (Swagger UI)"
DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/docs")
if [ "$DOCS_STATUS" == "200" ]; then
    echo "✅ Swagger UI available at $API_URL/docs"
else
    echo "❌ Swagger UI not available (status: $DOCS_STATUS)"
fi

echo "GET /redoc (ReDoc)"
REDOC_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/redoc")
if [ "$REDOC_STATUS" == "200" ]; then
    echo "✅ ReDoc available at $API_URL/redoc"
else
    echo "❌ ReDoc not available (status: $REDOC_STATUS)"
fi
echo ""

echo "=================================="
echo "✅ All tests completed!"
echo ""
echo "Next steps:"
echo "  • Open http://localhost:8000/docs in your browser for interactive API docs"
echo "  • Open http://localhost:8000/redoc for alternative documentation view"
echo "  • Check tender status with: curl -H 'X-API-Key: test-org' $API_URL/api/v1/tenders/$TENDER_ID"
