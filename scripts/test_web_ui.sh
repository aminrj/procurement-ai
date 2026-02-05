#!/bin/bash
# Test Web UI Endpoints

BASE_URL="http://localhost:8000"
echo "🧪 Testing Procurement AI Web UI"
echo "================================"

# Test dashboard
echo -n "✓ Testing dashboard... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/web/")
if [ "$STATUS" -eq 200 ]; then
    echo "✅ OK"
else
    echo "❌ FAILED (Status: $STATUS)"
fi

# Test API docs
echo -n "✓ Testing API docs... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/docs")
if [ "$STATUS" -eq 200 ]; then
    echo "✅ OK"
else
    echo "❌ FAILED (Status: $STATUS)"
fi

# Test tender list with filter
echo -n "✓ Testing tender list (filtered)... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/web/tenders?status=pending")
if [ "$STATUS" -eq 200 ]; then
    echo "✅ OK"
else
    echo "❌ FAILED (Status: $STATUS)"
fi

# Test tender list with search
echo -n "✓ Testing tender list (search)... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/web/tenders?search=transport")
if [ "$STATUS" -eq 200 ]; then
    echo "✅ OK"
else
    echo "❌ FAILED (Status: $STATUS)"
fi

# Test tender detail
echo -n "✓ Testing tender detail... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/web/tender/1")
if [ "$STATUS" -eq 200 ]; then
    echo "✅ OK"
else
    echo "❌ FAILED (Status: $STATUS)"
fi

# Test scrape modal
echo -n "✓ Testing scrape modal... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/web/scrape-modal")
if [ "$STATUS" -eq 200 ]; then
    echo "✅ OK"
else
    echo "❌ FAILED (Status: $STATUS)"
fi

# Test health endpoint
echo -n "✓ Testing health endpoint... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health")
if [ "$STATUS" -eq 200 ]; then
    echo "✅ OK"
else
    echo "❌ FAILED (Status: $STATUS)"
fi

echo ""
echo "================================"
echo "🎉 All tests completed!"
