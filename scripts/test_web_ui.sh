#!/bin/bash
# Test Web UI endpoints.

BASE_URL="http://localhost:8000"

echo "Testing Procurement AI Web UI"
echo "============================="

check_endpoint() {
    local label="$1"
    local url="$2"
    echo -n "Testing ${label}... "
    status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    if [ "$status" -eq 200 ]; then
        echo "OK"
    else
        echo "FAILED (status: $status)"
    fi
}

check_endpoint "dashboard" "$BASE_URL/web/"
check_endpoint "API docs" "$BASE_URL/api/docs"
check_endpoint "filtered tender list" "$BASE_URL/web/tenders?status=pending"
check_endpoint "search tender list" "$BASE_URL/web/tenders?search=transport"
check_endpoint "tender detail" "$BASE_URL/web/tender/1"
check_endpoint "scrape modal" "$BASE_URL/web/scrape-modal"
check_endpoint "health endpoint" "$BASE_URL/health"

echo ""
echo "============================="
echo "Web UI test script completed"
