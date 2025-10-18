"""Recruitment pipeline management."""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class PipelineStage(str, Enum):
    """Recruitment pipeline stages."""
    
    SOURCING = "sourcing"
    SCREENING = "screening"
    PHONE_SCREEN = "phone_screen"
    TECHNICAL_INTERVIEW = "technical_interview"
    BEHAVIORAL_INTERVIEW = "behavioral_interview"
    FINAL_INTERVIEW = "final_interview"
    OFFER = "offer"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class CandidateStatus(BaseModel):
    """Status of a candidate in the pipeline."""
    
    candidate_id: str
    candidate_name: str
    email: str
    current_stage: PipelineStage
    score: Optional[float] = None
    notes: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RecruitmentPipeline:
    """
    Manages the recruitment pipeline and candidate progression.
    
    Tracks candidates through various stages of the recruitment process
    and provides pipeline analytics.
    """
    
    def __init__(self):
        """Initialize the recruitment pipeline."""
        self.candidates: Dict[str, CandidateStatus] = {}
    
    def add_candidate(
        self,
        candidate_id: str,
        candidate_name: str,
        email: str,
        initial_stage: PipelineStage = PipelineStage.SOURCING,
        score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CandidateStatus:
        """
        Add a new candidate to the pipeline.
        
        Args:
            candidate_id: Unique candidate identifier
            candidate_name: Candidate name
            email: Candidate email
            initial_stage: Initial pipeline stage
            score: Initial screening score
            metadata: Additional candidate data
            
        Returns:
            CandidateStatus object
        """
        if candidate_id in self.candidates:
            raise ValueError(f"Candidate {candidate_id} already exists in pipeline")
        
        status = CandidateStatus(
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            email=email,
            current_stage=initial_stage,
            score=score,
            metadata=metadata or {}
        )
        
        self.candidates[candidate_id] = status
        return status
    
    def move_candidate(
        self,
        candidate_id: str,
        new_stage: PipelineStage,
        note: Optional[str] = None
    ) -> CandidateStatus:
        """
        Move a candidate to a new pipeline stage.
        
        Args:
            candidate_id: Candidate identifier
            new_stage: New pipeline stage
            note: Optional note about the stage change
            
        Returns:
            Updated CandidateStatus
        """
        if candidate_id not in self.candidates:
            raise ValueError(f"Candidate {candidate_id} not found in pipeline")
        
        candidate = self.candidates[candidate_id]
        candidate.current_stage = new_stage
        candidate.updated_at = datetime.now()
        
        if note:
            candidate.notes.append(f"[{datetime.now().isoformat()}] {note}")
        
        return candidate
    
    def update_score(
        self,
        candidate_id: str,
        score: float
    ) -> CandidateStatus:
        """
        Update a candidate's score.
        
        Args:
            candidate_id: Candidate identifier
            score: New score
            
        Returns:
            Updated CandidateStatus
        """
        if candidate_id not in self.candidates:
            raise ValueError(f"Candidate {candidate_id} not found in pipeline")
        
        candidate = self.candidates[candidate_id]
        candidate.score = score
        candidate.updated_at = datetime.now()
        
        return candidate
    
    def add_note(
        self,
        candidate_id: str,
        note: str
    ) -> CandidateStatus:
        """
        Add a note to a candidate's profile.
        
        Args:
            candidate_id: Candidate identifier
            note: Note to add
            
        Returns:
            Updated CandidateStatus
        """
        if candidate_id not in self.candidates:
            raise ValueError(f"Candidate {candidate_id} not found in pipeline")
        
        candidate = self.candidates[candidate_id]
        candidate.notes.append(f"[{datetime.now().isoformat()}] {note}")
        candidate.updated_at = datetime.now()
        
        return candidate
    
    def get_candidates_by_stage(
        self,
        stage: PipelineStage
    ) -> List[CandidateStatus]:
        """
        Get all candidates in a specific stage.
        
        Args:
            stage: Pipeline stage
            
        Returns:
            List of candidates in that stage
        """
        return [
            candidate for candidate in self.candidates.values()
            if candidate.current_stage == stage
        ]
    
    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """
        Get pipeline metrics and analytics.
        
        Returns:
            Dictionary with pipeline metrics
        """
        total_candidates = len(self.candidates)
        
        # Count by stage
        stage_counts = {}
        for stage in PipelineStage:
            stage_counts[stage.value] = len(
                self.get_candidates_by_stage(stage)
            )
        
        # Calculate conversion rates
        sourcing_count = stage_counts.get(PipelineStage.SOURCING.value, 0)
        screening_count = stage_counts.get(PipelineStage.SCREENING.value, 0)
        hired_count = stage_counts.get(PipelineStage.HIRED.value, 0)
        
        conversion_rate = 0.0
        if total_candidates > 0:
            conversion_rate = (hired_count / total_candidates) * 100
        
        # Average score
        scored_candidates = [
            c for c in self.candidates.values()
            if c.score is not None
        ]
        avg_score = 0.0
        if scored_candidates:
            avg_score = sum(c.score for c in scored_candidates) / len(scored_candidates)
        
        return {
            "total_candidates": total_candidates,
            "by_stage": stage_counts,
            "conversion_rate": round(conversion_rate, 2),
            "average_score": round(avg_score, 2),
            "active_candidates": total_candidates - stage_counts.get(PipelineStage.HIRED.value, 0) - stage_counts.get(PipelineStage.REJECTED.value, 0) - stage_counts.get(PipelineStage.WITHDRAWN.value, 0)
        }
    
    def get_top_candidates(
        self,
        limit: int = 10,
        stage: Optional[PipelineStage] = None
    ) -> List[CandidateStatus]:
        """
        Get top candidates by score.
        
        Args:
            limit: Number of candidates to return
            stage: Filter by stage (optional)
            
        Returns:
            List of top candidates
        """
        candidates = list(self.candidates.values())
        
        # Filter by stage if specified
        if stage:
            candidates = [c for c in candidates if c.current_stage == stage]
        
        # Filter out candidates without scores
        scored_candidates = [c for c in candidates if c.score is not None]
        
        # Sort by score descending
        sorted_candidates = sorted(
            scored_candidates,
            key=lambda x: x.score,
            reverse=True
        )
        
        return sorted_candidates[:limit]
