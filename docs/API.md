# Procurement AI - REST API Documentation

## Overview

The Procurement AI REST API provides endpoints to submit tenders for AI analysis, retrieve analysis results, and manage procurement workflows.

**Base URL:** `http://localhost:8000`  
**API Version:** v1  
**Authentication:** API Key (X-API-Key header)

## Authentication

All API endpoints require authentication using an API key passed in the `X-API-Key` header.

For MVP testing, the API key is the organization slug (e.g., `test-org`).

```bash
# Example with authentication
curl -H "X-API-Key: test-org" http://localhost:8000/api/v1/tenders
```

## Endpoints

### Health Check

#### `GET /health`

Check API and database health status.

**Authentication:** Not required

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "database": "connected",
  "llm_service": "configured"
}
```

**Example:**

```bash
curl http://localhost:8000/health
```

---

### Submit Tender for Analysis

#### `POST /api/v1/analyze`

Submit a tender for AI analysis. The analysis runs in the background.

**Authentication:** Required  
**Response:** `202 Accepted` (processing started)

**Request Body:**

```json
{
  "title": "AI-Powered Cybersecurity Platform",
  "description": "Government agency requires AI-based threat detection system with real-time monitoring capabilities...",
  "organization_name": "National Cyber Agency",
  "deadline": "2026-06-30",
  "estimated_value": "€2,500,000",
  "external_id": "CYBER-2026-001",
  "source": "api"
}
```

**Fields:**

- `title` (required): Tender title (1-500 chars)
- `description` (required): Detailed tender description (10-10000 chars)
- `organization_name` (required): Organization posting the tender
- `deadline` (optional): Deadline in YYYY-MM-DD format
- `estimated_value` (optional): Estimated contract value
- `external_id` (optional): External reference ID
- `source` (optional): Source of tender (default: "api")

**Response:**

```json
{
  "tender": {
    "id": 1,
    "title": "AI-Powered Cybersecurity Platform",
    "description": "Government agency requires...",
    "organization_name": "National Cyber Agency",
    "deadline": "2026-06-30",
    "estimated_value": "€2,500,000",
    "external_id": "CYBER-2026-001",
    "source": "api",
    "status": "processing",
    "created_at": "2026-02-02T10:30:00Z",
    "updated_at": "2026-02-02T10:30:00Z"
  },
  "status": "processing",
  "processing_time": null,
  "filter_result": null,
  "rating_result": null,
  "bid_document": null
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-org" \
  -d '{
    "title": "AI Cybersecurity Platform",
    "description": "Government needs AI-based threat detection system with machine learning capabilities for real-time monitoring and automated response to cyber threats.",
    "organization_name": "National Cyber Agency",
    "deadline": "2026-06-30",
    "estimated_value": "€2,500,000"
  }'
