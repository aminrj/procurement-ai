"""
SQLAlchemy database models for multi-tenant SAAS

Design principles:
- Multi-tenancy with organization_id foreign key
- Soft deletes with is_deleted flag
- Audit trails with created_at/updated_at
- Proper indexes for query performance
- JSON fields for flexible data storage
"""

from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    Enum,
    Index,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class SubscriptionTier(str, enum.Enum):
    """Subscription tier for billing"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class UserRole(str, enum.Enum):
    """User role within an organization"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class TenderStatus(str, enum.Enum):
    """Processing status of a tender"""
    PENDING = "pending"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    REJECTED = "rejected"
    FILTERED_OUT = "filtered_out"
    RATED_LOW = "rated_low"
    COMPLETE = "complete"
    ERROR = "error"


# =============================================================================
# Organizations & Users
# =============================================================================

class Organization(Base):
    """
    Multi-tenant organization/workspace
    
    Each organization has:
    - Multiple users with different roles
    - Subscription tier and limits
    - Their own tenders and analyses
    """
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    
    # Subscription
    subscription_tier = Column(
        Enum(SubscriptionTier),
        nullable=False,
        default=SubscriptionTier.FREE
    )
    
    # Usage limits (reset monthly)
    monthly_analysis_limit = Column(Integer, nullable=False, default=100)
    monthly_analysis_count = Column(Integer, nullable=False, default=0)
    
    # Metadata
    is_active = Column(Boolean, nullable=False, default=True)
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    tenders = relationship("TenderDB", back_populates="organization", cascade="all, delete-orphan")
    
    @property
    def analyses_this_month(self) -> int:
        """Alias for monthly_analysis_count"""
        return self.monthly_analysis_count
    
    def can_analyze(self) -> bool:
        """Check if organization can analyze more tenders this month"""
        if not self.is_active or self.is_deleted:
            return False
        return self.monthly_analysis_count < self.monthly_analysis_limit
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}', tier={self.subscription_tier.value})>"


class User(Base):
    """
    User account within an organization
    
    Authentication via JWT tokens
    Role-based access control within organization
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.MEMBER)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role={self.role.value})>"


# =============================================================================
# Tenders & Analysis
# =============================================================================

class TenderDB(Base):
    """
    Procurement tender from various sources
    
    Stores original tender data and metadata
    Links to analysis results
    """
    __tablename__ = "tenders"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # External identifiers (for deduplication)
    external_id = Column(String(255), nullable=True, index=True)
    source = Column(String(100), nullable=True)  # e.g., "ted_europa", "sam_gov", "manual"
    
    # Tender content (matches Pydantic Tender model)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    organization_name = Column(String(255), nullable=False)
    deadline = Column(String(100), nullable=True)
    estimated_value = Column(String(100), nullable=True)
    
    # Additional metadata
    url = Column(String(1000), nullable=True)
    location = Column(String(255), nullable=True)
    categories = Column(JSON, nullable=True)  # List of category strings
    
    # Processing status
    status = Column(
        Enum(TenderStatus),
        nullable=False,
        default=TenderStatus.PENDING,
        index=True
    )
    processing_time = Column(Float, nullable=True)  # seconds
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    published_at = Column(DateTime, nullable=True)  # Original publication date
    
    # Relationships
    organization = relationship("Organization", back_populates="tenders")
    analysis = relationship("AnalysisResult", back_populates="tender", uselist=False, cascade="all, delete-orphan")
    bid_document = relationship("BidDocument", back_populates="tender", uselist=False, cascade="all, delete-orphan")
    
    # Unique constraint: one tender per external_id per organization
    __table_args__ = (
        Index("idx_org_external", "organization_id", "external_id"),
        UniqueConstraint("organization_id", "external_id", name="uq_org_external_id"),
        Index("idx_org_status_created", "organization_id", "status", "created_at"),
    )
    
    def __repr__(self):
        return f"<TenderDB(id={self.id}, title='{self.title[:50]}...', status={self.status.value})>"


class AnalysisResult(Base):
    """
    AI analysis result for a tender
    
    Stores filter, rating, and reasoning from AI agents
    """
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False, unique=True, index=True)
    
    # Filter results
    is_relevant = Column(Boolean, nullable=False)
    confidence = Column(Float, nullable=False)
    filter_categories = Column(JSON, nullable=True)  # List of category strings
    filter_reasoning = Column(Text, nullable=True)
    
    # Rating results (if relevant)
    overall_score = Column(Float, nullable=True)
    strategic_fit = Column(Float, nullable=True)
    financial_attractiveness = Column(Float, nullable=True)
    win_probability = Column(Float, nullable=True)
    resource_requirements = Column(Float, nullable=True)
    
    # Detailed analysis (JSON arrays)
    strengths = Column(JSON, nullable=True)  # List of strings
    risks = Column(JSON, nullable=True)  # List of strings
    requirements = Column(JSON, nullable=True)  # List of strings
    recommendation = Column(Text, nullable=True)
    
    # Metadata
    llm_model = Column(String(100), nullable=True)  # Which model was used
    processing_cost = Column(Float, nullable=True)  # Estimated cost in USD
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    tender = relationship("TenderDB", back_populates="analysis")
    
    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, relevant={self.is_relevant}, score={self.overall_score})>"


class BidDocument(Base):
    """
    Generated bid document content
    
    Stores AI-generated proposal sections
    """
    __tablename__ = "bid_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False, unique=True, index=True)
    
    # Document content (matches Pydantic BidDocument model)
    executive_summary = Column(Text, nullable=False)
    capabilities = Column(Text, nullable=False)
    approach = Column(Text, nullable=False)
    value_proposition = Column(Text, nullable=False)
    
    # Additional sections (JSON for flexibility)
    additional_sections = Column(JSON, nullable=True)
    
    # Generation metadata
    llm_model = Column(String(100), nullable=True)
    generation_cost = Column(Float, nullable=True)  # Estimated cost in USD
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    tender = relationship("TenderDB", back_populates="bid_document")
    
    def __repr__(self):
        return f"<BidDocument(id={self.id}, tender_id={self.tender_id})>"
