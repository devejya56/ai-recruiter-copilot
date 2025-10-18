"""Orchestrator for coordinating multiple agents in the recruitment process."""

from typing import Dict, Any, Optional, List
from agents import RecruiterAgent, SourcingAgent, ScreeningAgent, AgentResponse
from configs.llm_config import LLMConfig, get_llm_config
from tools.resume_parser import ResumeParser, ParsedResume


class RecruitmentOrchestrator:
    """
    Orchestrates the entire recruitment workflow by coordinating multiple agents.
    
    This class manages the flow between sourcing, screening, and recruitment
    activities, ensuring efficient and coordinated candidate processing.
    """
    
    def __init__(self, llm_config: Optional[LLMConfig] = None):
        """
        Initialize the recruitment orchestrator.
        
        Args:
            llm_config: LLM configuration (uses default if not provided)
        """
        self.llm_config = llm_config or get_llm_config()
        
        # Initialize agents
        self.recruiter_agent = RecruiterAgent(self.llm_config)
        self.sourcing_agent = SourcingAgent(self.llm_config)
        self.screening_agent = ScreeningAgent(self.llm_config)
        
        # Initialize tools
        self.resume_parser = ResumeParser()
    
    def create_job_and_source(
        self,
        job_description: str,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create job requirements and generate sourcing strategies.
        
        Args:
            job_description: Raw job description
            location: Location filter
            
        Returns:
            Dictionary with job requirements and sourcing recommendations
        """
        # Step 1: Extract job requirements
        job_response = self.recruiter_agent.process(
            action="create_job_requirements",
            job_description=job_description
        )
        
        if not job_response.success:
            return {
                "success": False,
                "error": job_response.error,
                "message": "Failed to create job requirements"
            }
        
        # Step 2: Generate sourcing strategies
        sourcing_response = self.sourcing_agent.process(
            action="generate_search_query",
            job_requirements=job_response.data,
            location=location
        )
        
        # Step 3: Recommend sourcing channels
        channels_response = self.sourcing_agent.process(
            action="recommend_sources",
            skills=job_response.data.get("skills", [])
        )
        
        return {
            "success": True,
            "job_requirements": job_response.data,
            "sourcing_queries": sourcing_response.data if sourcing_response.success else None,
            "sourcing_channels": channels_response.data if channels_response.success else None
        }
    
    def screen_candidate(
        self,
        resume_file_path: str,
        job_requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Screen a candidate through resume parsing and evaluation.
        
        Args:
            resume_file_path: Path to resume file
            job_requirements: Job requirements for comparison
            
        Returns:
            Dictionary with screening results
        """
        # Step 1: Parse resume
        try:
            parsed_resume = self.resume_parser.parse_file(resume_file_path)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to parse resume"
            }
        
        # Step 2: Evaluate fit
        evaluation_response = self.screening_agent.process(
            action="evaluate_fit",
            resume=parsed_resume,
            job_requirements=job_requirements
        )
        
        # Step 3: Calculate score
        score_response = self.screening_agent.process(
            action="calculate_score",
            resume=parsed_resume,
            job_requirements=job_requirements
        )
        
        # Step 4: Generate interview questions
        questions_response = self.screening_agent.process(
            action="generate_questions",
            resume=parsed_resume,
            job_requirements=job_requirements
        )
        
        return {
            "success": True,
            "candidate": {
                "name": parsed_resume.name,
                "email": parsed_resume.email,
                "phone": parsed_resume.phone,
                "skills": parsed_resume.skills
            },
            "evaluation": evaluation_response.data if evaluation_response.success else None,
            "score": score_response.data if score_response.success else None,
            "interview_questions": questions_response.data if questions_response.success else None
        }
    
    def full_recruitment_cycle(
        self,
        job_description: str,
        resume_files: List[str],
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a complete recruitment cycle from job creation to candidate screening.
        
        Args:
            job_description: Job description
            resume_files: List of resume file paths
            location: Location filter
            
        Returns:
            Dictionary with complete recruitment cycle results
        """
        # Step 1: Create job and sourcing strategy
        job_result = self.create_job_and_source(job_description, location)
        
        if not job_result["success"]:
            return job_result
        
        # Step 2: Screen all candidates
        candidate_results = []
        for resume_file in resume_files:
            result = self.screen_candidate(
                resume_file,
                job_result.get("job_requirements")
            )
            if result["success"]:
                candidate_results.append(result)
        
        # Step 3: Rank candidates by score
        ranked_candidates = sorted(
            candidate_results,
            key=lambda x: x.get("score", {}).get("overall_score", 0),
            reverse=True
        )
        
        return {
            "success": True,
            "job_requirements": job_result["job_requirements"],
            "sourcing_strategy": {
                "queries": job_result.get("sourcing_queries"),
                "channels": job_result.get("sourcing_channels")
            },
            "candidates_screened": len(candidate_results),
            "ranked_candidates": ranked_candidates
        }
    
    def generate_market_insights(
        self,
        skills: List[str],
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate market insights for recruitment planning.
        
        Args:
            skills: Required skills
            location: Location
            
        Returns:
            Dictionary with market insights
        """
        market_response = self.sourcing_agent.process(
            action="analyze_market",
            skills=skills,
            location=location
        )
        
        return {
            "success": market_response.success,
            "insights": market_response.data if market_response.success else None,
            "error": market_response.error
        }
