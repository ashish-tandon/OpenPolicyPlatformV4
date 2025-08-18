"""
Database Configuration

This module handles database connection configuration and settings.
"""

import os
from typing import Optional
from dataclasses import dataclass
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    host: str = "localhost"
    port: int = 5432
    database: str = "openpolicy"
    username: str = "openpolicy"
    password: Optional[str] = None
    
    def get_url(self) -> str:
        """Get the database URL for SQLAlchemy"""
        if self.password:
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            return f"postgresql://{self.username}@{self.host}:{self.port}/{self.database}"


def get_database_config() -> DatabaseConfig:
    """Get database configuration from environment variables or defaults"""
    return DatabaseConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "openpolicy"),
        username=os.getenv("DB_USER", "openpolicy"),
        password=os.getenv("DB_PASSWORD", "openpolicy123")
    )


def get_database_url():
    """Get database URL from environment variables or use default"""
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    name = os.getenv('DB_NAME', 'openpolicy')
    user = os.getenv('DB_USER', 'openpolicy')
    password = os.getenv('DB_PASSWORD', 'openpolicy123')
    
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"

def get_engine():
    """Get SQLAlchemy engine with connection pooling"""
    database_url = get_database_url()
    
    # Configure connection pooling
    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=5,  # Maximum number of connections in the pool
        max_overflow=10,  # Maximum number of connections that can be created beyond pool_size
        pool_timeout=30,  # Timeout for getting a connection from the pool
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_pre_ping=True,  # Verify connections before use
        echo=False  # Set to True for SQL logging
    )
    
    return engine

def get_session():
    """Get database session"""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def create_engine_from_config(config_or_url) -> 'Engine':
    """Create SQLAlchemy engine from config or URL string"""
    if isinstance(config_or_url, str):
        return create_engine(config_or_url, echo=False)
    else:
        return create_engine(config_or_url.get_url(), echo=False)


def get_session_factory(engine=None):
    """Get session factory"""
    if engine is None:
        engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()