"""LLM configuration and provider management."""

import os
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMConfig(BaseModel):
    """Configuration for LLM providers."""
    
    # Provider settings
    default_provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        description="Default LLM provider to use"
    )
    
    # OpenAI settings
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )
    openai_model: str = Field(
        default="gpt-4-turbo-preview",
        description="OpenAI model to use"
    )
    
    # Anthropic settings
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key"
    )
    anthropic_model: str = Field(
        default="claude-3-opus-20240229",
        description="Anthropic model to use"
    )
    
    # General LLM settings
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM responses"
    )
    max_tokens: int = Field(
        default=2000,
        ge=1,
        le=8000,
        description="Maximum tokens for LLM responses"
    )
    
    # Rate limiting
    max_requests_per_minute: int = Field(
        default=60,
        description="Maximum requests per minute per provider"
    )
    
    class Config:
        """Pydantic config."""
        use_enum_values = True


def get_llm_config() -> LLMConfig:
    """Get LLM configuration from environment variables."""
    provider = os.getenv("DEFAULT_LLM_PROVIDER", "openai")
    
    return LLMConfig(
        default_provider=provider,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
        max_requests_per_minute=int(os.getenv("MAX_REQUESTS_PER_MINUTE", "60")),
    )
