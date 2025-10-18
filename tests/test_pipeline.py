"""Tests for recruitment pipeline."""

import pytest
from workflows.pipeline import RecruitmentPipeline, PipelineStage, CandidateStatus


class TestRecruitmentPipeline:
    """Test suite for RecruitmentPipeline."""
    
    @pytest.fixture
    def pipeline(self):
        """Create a pipeline instance."""
        return RecruitmentPipeline()
    
    def test_add_candidate(self, pipeline):
        """Test adding a candidate to the pipeline."""
        status = pipeline.add_candidate(
            candidate_id="candidate_1",
            candidate_name="John Doe",
            email="john@example.com",
            score=85.0
        )
        
        assert isinstance(status, CandidateStatus)
        assert status.candidate_id == "candidate_1"
        assert status.candidate_name == "John Doe"
        assert status.score == 85.0
        assert status.current_stage == PipelineStage.SOURCING
    
    def test_add_duplicate_candidate(self, pipeline):
        """Test adding duplicate candidate raises error."""
        pipeline.add_candidate(
            candidate_id="candidate_1",
            candidate_name="John Doe",
            email="john@example.com"
        )
        
        with pytest.raises(ValueError, match="already exists"):
            pipeline.add_candidate(
                candidate_id="candidate_1",
                candidate_name="Jane Smith",
                email="jane@example.com"
            )
    
    def test_move_candidate(self, pipeline):
        """Test moving candidate to new stage."""
        pipeline.add_candidate(
            candidate_id="candidate_1",
            candidate_name="John Doe",
            email="john@example.com"
        )
        
        status = pipeline.move_candidate(
            candidate_id="candidate_1",
            new_stage=PipelineStage.SCREENING,
            note="Moving to screening"
        )
        
        assert status.current_stage == PipelineStage.SCREENING
        assert len(status.notes) == 1
        assert "Moving to screening" in status.notes[0]
    
    def test_move_nonexistent_candidate(self, pipeline):
        """Test moving nonexistent candidate raises error."""
        with pytest.raises(ValueError, match="not found"):
            pipeline.move_candidate(
                candidate_id="nonexistent",
                new_stage=PipelineStage.SCREENING
            )
    
    def test_update_score(self, pipeline):
        """Test updating candidate score."""
        pipeline.add_candidate(
            candidate_id="candidate_1",
            candidate_name="John Doe",
            email="john@example.com",
            score=75.0
        )
        
        status = pipeline.update_score("candidate_1", 90.0)
        
        assert status.score == 90.0
    
    def test_add_note(self, pipeline):
        """Test adding note to candidate."""
        pipeline.add_candidate(
            candidate_id="candidate_1",
            candidate_name="John Doe",
            email="john@example.com"
        )
        
        status = pipeline.add_note("candidate_1", "Great interview")
        
        assert len(status.notes) == 1
        assert "Great interview" in status.notes[0]
    
    def test_get_candidates_by_stage(self, pipeline):
        """Test getting candidates by stage."""
        pipeline.add_candidate(
            candidate_id="candidate_1",
            candidate_name="John Doe",
            email="john@example.com",
            initial_stage=PipelineStage.SCREENING
        )
        pipeline.add_candidate(
            candidate_id="candidate_2",
            candidate_name="Jane Smith",
            email="jane@example.com",
            initial_stage=PipelineStage.SCREENING
        )
        pipeline.add_candidate(
            candidate_id="candidate_3",
            candidate_name="Bob Johnson",
            email="bob@example.com",
            initial_stage=PipelineStage.OFFER
        )
        
        screening_candidates = pipeline.get_candidates_by_stage(PipelineStage.SCREENING)
        
        assert len(screening_candidates) == 2
        assert all(c.current_stage == PipelineStage.SCREENING for c in screening_candidates)
    
    def test_get_pipeline_metrics(self, pipeline):
        """Test getting pipeline metrics."""
        pipeline.add_candidate(
            candidate_id="candidate_1",
            candidate_name="John Doe",
            email="john@example.com",
            score=85.0
        )
        pipeline.add_candidate(
            candidate_id="candidate_2",
            candidate_name="Jane Smith",
            email="jane@example.com",
            initial_stage=PipelineStage.HIRED,
            score=95.0
        )
        
        metrics = pipeline.get_pipeline_metrics()
        
        assert metrics["total_candidates"] == 2
        assert metrics["average_score"] == 90.0
        assert metrics["conversion_rate"] == 50.0
        assert "by_stage" in metrics
    
    def test_get_top_candidates(self, pipeline):
        """Test getting top candidates by score."""
        pipeline.add_candidate(
            candidate_id="candidate_1",
            candidate_name="John Doe",
            email="john@example.com",
            score=75.0
        )
        pipeline.add_candidate(
            candidate_id="candidate_2",
            candidate_name="Jane Smith",
            email="jane@example.com",
            score=95.0
        )
        pipeline.add_candidate(
            candidate_id="candidate_3",
            candidate_name="Bob Johnson",
            email="bob@example.com",
            score=85.0
        )
        
        top_candidates = pipeline.get_top_candidates(limit=2)
        
        assert len(top_candidates) == 2
        assert top_candidates[0].candidate_name == "Jane Smith"
        assert top_candidates[1].candidate_name == "Bob Johnson"
    
    def test_get_top_candidates_by_stage(self, pipeline):
        """Test getting top candidates filtered by stage."""
        pipeline.add_candidate(
            candidate_id="candidate_1",
            candidate_name="John Doe",
            email="john@example.com",
            initial_stage=PipelineStage.SCREENING,
            score=85.0
        )
        pipeline.add_candidate(
            candidate_id="candidate_2",
            candidate_name="Jane Smith",
            email="jane@example.com",
            initial_stage=PipelineStage.OFFER,
            score=95.0
        )
        
        top_screening = pipeline.get_top_candidates(
            limit=10,
            stage=PipelineStage.SCREENING
        )
        
        assert len(top_screening) == 1
        assert top_screening[0].candidate_name == "John Doe"
