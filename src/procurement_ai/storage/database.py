"""Database configuration and session management"""

from contextlib import contextmanager
from typing import Generator
import os

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool


# Base class for all SQLAlchemy models
Base = declarative_base()


class Database:
    """
    Database manager with connection pooling and session management
    
    Best practices:
    - Separate read/write connections for scaling
    - Connection pooling for performance
    - Context managers for session lifecycle
    - Support for testing with in-memory SQLite
    """
    
    def __init__(
        self,
        database_url: str | None = None,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
    ):
        """
        Initialize database connection
        
        Args:
            database_url: Database connection string (e.g., postgresql://user:pass@localhost/db)
            echo: If True, log all SQL statements (useful for debugging)
            pool_size: Number of connections to keep in pool
            max_overflow: Max connections beyond pool_size
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@127.0.0.1:5432/procurement_ai?gssencmode=disable"
        )
        
        # For testing with SQLite in-memory
        if self.database_url.startswith("sqlite"):
            self.engine = create_engine(
                self.database_url,
                echo=echo,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,  # Required for SQLite in-memory
            )
        else:
            # Production PostgreSQL configuration
            self.engine = create_engine(
                self.database_url,
                echo=echo,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=3600,  # Recycle connections after 1 hour
            )
        
        # Enable PostgreSQL-specific optimizations
        if self.database_url.startswith("postgresql"):
            @event.listens_for(self.engine, "connect")
            def set_search_path(dbapi_conn, connection_record):
                """Set search path for multi-schema support"""
                cursor = dbapi_conn.cursor()
                cursor.execute("SET search_path TO public")
                cursor.close()
        
        # Session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
    
    @classmethod
    def from_config(cls, config=None) -> "Database":
        """
        Create database from config object
        
        Args:
            config: Config object with DATABASE_URL (optional)
        
        Returns:
            Database instance
        """
        from procurement_ai.config import Config
        
        if config is None:
            config = Config()
        
        database_url = getattr(config, "DATABASE_URL", None) or os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@127.0.0.1:5432/procurement_ai?gssencmode=disable"
        )
        
        return cls(database_url=database_url)
    
    def create_all(self):
        """Create all tables (use for development/testing, not production)"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_all(self):
        """Drop all tables (careful! For testing only)"""
        Base.metadata.drop_all(bind=self.engine)
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions
        
        Usage:
            with db.get_session() as session:
                user = session.query(User).first()
        
        Automatically:
        - Commits on success
        - Rolls back on error
        - Closes session when done
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """Check if database is accessible"""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception:
            return False


# Global database instance (initialized in main)
_db: Database | None = None


def init_db(database_url: str | None = None, **kwargs) -> Database:
    """
    Initialize global database instance
    
    Args:
        database_url: Database connection string
        **kwargs: Additional arguments for Database class
    
    Returns:
        Database instance
    """
    global _db
    _db = Database(database_url=database_url, **kwargs)
    return _db


def get_db() -> Database:
    """
    Get global database instance
    
    Raises:
        RuntimeError: If database not initialized
    """
    if _db is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() first."
        )
    return _db


# Dependency for FastAPI (future use)
def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions
    
    Usage:
        @app.get("/users")
        def list_users(session: Session = Depends(get_db_session)):
            return session.query(User).all()
    """
    db = get_db()
    with db.get_session() as session:
        yield session
