"""Data models for tenders and processing results"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .agents.filter import FilterResult
    from .agents.rating import RatingResult
    from .agents.generator import BidDocument


class TenderCategory(str, Enum):
    """Categories for tender classification"""
    CYBERSECURITY = "cybersecurity"
    ARTIFICIAL_INTELLIGENCE = "ai"
    SOFTWARE_DEVELOPMENT = "software"
    OTHER = "other"


class Tender(BaseModel):
    """Input tender data"""
    id: str
    title: str
    description: str
    organization: str
    deadline: str
    estimated_value: Optional[str] = None


class ProcessedTender(BaseModel):
    """Complete analysis result"""
    tender: Tender
    filter_result: Optional[dict] = None  # Will be FilterResult
    rating_result: Optional[dict] = None  # Will be RatingResult
    bid_document: Optional[dict] = None  # Will be BidDocument
    processing_time: float = 0.0
    status: str = "pending"
