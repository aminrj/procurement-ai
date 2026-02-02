"""
Repository pattern for data access

Benefits:
- Abstracts database operations from business logic
- Easy to test (can mock repositories)
- Centralized query logic
- Type-safe with proper return types
"""

from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from .models import (
    Organization,
    User,
    TenderDB,
    AnalysisResult,
    BidDocument,
    SubscriptionTier,
    UserRole,
    TenderStatus,
)


class BaseRepository:
    """Base repository with common CRUD operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def commit(self):
        """Commit current transaction"""
        self.session.commit()
    
    def rollback(self):
        """Rollback current transaction"""
        self.session.rollback()
    
    def refresh(self, obj):
        """Refresh object from database"""
        self.session.refresh(obj)


class OrganizationRepository(BaseRepository):
    """Repository for Organization management"""
    
    def create(
        self,
        name: str,
        slug: str,
        subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    ) -> Organization:
        """Create new organization"""
        org = Organization(
            name=name,
            slug=slug,
            subscription_tier=subscription_tier,
        )
        self.session.add(org)
        self.session.flush()  # Get ID without committing
        return org
    
    def get_by_id(self, org_id: int) -> Optional[Organization]:
        """Get organization by ID"""
        return (
            self.session.query(Organization)
            .filter(
                Organization.id == org_id,
                Organization.is_deleted == False
            )
            .first()
        )
    
    def get_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug"""
        return (
            self.session.query(Organization)
            .filter(
                Organization.slug == slug,
                Organization.is_deleted == False
            )
            .first()
        )
    
    def list_active(self, limit: int = 100) -> List[Organization]:
        """List active organizations"""
        return (
            self.session.query(Organization)
            .filter(
                Organization.is_active == True,
                Organization.is_deleted == False
            )
            .limit(limit)
            .all()
        )
    
    def update_usage(self, org_id: int, increment: int = 1) -> bool:
        """Increment monthly analysis count"""
        org = self.get_by_id(org_id)
        if not org:
            return False
        
        org.monthly_analysis_count += increment
        org.updated_at = datetime.utcnow()
        return True
    
    def reset_monthly_usage(self, org_id: int) -> bool:
        """Reset monthly analysis count (called by cron)"""
        org = self.get_by_id(org_id)
        if not org:
            return False
        
        org.monthly_analysis_count = 0
        org.updated_at = datetime.utcnow()
        return True
    
    def can_analyze(self, org_id: int) -> bool:
        """Check if organization can analyze more tenders"""
        org = self.get_by_id(org_id)
        if not org or not org.is_active:
            return False
        
        return org.monthly_analysis_count < org.monthly_analysis_limit
    
    def soft_delete(self, org_id: int) -> bool:
        """Soft delete organization"""
        org = self.get_by_id(org_id)
        if not org:
            return False
        
        org.is_deleted = True
        org.is_active = False
        org.updated_at = datetime.utcnow()
        return True


