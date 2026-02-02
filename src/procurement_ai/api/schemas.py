"""
API Request and Response Schemas
Separates API contracts from internal models
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from procurement_ai.models import TenderCategory
from procurement_ai.storage.models import TenderStatus


# ============================================================================
# Request Schemas
# ============================================================================


class AnalyzeRequest(BaseModel):
    """Request body for tender analysis"""

    title: str = Field(..., min_length=1, max_length=500, description="Tender title")
    description: str = Field(
        ..., min_length=10, max_length=10000, description="Tender description"
    )
    organization_name: str = Field(
        ..., min_length=1, max_length=200, description="Organization posting the tender"
    )
    deadline: Optional[str] = Field(None, description="Deadline in YYYY-MM-DD format")
    estimated_value: Optional[str] = Field(
        None, description="Estimated contract value"
    )
    external_id: Optional[str] = Field(None, description="External reference ID from source")
    source: str = Field(default="api", description="Source of the tender")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "AI-Powered Cybersecurity Platform",
                "description": "Government agency requires AI-based threat detection system...",
                "organization_name": "National Cyber Agency",
                "deadline": "2026-06-30",
                "estimated_value": "€2,500,000",
                "external_id": "CYBER-2026-001",
                "source": "api",
            }
        }
    )


# ============================================================================
# Response Schemas
# ============================================================================


class FilterResultResponse(BaseModel):
    """Filter agent result"""

    is_relevant: bool
    confidence: float
    categories: List[TenderCategory]
    reasoning: str


class RatingResultResponse(BaseModel):
    """Rating agent result"""

    overall_score: float
    strategic_fit: float
    win_probability: float
    effort_required: float
    strengths: List[str]
    risks: List[str]
    recommendation: str


class BidDocumentResponse(BaseModel):
    """Generated bid document"""

    executive_summary: str
    technical_approach: str
    value_proposition: str
    timeline_estimate: str


class TenderResponse(BaseModel):
    """Tender with basic info"""

    id: int  # Database uses integer IDs
    title: str
    description: str
    organization_name: str
    deadline: Optional[str]
    estimated_value: Optional[str]
    external_id: Optional[str]
    source: Optional[str] = None  # Can be None for manual entries
    status: TenderStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalysisResponse(BaseModel):
    """Complete analysis result"""

    tender: TenderResponse
    status: str
    processing_time: Optional[float] = None
    filter_result: Optional[FilterResultResponse] = None
    rating_result: Optional[RatingResultResponse] = None
    bid_document: Optional[BidDocumentResponse] = None
    error: Optional[str] = None


class TenderListResponse(BaseModel):
    """Paginated list of tenders"""

    tenders: List[TenderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    version: str
    database: str
    llm: str
