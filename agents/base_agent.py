"""Base agent class for all recruiting agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel
from langchain.llms.base import BaseLLM
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from configs.llm_config import LLMConfig, LLMProvider


class AgentResponse(BaseModel):
    """Response from an agent."""
    
    success: bool
    message: str
    data: Dict[str, Any] = {}
    error: Optional[str] = None


class BaseAgent(ABC):
    """Base class for all recruiting agents."""
    
    def __init__(self, llm_config: LLMConfig):
        """
        Initialize the base agent.
        
        Args:
            llm_config: LLM configuration
        """
        self.llm_config = llm_config
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self) -> BaseLLM:
        """
        Initialize the appropriate LLM based on configuration.
        
        Returns:
            Configured LLM instance
        """
        if self.llm_config.default_provider == LLMProvider.OPENAI:
            return ChatOpenAI(
                api_key=self.llm_config.openai_api_key,
                model=self.llm_config.openai_model,
                temperature=self.llm_config.temperature,
                max_tokens=self.llm_config.max_tokens,
            )
        elif self.llm_config.default_provider == LLMProvider.ANTHROPIC:
            return ChatAnthropic(
                api_key=self.llm_config.anthropic_api_key,
                model=self.llm_config.anthropic_model,
                temperature=self.llm_config.temperature,
                max_tokens=self.llm_config.max_tokens,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_config.default_provider}")
    
    @abstractmethod
    def process(self, **kwargs) -> AgentResponse:
        """
        Process a request with this agent.
        
        Args:
            **kwargs: Agent-specific parameters
            
        Returns:
            AgentResponse with results
        """
        pass
    
    def _call_llm(self, prompt: str) -> str:
        """
        Call the LLM with a prompt.
        
        Args:
            prompt: Prompt to send to the LLM
            
        Returns:
            LLM response text
        """
        try:
            response = self.llm.invoke(prompt)
            # Handle different response types
            if hasattr(response, 'content'):
                return response.content
            return str(response)
        except Exception as e:
            raise RuntimeError(f"LLM call failed: {str(e)}")
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the agent name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Get the agent description."""
        pass