class UserRepository(BaseRepository):
    """Repository for User management"""
    
    def create(
        self,
        organization_id: int,
        email: str,
        hashed_password: str,
        full_name: str,
        role: UserRole = UserRole.MEMBER
    ) -> User:
        """Create new user"""
        user = User(
            organization_id=organization_id,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
        )
        self.session.add(user)
        self.session.flush()
        return user
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return (
            self.session.query(User)
            .filter(
                User.id == user_id,
                User.is_deleted == False
            )
            .first()
        )
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email (case-insensitive)"""
        return (
            self.session.query(User)
            .filter(
                User.email.ilike(email),
                User.is_deleted == False
            )
            .first()
        )
    
    def list_by_organization(self, org_id: int) -> List[User]:
        """List all users in organization"""
        return (
            self.session.query(User)
            .filter(
                User.organization_id == org_id,
                User.is_deleted == False
            )
            .all()
        )
    
    def update_last_login(self, user_id: int) -> bool:
        """Update last login timestamp"""
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        user.last_login_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        return True
    
    def soft_delete(self, user_id: int) -> bool:
        """Soft delete user"""
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        user.is_deleted = True
        user.is_active = False
        user.updated_at = datetime.utcnow()
        return True


class TenderRepository(BaseRepository):
    """Repository for Tender management"""
    
    def create(
        self,
        organization_id: int,
        title: str,
        description: str,
        organization_name: str,
        deadline: Optional[str] = None,
        estimated_value: Optional[str] = None,
        external_id: Optional[str] = None,
        source: Optional[str] = None,
        **kwargs
    ) -> TenderDB:
        """Create new tender"""
        tender = TenderDB(
            organization_id=organization_id,
            title=title,
            description=description,
            organization_name=organization_name,
            deadline=deadline,
            estimated_value=estimated_value,
            external_id=external_id,
            source=source,
            **kwargs
        )
        self.session.add(tender)
        self.session.flush()
        return tender
    
    def get_by_id(self, tender_id: int, org_id: int) -> Optional[TenderDB]:
        """Get tender by ID (with organization isolation)"""
        return (
            self.session.query(TenderDB)
            .filter(
                TenderDB.id == tender_id,
                TenderDB.organization_id == org_id,
                TenderDB.is_deleted == False
            )
            .first()
        )
    
    def get_by_external_id(
        self,
        external_id: str,
        org_id: int
    ) -> Optional[TenderDB]:
        """Get tender by external ID (for deduplication)"""
        return (
            self.session.query(TenderDB)
            .filter(
                TenderDB.external_id == external_id,
                TenderDB.organization_id == org_id,
                TenderDB.is_deleted == False
            )
            .first()
        )
    
    def list_by_organization(
        self,
        org_id: int,
        status: Optional[TenderStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TenderDB]:
        """List tenders for organization"""
        query = (
            self.session.query(TenderDB)
            .filter(
                TenderDB.organization_id == org_id,
                TenderDB.is_deleted == False
            )
        )
        
        if status:
            query = query.filter(TenderDB.status == status)
        
        return (
            query
            .order_by(desc(TenderDB.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
    
    def count_by_organization(
        self,
        org_id: int,
        status: Optional[TenderStatus] = None
    ) -> int:
        """Count tenders for organization"""
        query = (
            self.session.query(TenderDB)
            .filter(
                TenderDB.organization_id == org_id,
                TenderDB.is_deleted == False
            )
        )
        
        if status:
            query = query.filter(TenderDB.status == status)
        
        return query.count()
    
    def update_status(
        self,
        tender_id: int,
        status: TenderStatus,
        error_message: Optional[str] = None,
        processing_time: Optional[float] = None
    ) -> bool:
        """Update tender processing status"""
        tender = self.session.query(TenderDB).filter(
            TenderDB.id == tender_id
        ).first()
        
        if not tender:
            return False
        
        tender.status = status
        tender.updated_at = datetime.utcnow()
        
        if error_message:
            tender.error_message = error_message
        
        if processing_time:
            tender.processing_time = processing_time
        
        return True
    
    def soft_delete(self, tender_id: int, org_id: int) -> bool:
        """Soft delete tender"""
        tender = self.get_by_id(tender_id, org_id)
        if not tender:
            return False
        
        tender.is_deleted = True
        tender.updated_at = datetime.utcnow()
        return True


class AnalysisRepository(BaseRepository):
    """Repository for AnalysisResult management"""
    
    def create(
        self,
        tender_id: int,
        is_relevant: bool,
        confidence: float,
        filter_categories: Optional[List[str]] = None,
        filter_reasoning: Optional[str] = None,
        **kwargs
    ) -> AnalysisResult:
        """Create new analysis result"""
        analysis = AnalysisResult(
            tender_id=tender_id,
            is_relevant=is_relevant,
            confidence=confidence,
            filter_categories=filter_categories,
            filter_reasoning=filter_reasoning,
            **kwargs
        )
        self.session.add(analysis)
        self.session.flush()
        return analysis
    
    def get_by_tender_id(self, tender_id: int) -> Optional[AnalysisResult]:
        """Get analysis for a tender"""
        return (
            self.session.query(AnalysisResult)
            .filter(AnalysisResult.tender_id == tender_id)
            .first()
        )
    
    def get_latest_by_tender(self, tender_id: int) -> Optional[AnalysisResult]:
        """Alias for get_by_tender_id (for API compatibility)"""
        return self.get_by_tender_id(tender_id)
    
    def update_rating(
        self,
        tender_id: int,
        overall_score: float,
        strategic_fit: float,
        financial_attractiveness: float,
        win_probability: float,
        resource_requirements: float,
        strengths: List[str],
        risks: List[str],
        requirements: List[str],
        recommendation: str
    ) -> bool:
        """Update analysis with rating results"""
        analysis = self.get_by_tender_id(tender_id)
        if not analysis:
            return False
        
        analysis.overall_score = overall_score
        analysis.strategic_fit = strategic_fit
        analysis.financial_attractiveness = financial_attractiveness
        analysis.win_probability = win_probability
        analysis.resource_requirements = resource_requirements
        analysis.strengths = strengths
        analysis.risks = risks
        analysis.requirements = requirements
        analysis.recommendation = recommendation
        analysis.updated_at = datetime.utcnow()
        
        return True
    
    def get_high_score_tenders(
        self,
        org_id: int,
        min_score: float = 7.0,
        limit: int = 50
    ) -> List[TenderDB]:
        """Get tenders with high ratings for an organization"""
        return (
            self.session.query(TenderDB)
            .join(AnalysisResult)
            .filter(
                TenderDB.organization_id == org_id,
                TenderDB.is_deleted == False,
                AnalysisResult.is_relevant == True,
                AnalysisResult.overall_score >= min_score
            )
            .order_by(desc(AnalysisResult.overall_score))
            .limit(limit)
            .all()
        )


class BidDocumentRepository(BaseRepository):
    """Repository for BidDocument management"""
    
    def create(
        self,
        tender_id: int,
        executive_summary: str,
        capabilities: str,
        approach: str,
        value_proposition: str,
        **kwargs
    ) -> BidDocument:
        """Create new bid document"""
        doc = BidDocument(
            tender_id=tender_id,
            executive_summary=executive_summary,
            capabilities=capabilities,
            approach=approach,
            value_proposition=value_proposition,
            **kwargs
        )
        self.session.add(doc)
        self.session.flush()
        return doc
    
    def get_by_tender_id(self, tender_id: int) -> Optional[BidDocument]:
        """Get bid document for a tender"""
        return (
            self.session.query(BidDocument)
            .filter(BidDocument.tender_id == tender_id)
            .first()
        )
    
    def get_latest_by_tender(self, tender_id: int) -> Optional[BidDocument]:
        """Alias for get_by_tender_id (for API compatibility)"""
        return self.get_by_tender_id(tender_id)
    
    def list_by_organization(
        self,
        org_id: int,
        limit: int = 100
    ) -> List[BidDocument]:
        """List bid documents for organization"""
        return (
            self.session.query(BidDocument)
            .join(TenderDB)
            .filter(
                TenderDB.organization_id == org_id,
                TenderDB.is_deleted == False
            )
            .order_by(desc(BidDocument.created_at))
            .limit(limit)
            .all()
        )
