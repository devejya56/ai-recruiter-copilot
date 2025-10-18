"""Tests for agents."""

import pytest
from unittest.mock import Mock, patch
from agents import RecruiterAgent, SourcingAgent, ScreeningAgent, AgentResponse
from configs.llm_config import LLMConfig, LLMProvider
from tools.resume_parser import ParsedResume


@pytest.fixture
def mock_llm_config():
    """Create a mock LLM config."""
    return LLMConfig(
        default_provider=LLMProvider.OPENAI,
        openai_api_key="test-key",
        openai_model="gpt-4",
        temperature=0.7,
        max_tokens=2000
    )


class TestRecruiterAgent:
    """Test suite for RecruiterAgent."""
    
    def test_agent_initialization(self, mock_llm_config):
        """Test agent initialization."""
        agent = RecruiterAgent(mock_llm_config)
        assert agent.name == "RecruiterAgent"
        assert agent.llm_config == mock_llm_config
    
    def test_create_job_requirements_without_description(self, mock_llm_config):
        """Test creating job requirements without description."""
        agent = RecruiterAgent(mock_llm_config)
        response = agent.process(
            action="create_job_requirements",
            job_description=None
        )
        
        assert not response.success
        assert "required" in response.message.lower()
    
    @patch('agents.base_agent.ChatOpenAI')
    def test_create_job_requirements_success(self, mock_openai, mock_llm_config):
        """Test successful job requirements creation."""
        # Mock LLM response
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content="Technical Skills: Python, AWS")
        mock_openai.return_value = mock_llm
        
        agent = RecruiterAgent(mock_llm_config)
        agent.llm = mock_llm
        
        response = agent.process(
            action="create_job_requirements",
            job_description="Software Engineer position"
        )
        
        assert response.success
        assert "requirements" in response.data
    
    def test_unknown_action(self, mock_llm_config):
        """Test handling of unknown action."""
        agent = RecruiterAgent(mock_llm_config)
        response = agent.process(action="unknown_action")
        
        assert not response.success
        assert "Unknown action" in response.message


class TestSourcingAgent:
    """Test suite for SourcingAgent."""
    
    def test_agent_initialization(self, mock_llm_config):
        """Test agent initialization."""
        agent = SourcingAgent(mock_llm_config)
        assert agent.name == "SourcingAgent"
    
    @patch('agents.base_agent.ChatOpenAI')
    def test_generate_search_query(self, mock_openai, mock_llm_config):
        """Test search query generation."""
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content="LinkedIn: Python AND AWS")
        mock_openai.return_value = mock_llm
        
        agent = SourcingAgent(mock_llm_config)
        agent.llm = mock_llm
        
        response = agent.process(
            action="generate_search_query",
            skills=["Python", "AWS"]
        )
        
        assert response.success
        assert "queries" in response.data
    
    @patch('agents.base_agent.ChatOpenAI')
    def test_recommend_sources(self, mock_openai, mock_llm_config):
        """Test source recommendations."""
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content="LinkedIn, GitHub, Stack Overflow")
        mock_openai.return_value = mock_llm
        
        agent = SourcingAgent(mock_llm_config)
        agent.llm = mock_llm
        
        response = agent.process(
            action="recommend_sources",
            skills=["Python"]
        )
        
        assert response.success
        assert "recommendations" in response.data


class TestScreeningAgent:
    """Test suite for ScreeningAgent."""
    
    def test_agent_initialization(self, mock_llm_config):
        """Test agent initialization."""
        agent = ScreeningAgent(mock_llm_config)
        assert agent.name == "ScreeningAgent"
    
    def test_evaluate_fit_without_resume(self, mock_llm_config):
        """Test evaluation without resume."""
        agent = ScreeningAgent(mock_llm_config)
        response = agent.process(
            action="evaluate_fit",
            resume=None
        )
        
        assert not response.success
        assert "required" in response.message.lower()
    
    @patch('agents.base_agent.ChatOpenAI')
    def test_evaluate_fit_success(self, mock_openai, mock_llm_config):
        """Test successful candidate evaluation."""
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content="Strong Fit - 85/100")
        mock_openai.return_value = mock_llm
        
        agent = ScreeningAgent(mock_llm_config)
        agent.llm = mock_llm
        
        resume = ParsedResume(
            raw_text="John Doe - Python Developer",
            name="John Doe",
            email="john@example.com",
            skills=["python", "aws"]
        )
        
        response = agent.process(
            action="evaluate_fit",
            resume=resume
        )
        
        assert response.success
        assert "evaluation" in response.data
    
    def test_calculate_score(self, mock_llm_config):
        """Test score calculation."""
        agent = ScreeningAgent(mock_llm_config)
        
        resume = ParsedResume(
            raw_text="Python Developer",
            name="John Doe",
            skills=["python", "aws", "docker"]
        )
        
        job_requirements = {
            "skills": ["python", "aws"]
        }
        
        response = agent.process(
            action="calculate_score",
            resume=resume,
            job_requirements=job_requirements
        )
        
        assert response.success
        assert "overall_score" in response.data
        assert response.data["matched_skills"] == 2
