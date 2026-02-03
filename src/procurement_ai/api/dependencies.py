"""
Dependency injection for FastAPI
Provides database sessions, config, and services
"""
from functools import lru_cache
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from procurement_ai.config import Config
from procurement_ai.storage import DatabaseManager
from procurement_ai.storage.repositories import OrganizationRepository
from procurement_ai.services.llm import LLMService


@lru_cache()
def get_db() -> DatabaseManager:
    """Get database manager (cached)"""
    return DatabaseManager.from_config()


@lru_cache()
def get_config() -> Config:
    """Get config (cached)"""
    return Config()


@lru_cache()
def get_llm_service() -> LLMService:
    """Get LLM service (cached)"""
    config = get_config()
    return LLMService(config)


def get_db_session(db: DatabaseManager = Depends(get_db)):
    """Get database session (context manager)"""
    with db.get_session() as session:
        yield session


def get_current_organization(
    x_api_key: str = Header(..., description="API key for authentication"),
    session: Session = Depends(get_db_session),
):
    """
    Authenticate request and get organization
    
    For MVP: Simple API key in header
    Future: JWT tokens, OAuth, etc.
    
    Returns organization object that stays bound to the provided session
    """
    # Try to find organization by slug (API key = slug for MVP)
    org_repo = OrganizationRepository(session)
    org = org_repo.get_by_slug(x_api_key)
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if not org.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization is inactive",
        )
    
    return org
