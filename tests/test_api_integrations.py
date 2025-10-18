"""Tests for API integrations."""

import pytest
from tools.api_integrations import (
    LinkedInIntegration,
    IndeedIntegration,
    GreenhouseIntegration,
    Candidate,
    JobPosting
)


class TestLinkedInIntegration:
    """Test suite for LinkedIn integration."""
    
    def test_initialization(self):
        """Test integration initialization."""
        integration = LinkedInIntegration(api_key="test-key")
        assert integration.api_key == "test-key"
        assert "linkedin" in integration.base_url.lower()
    
    def test_search_candidates_without_key(self):
        """Test searching without API key raises error."""
        integration = LinkedInIntegration()
        
        with pytest.raises(ValueError, match="API key is required"):
            integration.search_candidates("Python developer")
    
    def test_get_candidate_without_key(self):
        """Test getting candidate without API key raises error."""
        integration = LinkedInIntegration()
        
        with pytest.raises(ValueError, match="API key is required"):
            integration.get_candidate("candidate_123")
    
    def test_get_candidate_with_key(self):
        """Test getting candidate with API key."""
        integration = LinkedInIntegration(api_key="test-key")
        candidate = integration.get_candidate("candidate_123")
        
        assert isinstance(candidate, Candidate)
        assert candidate.source == "linkedin"


class TestIndeedIntegration:
    """Test suite for Indeed integration."""
    
    def test_initialization(self):
        """Test integration initialization."""
        integration = IndeedIntegration(api_key="test-key")
        assert integration.api_key == "test-key"
        assert "indeed" in integration.base_url.lower()
    
    def test_search_candidates_without_key(self):
        """Test searching without API key raises error."""
        integration = IndeedIntegration()
        
        with pytest.raises(ValueError, match="API key is required"):
            integration.search_candidates("Java developer")
    
    def test_get_candidate_with_key(self):
        """Test getting candidate with API key."""
        integration = IndeedIntegration(api_key="test-key")
        candidate = integration.get_candidate("candidate_456")
        
        assert isinstance(candidate, Candidate)
        assert candidate.source == "indeed"


class TestGreenhouseIntegration:
    """Test suite for Greenhouse integration."""
    
    def test_initialization(self):
        """Test integration initialization."""
        integration = GreenhouseIntegration(api_key="test-key")
        assert integration.api_key == "test-key"
        assert "greenhouse" in integration.base_url.lower()
    
    def test_search_candidates_without_key(self):
        """Test searching without API key raises error."""
        integration = GreenhouseIntegration()
        
        with pytest.raises(ValueError, match="API key is required"):
            integration.search_candidates("Software engineer")
    
    def test_get_candidate_with_key(self):
        """Test getting candidate with API key."""
        integration = GreenhouseIntegration(api_key="test-key")
        candidate = integration.get_candidate("candidate_789")
        
        assert isinstance(candidate, Candidate)
        assert candidate.source == "greenhouse"
    
    def test_create_candidate(self):
        """Test creating candidate in Greenhouse."""
        integration = GreenhouseIntegration(api_key="test-key")
        
        candidate = Candidate(
            id="test_id",
            name="John Doe",
            email="john@example.com",
            source="manual"
        )
        
        candidate_id = integration.create_candidate(candidate, job_id="job_123")
        assert candidate_id is not None
        assert isinstance(candidate_id, str)
    
    def test_update_candidate_stage(self):
        """Test updating candidate stage."""
        integration = GreenhouseIntegration(api_key="test-key")
        
        success = integration.update_candidate_stage(
            candidate_id="candidate_789",
            stage_id="stage_456"
        )
        
        assert success is True


class TestDataModels:
    """Test data models."""
    
    def test_candidate_model(self):
        """Test Candidate model."""
        candidate = Candidate(
            id="123",
            name="John Doe",
            email="john@example.com",
            phone="+1-555-123-4567",
            source="linkedin",
            metadata={"location": "San Francisco"}
        )
        
        assert candidate.id == "123"
        assert candidate.name == "John Doe"
        assert candidate.email == "john@example.com"
        assert candidate.metadata["location"] == "San Francisco"
    
    def test_job_posting_model(self):
        """Test JobPosting model."""
        job = JobPosting(
            id="job_123",
            title="Software Engineer",
            description="We are hiring",
            requirements=["Python", "AWS"],
            location="Remote",
            company="Tech Corp"
        )
        
        assert job.id == "job_123"
        assert job.title == "Software Engineer"
        assert len(job.requirements) == 2
        assert "Python" in job.requirements
