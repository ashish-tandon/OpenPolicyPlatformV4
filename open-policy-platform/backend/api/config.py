"""
API Configuration Settings
"""

import os
from typing import List, Optional, Union
from pydantic import field_validator, field_serializer
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "Open Policy Platform"
    version: str = "1.0.0"
    environment: str = "development"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database (canonical)
    database_url: str = "postgresql://postgres@localhost:5432/openpolicy"

    # Optional logical databases
    app_database_url: Optional[str] = None
    scrapers_database_url: Optional[str] = None
    auth_database_url: Optional[str] = None
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    jwt_secret: str = "your-jwt-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_origins: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    # Trusted hosts
    allowed_hosts: Union[str, List[str]] = ["*"]
    
    @field_validator('allowed_origins', 'allowed_hosts', mode='before')
    @classmethod
    def parse_list_fields(cls, v):
        """Parse comma-separated strings into lists"""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        elif isinstance(v, list):
            return v
        return v
    
    # Logging
    log_level: str = "INFO"
    
    # Redis (for caching and sessions)
    redis_url: str = "redis://localhost:6379"
    
    # External APIs
    openai_api_key: str = ""
    
    # Scraping
    scraper_timeout: int = 30
    max_concurrent_scrapers: int = 5
    # Optional directories to locate scraper artifacts (defaults to current working directory)
    scraper_reports_dir: str = ""
    scraper_logs_dir: str = ""
    
    # File upload
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    upload_dir: str = "uploads"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "env_parse_none_str": "none"
    }

    # Derived properties with fallback to canonical database_url
    @property
    def resolved_app_database_url(self) -> str:
        return self.app_database_url or self.database_url

    @property
    def resolved_scrapers_database_url(self) -> str:
        return self.scrapers_database_url or self.database_url

    @property
    def resolved_auth_database_url(self) -> str:
        return self.auth_database_url or self.database_url

# Global settings instance
settings = Settings()
