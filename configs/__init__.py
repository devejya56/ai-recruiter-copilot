"""Configuration module for AI Recruiter Copilot."""

from .llm_config import LLMConfig, get_llm_config
from .app_config import AppConfig, get_app_config

__all__ = [
    "LLMConfig",
    "get_llm_config",
    "AppConfig",
    "get_app_config",
]
