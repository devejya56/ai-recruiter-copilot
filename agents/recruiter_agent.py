"""Recruiter agent for managing the overall recruitment process."""

from typing import Dict, Any, Optional
from .base_agent import BaseAgent, AgentResponse
from configs.llm_config import LLMConfig


class RecruiterAgent(BaseAgent):
    """
    Main recruiter agent that orchestrates the recruitment process.
    
    Responsibilities:
    - Create and manage job postings
    - Coordinate with sourcing and screening agents
    - Track recruitment pipeline
    - Generate recruitment insights
    """
    
    def __init__(self, llm_config: LLMConfig):
        """
        Initialize the recruiter agent.
        
        Args:
            llm_config: LLM configuration
        """
        super().__init__(llm_config)
    
    @property
    def name(self) -> str:
        """Get the agent name."""
        return "RecruiterAgent"
    
    @property
    def description(self) -> str:
        """Get the agent description."""
        return "Main recruiter agent that orchestrates the recruitment process"
    
    def process(
        self,
        action: str,
        job_description: Optional[str] = None,
        candidate_id: Optional[str] = None,
        **kwargs
    ) -> AgentResponse:
        """
        Process a recruitment request.
        
        Args:
            action: Action to perform (create_job, analyze_pipeline, etc.)
            job_description: Job description for job creation
            candidate_id: Candidate ID for candidate-specific actions
            **kwargs: Additional parameters
            
        Returns:
            AgentResponse with results
        """
        try:
            if action == "create_job_requirements":
                return self._create_job_requirements(job_description)
            elif action == "analyze_pipeline":
                return self._analyze_pipeline()
            elif action == "generate_outreach":
                return self._generate_outreach(candidate_id)
            else:
                return AgentResponse(
                    success=False,
                    message=f"Unknown action: {action}",
                    error="Invalid action"
                )
        except Exception as e:
            return AgentResponse(
                success=False,
                message="Failed to process request",
                error=str(e)
            )
    
    def _create_job_requirements(self, job_description: Optional[str]) -> AgentResponse:
        """
        Create structured job requirements from a job description.
        
        Args:
            job_description: Raw job description
            
        Returns:
            AgentResponse with structured requirements
        """
        if not job_description:
            return AgentResponse(
                success=False,
                message="Job description is required",
                error="Missing job description"
            )
        
        prompt = f"""
        Analyze the following job description and extract structured requirements:
        
        Job Description:
        {job_description}
        
        Please provide:
        1. Key technical skills required
        2. Years of experience needed
        3. Education requirements
        4. Nice-to-have skills
        5. Key responsibilities
        
        Format your response as a structured list.
        """
        
        try:
            response = self._call_llm(prompt)
            
            return AgentResponse(
                success=True,
                message="Successfully extracted job requirements",
                data={
                    "requirements": response,
                    "original_description": job_description
                }
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                message="Failed to extract requirements",
                error=str(e)
            )
    
    def _analyze_pipeline(self) -> AgentResponse:
        """
        Analyze the current recruitment pipeline.
        
        Returns:
            AgentResponse with pipeline analysis
        """
        # This would integrate with database to get actual pipeline data
        # For now, return a mock response
        
        return AgentResponse(
            success=True,
            message="Pipeline analysis complete",
            data={
                "total_candidates": 0,
                "by_stage": {
                    "sourcing": 0,
                    "screening": 0,
                    "interview": 0,
                    "offer": 0
                },
                "insights": "No candidates in pipeline yet"
            }
        )
    
    def _generate_outreach(self, candidate_id: Optional[str]) -> AgentResponse:
        """
        Generate personalized outreach message for a candidate.
        
        Args:
            candidate_id: Candidate identifier
            
        Returns:
            AgentResponse with outreach message
        """
        if not candidate_id:
            return AgentResponse(
                success=False,
                message="Candidate ID is required",
                error="Missing candidate ID"
            )
        
        # This would fetch candidate data from database
        # For now, generate a generic template
        
        prompt = """
        Generate a professional and personalized outreach message for a candidate.
        
        The message should:
        1. Be warm and engaging
        2. Highlight the opportunity
        3. Express genuine interest in their background
        4. Include a clear call to action
        
        Keep it under 200 words.
        """
        
        try:
            response = self._call_llm(prompt)
            
            return AgentResponse(
                success=True,
                message="Outreach message generated",
                data={
                    "candidate_id": candidate_id,
                    "message": response
                }
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                message="Failed to generate outreach",
                error=str(e)
            )
