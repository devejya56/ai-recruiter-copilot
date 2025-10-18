"""Base Agent class for AI Recruiter Copilot."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from langchain.schema import BaseMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from loguru import logger
import os


class BaseAgent(ABC):
    """Abstract base class for all recruitment agents."""
    
    def __init__(
        self,
        model_name: str = "gpt-4-turbo-preview",
        provider: str = "openai",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        """Initialize base agent.
        
        Args:
            model_name: Name of the LLM model to use
            provider: LLM provider ("openai" or "anthropic")
            temperature: Sampling temperature for generation
            max_tokens: Maximum tokens in response
        """
        self.model_name = model_name
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.llm = self._initialize_llm()
        
        logger.info(
            f"Initialized {self.__class__.__name__} with "
            f"{provider}/{model_name}"
        )
    
    def _initialize_llm(self):
        """Initialize the LLM based on provider."""
        if self.provider == "openai":
            return ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                api_key=os.getenv("OPENAI_API_KEY"),
            )
        elif self.provider == "anthropic":
            return ChatAnthropic(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens_to_sample=self.max_tokens,
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent's primary task.
        
        Args:
            input_data: Input parameters for the agent
            
        Returns:
            Result dictionary with agent outputs
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get agent-specific system prompt."""
        pass
    
    async def invoke(self, messages: List[BaseMessage]) -> str:
        """Invoke LLM with messages.
        
        Args:
            messages: List of messages to send to LLM
            
        Returns:
            LLM response content
        """
        try:
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            raise
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent metadata."""
        return {
            "agent_type": self.__class__.__name__,
            "model_name": self.model_name,
            "provider": self.provider,
            "temperature": self.temperature,
        }
