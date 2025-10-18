"""Application configuration."""

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class AppConfig(BaseModel):
    """Application configuration."""
    
    # Application settings
    app_env: str = Field(
        default="development",
        description="Application environment"
    )
    debug: bool = Field(
        default=True,
        description="Debug mode"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    # Database settings
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/ai_recruiter",
        description="Database connection URL"
    )
    db_echo: bool = Field(
        default=False,
        description="Echo SQL queries"
    )
    
    # Redis settings
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    # External API keys
    linkedin_api_key: Optional[str] = Field(
        default=None,
        description="LinkedIn API key"
    )
    indeed_api_key: Optional[str] = Field(
        default=None,
        description="Indeed API key"
    )
    greenhouse_api_key: Optional[str] = Field(
        default=None,
        description="Greenhouse API key"
    )
    
    # Email settings
    smtp_host: str = Field(
        default="smtp.gmail.com",
        description="SMTP host"
    )
    smtp_port: int = Field(
        default=587,
        description="SMTP port"
    )
    smtp_user: Optional[str] = Field(
        default=None,
        description="SMTP username"
    )
    smtp_password: Optional[str] = Field(
        default=None,
        description="SMTP password"
    )
    
    # Application limits
    max_resume_parse_size_mb: int = Field(
        default=10,
        description="Maximum resume file size in MB"
    )


def get_app_config() -> AppConfig:
    """Get application configuration from environment variables."""
    return AppConfig(
        app_env=os.getenv("APP_ENV", "development"),
        debug=os.getenv("DEBUG", "True").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        database_url=os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/ai_recruiter"),
        db_echo=os.getenv("DB_ECHO", "False").lower() == "true",
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        linkedin_api_key=os.getenv("LINKEDIN_API_KEY"),
        indeed_api_key=os.getenv("INDEED_API_KEY"),
        greenhouse_api_key=os.getenv("GREENHOUSE_API_KEY"),
        smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_user=os.getenv("SMTP_USER"),
        smtp_password=os.getenv("SMTP_PASSWORD"),
        max_resume_parse_size_mb=int(os.getenv("MAX_RESUME_PARSE_SIZE_MB", "10")),
    )
