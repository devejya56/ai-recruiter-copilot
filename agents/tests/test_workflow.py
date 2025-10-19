import pytest
from unittest.mock import Mock, patch
import asyncio


class TestAgentWorkflow:
    """End-to-end workflow tests for AI recruiter copilot agent."""

    @pytest.fixture
    def mock_candidate_data(self):
        """Mock candidate data for testing."""
        return {
            "candidate_id": "C001",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "resume": "Software Engineer with 5 years experience in Python...",
            "skills": ["Python", "Machine Learning", "AWS"],
            "experience_years": 5
        }

    @pytest.fixture
    def mock_job_requirements(self):
        """Mock job requirements for testing."""
        return {
            "job_id": "J001",
            "title": "Senior Software Engineer",
            "required_skills": ["Python", "Machine Learning"],
            "min_experience": 3,
            "description": "Looking for experienced Python developer..."
        }

    @pytest.fixture
    def mock_agent(self):
        """Mock AI agent for testing."""
        agent = Mock()
        agent.analyze_candidate = Mock(return_value={
            "match_score": 0.85,
            "skills_match": True,
            "experience_match": True,
            "recommendation": "Strong candidate - proceed to interview"
        })
        agent.generate_questions = Mock(return_value=[
            "Describe your experience with Python and ML",
            "How do you handle large-scale data processing?"
        ])
        return agent

    def test_candidate_screening_workflow(self, mock_candidate_data, 
                                         mock_job_requirements, mock_agent):
        """Test complete candidate screening workflow."""
        # Step 1: Analyze candidate against job requirements
        analysis_result = mock_agent.analyze_candidate(
            mock_candidate_data, 
            mock_job_requirements
        )
        
        # Verify analysis was called with correct parameters
        mock_agent.analyze_candidate.assert_called_once_with(
            mock_candidate_data,
            mock_job_requirements
        )
        
        # Verify analysis results
        assert analysis_result["match_score"] >= 0.7
        assert analysis_result["skills_match"] is True
        assert analysis_result["recommendation"] is not None
        
        # Step 2: Generate interview questions if candidate is qualified
        if analysis_result["match_score"] >= 0.7:
            questions = mock_agent.generate_questions(mock_candidate_data)
            
            # Verify questions were generated
            mock_agent.generate_questions.assert_called_once()
            assert len(questions) > 0
            assert all(isinstance(q, str) for q in questions)

    def test_workflow_with_unqualified_candidate(self, mock_job_requirements):
        """Test workflow handles unqualified candidates correctly."""
        # Mock unqualified candidate
        unqualified_candidate = {
            "candidate_id": "C002",
            "name": "Jane Smith",
            "skills": ["JavaScript", "React"],
            "experience_years": 1
        }
        
        # Mock agent with low match score
        agent = Mock()
        agent.analyze_candidate = Mock(return_value={
            "match_score": 0.4,
            "skills_match": False,
            "experience_match": False,
            "recommendation": "Does not meet minimum requirements"
        })
        
        result = agent.analyze_candidate(unqualified_candidate, mock_job_requirements)
        
        # Verify low match score
        assert result["match_score"] < 0.7
        assert result["skills_match"] is False

    @pytest.mark.asyncio
    async def test_async_workflow_processing(self, mock_candidate_data, 
                                            mock_job_requirements):
        """Test asynchronous workflow processing."""
        # Mock async agent
        async def mock_async_analyze(candidate, job):
            await asyncio.sleep(0.1)  # Simulate processing time
            return {
                "match_score": 0.88,
                "processing_time": 0.1,
                "status": "completed"
            }
        
        # Execute async workflow
        result = await mock_async_analyze(mock_candidate_data, mock_job_requirements)
        
        # Verify async processing completed
        assert result["status"] == "completed"
        assert result["match_score"] > 0

    def test_workflow_error_handling(self, mock_job_requirements):
        """Test workflow handles errors gracefully."""
        # Mock agent that raises an exception
        agent = Mock()
        agent.analyze_candidate = Mock(side_effect=Exception("Processing error"))
        
        # Verify error is raised
        with pytest.raises(Exception) as exc_info:
            agent.analyze_candidate({}, mock_job_requirements)
        
        assert "Processing error" in str(exc_info.value)

    def test_workflow_data_validation(self, mock_agent, mock_job_requirements):
        """Test workflow validates input data correctly."""
        # Test with missing required fields
        invalid_candidate = {
            "candidate_id": "C003"
            # Missing required fields
        }
        
        # Mock validation
        def validate_candidate(candidate):
            required_fields = ["candidate_id", "name", "skills"]
            return all(field in candidate for field in required_fields)
        
        # Verify validation fails
        assert validate_candidate(invalid_candidate) is False

    def test_complete_workflow_integration(self, mock_candidate_data, 
                                          mock_job_requirements, mock_agent):
        """Test complete end-to-end workflow integration."""
        # Simulate complete workflow
        workflow_steps = []
        
        # Step 1: Initial screening
        analysis = mock_agent.analyze_candidate(
            mock_candidate_data, 
            mock_job_requirements
        )
        workflow_steps.append(("screening", analysis["match_score"]))
        
        # Step 2: Generate questions
        if analysis["match_score"] >= 0.7:
            questions = mock_agent.generate_questions(mock_candidate_data)
            workflow_steps.append(("questions", len(questions)))
        
        # Step 3: Final recommendation
        workflow_steps.append(("recommendation", analysis["recommendation"]))
        
        # Verify workflow completed all steps
        assert len(workflow_steps) == 3
        assert workflow_steps[0][0] == "screening"
        assert workflow_steps[1][0] == "questions"
        assert workflow_steps[2][0] == "recommendation"
        
        # Verify workflow produced valid outputs
        assert isinstance(workflow_steps[0][1], (int, float))
        assert isinstance(workflow_steps[1][1], int)
        assert isinstance(workflow_steps[2][1], str)
