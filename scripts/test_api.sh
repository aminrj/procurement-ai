#!/bin/bash
# Test script for Procurement AI API.

set -e

API_URL="http://localhost:8000"
API_KEY="${API_KEY:-test-org-key}"

echo "Testing Procurement AI REST API"
echo "================================"
echo ""

echo "Waiting for API to start..."
for i in {1..15}; do
    if curl -s "$API_URL/health" > /dev/null 2>&1; then
        echo "API is ready"
        break
    fi
    sleep 1
    if [ $i -eq 15 ]; then
        echo "API did not start in time"
        exit 1
    fi
done
echo ""

echo "1. Health Check"
echo "GET /health"
HEALTH=$(curl -s "$API_URL/health")
echo "$HEALTH" | python3 -m json.tool
echo ""

echo "2. Submit Tender"
echo "POST /api/v1/analyze"
TENDER_JSON='{
  "title": "AI Cybersecurity Platform Development",
  "description": "Government agency seeks experienced vendor to develop an AI-powered cybersecurity platform for real-time threat detection and automated response. Must include machine learning capabilities, integration with existing security infrastructure, and comprehensive training for staff.",
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
echo "Tender ID: $TENDER_ID"
echo ""

echo "3. List Tenders"
echo "GET /api/v1/tenders"
TENDERS=$(curl -s -H "X-API-Key: $API_KEY" "$API_URL/api/v1/tenders")
echo "$TENDERS" | python3 -m json.tool
echo ""

echo "4. Get Specific Tender"
echo "GET /api/v1/tenders/$TENDER_ID"
echo "Waiting 3 seconds for background processing..."
sleep 3

TENDER_DETAIL=$(curl -s -H "X-API-Key: $API_KEY" "$API_URL/api/v1/tenders/$TENDER_ID")
echo "$TENDER_DETAIL" | python3 -m json.tool
echo ""

echo "5. OpenAPI Documentation"
DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/docs")
if [ "$DOCS_STATUS" == "200" ]; then
    echo "Swagger UI available at $API_URL/api/docs"
else
    echo "Swagger UI not available (status: $DOCS_STATUS)"
fi

REDOC_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/redoc")
if [ "$REDOC_STATUS" == "200" ]; then
    echo "ReDoc available at $API_URL/api/redoc"
else
    echo "ReDoc not available (status: $REDOC_STATUS)"
fi

echo ""
echo "================================"
echo "API test script completed"
echo ""
echo "Next steps:"
echo "  - Open http://localhost:8000/api/docs in your browser"
echo "  - Check tender status: curl -H 'X-API-Key: $API_KEY' $API_URL/api/v1/tenders/$TENDER_ID"