```

---

### List Tenders

#### `GET /api/v1/tenders`

List all tenders for the authenticated organization with pagination.

**Authentication:** Required

**Query Parameters:**

- `page` (optional): Page number (default: 1, min: 1)
- `page_size` (optional): Items per page (default: 20, min: 1, max: 100)

**Response:** `200 OK`

```json
{
  "tenders": [
    {
      "id": 1,
      "title": "AI Cybersecurity Platform",
      "description": "Government needs...",
      "organization_name": "National Cyber Agency",
      "deadline": "2026-06-30",
      "estimated_value": "€2,500,000",
      "external_id": null,
      "source": "api",
      "status": "analyzed",
      "created_at": "2026-02-02T10:30:00Z",
      "updated_at": "2026-02-02T10:35:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

**Examples:**

```bash
# Get first page (default 20 items)
curl -H "X-API-Key: test-org" http://localhost:8000/api/v1/tenders

# Get second page with 10 items
curl -H "X-API-Key: test-org" http://localhost:8000/api/v1/tenders?page=2&page_size=10
```

---

### Get Tender Analysis

#### `GET /api/v1/tenders/{id}`

Get detailed information about a specific tender including analysis results.

**Authentication:** Required

**Path Parameters:**

- `id` (required): Tender ID (integer)

**Response:** `200 OK`

```json
{
  "tender": {
    "id": 1,
    "title": "AI Cybersecurity Platform",
    "description": "Government needs AI-based threat detection...",
    "organization_name": "National Cyber Agency",
    "deadline": "2026-06-30",
    "estimated_value": "€2,500,000",
    "external_id": null,
    "source": "api",
    "status": "analyzed",
    "created_at": "2026-02-02T10:30:00Z",
    "updated_at": "2026-02-02T10:35:00Z"
  },
  "status": "analyzed",
  "processing_time": 4.5,
  "filter_result": {
    "is_relevant": true,
    "confidence": 0.95,
    "categories": ["cybersecurity", "ai"],
    "reasoning": "Strong alignment with company expertise in AI and cybersecurity. Government sector matches target market."
  },
  "rating_result": {
    "overall_score": 8.5,
    "strategic_fit": 9.0,
    "win_probability": 8.0,
    "effort_required": 7.5,
    "strengths": [
      "Perfect fit with AI and cybersecurity capabilities",
      "Government sector experience",
      "Estimated value matches typical project size"
    ],
    "risks": [
      "Timeline may be tight (4 months)",
      "Government procurement can be slow",
      "Competition likely to be strong"
    ],
    "recommendation": "PURSUE - High strategic value, good win probability. Allocate senior team members."
  },
  "bid_document": {
    "executive_summary": "Our company is uniquely positioned to deliver...",
    "technical_approach": "We propose a three-phase approach...",
    "value_proposition": "Our solution provides...",
    "timeline_estimate": "Phase 1 (Months 1-2): Requirements and design..."
  }
}
```

**Example:**

```bash
# Get tender with ID 1
curl -H "X-API-Key: test-org" http://localhost:8000/api/v1/tenders/1
```

---

## Status Codes

- `200 OK` - Request successful
- `202 Accepted` - Request accepted, processing in background
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Missing or invalid API key
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

## Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Example:**

```json
{
  "detail": "Monthly analysis limit reached (100/100)"
}
```

---

## Interactive Documentation

The API provides auto-generated interactive documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

These interfaces allow you to:
- Browse all available endpoints
- See request/response schemas
- Test API calls directly from the browser
- Download OpenAPI specification

---

## Complete Testing Workflow

### 1. Check API Health

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"healthy","database":"connected","llm_service":"configured"}`

### 2. Submit a Tender

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-org" \
  -d '{
    "title": "Cloud Migration Services",
    "description": "Large enterprise requires cloud migration strategy and implementation for 500+ servers, including security assessment, data migration, and staff training. Must support hybrid cloud architecture with Azure and AWS.",
    "organization_name": "Tech Corp International",
    "deadline": "2026-08-15",
    "estimated_value": "$1,200,000"
  }'
```

Save the tender `id` from the response.

### 3. List All Tenders

```bash
curl -H "X-API-Key: test-org" http://localhost:8000/api/v1/tenders
```

### 4. Get Analysis Results

```bash
# Replace {id} with actual tender ID
curl -H "X-API-Key: test-org" http://localhost:8000/api/v1/tenders/{id}
```

**Note:** If status is still "processing", wait a few seconds and try again.

---

## Rate Limits

Each organization has a monthly analysis limit based on subscription tier:

- **FREE:** 100 analyses/month
- **BASIC:** 500 analyses/month
- **PRO:** 2,000 analyses/month
- **ENTERPRISE:** Unlimited

When limit is reached, POST /analyze returns `429 Too Many Requests`.

---

## Best Practices

1. **Check health before testing:** Ensure database and LLM service are available
2. **Use meaningful external_id:** For deduplication and tracking
3. **Poll for results:** Analysis runs in background, poll GET /tenders/{id} for completion
4. **Handle errors gracefully:** Check status codes and parse error messages
5. **Test with interactive docs:** Use /docs for quick experimentation
6. **Keep API key secure:** Don't commit keys to version control

---

## Environment Variables

Configure the API using these environment variables:

```bash
# Database
DATABASE_URL=postgresql://procurement:procurement@localhost:5432/procurement

# LLM Service
LLM_BASE_URL=http://localhost:1234/v1
LLM_MODEL=local-model
LLM_API_KEY=not-needed

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["http://localhost:3000"]
```

---

## Next Steps

- **Web Scraping:** Priority 4 will add automated tender collection from TED Europa
- **Authentication:** Production deployment will use JWT tokens instead of simple API keys
- **WebSockets:** Real-time notifications when analysis completes
- **Batch Processing:** Submit multiple tenders in one request
