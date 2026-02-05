"""Data models for tenders and processing results"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class TenderCategory(str, Enum):
    """Categories for tender classification"""
    CYBERSECURITY = "cybersecurity"
    ARTIFICIAL_INTELLIGENCE = "ai"
    SOFTWARE_DEVELOPMENT = "software"
    OTHER = "other"


class Tender(BaseModel):
    """Input tender data"""
    id: Optional[str] = None
    title: str
    description: str
    organization: str
    deadline: str
    estimated_value: Optional[str] = None


class ProcessedTender(BaseModel):
    """Complete analysis result"""
    tender: Tender
    filter_result: Optional[object] = None
    rating_result: Optional[object] = None
    bid_document: Optional[object] = None
    processing_time: float = 0.0
    status: str = "pending"
    error: Optional[str] = None
