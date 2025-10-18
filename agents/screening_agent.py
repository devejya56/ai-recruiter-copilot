"""Screening agent for evaluating and filtering candidates."""

from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent, AgentResponse
from configs.llm_config import LLMConfig
from tools.resume_parser import ParsedResume


class ScreeningAgent(BaseAgent):
    """
    Screening agent for candidate evaluation.
    
    Responsibilities:
    - Evaluate candidate fit based on job requirements
    - Score candidates objectively
    - Generate interview questions
    - Identify red flags and strengths
    """
    
    def __init__(self, llm_config: LLMConfig):
        """
        Initialize the screening agent.
        
        Args:
            llm_config: LLM configuration
        """
        super().__init__(llm_config)
    
    @property
    def name(self) -> str:
        """Get the agent name."""
        return "ScreeningAgent"
    
    @property
    def description(self) -> str:
        """Get the agent description."""
        return "Agent specialized in candidate screening and evaluation"
    
    def process(
        self,
        action: str,
        resume: Optional[ParsedResume] = None,
        job_requirements: Optional[Dict[str, Any]] = None,
        candidate_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentResponse:
        """
        Process a screening request.
        
        Args:
            action: Action to perform
            resume: Parsed resume data
            job_requirements: Job requirements for comparison
            candidate_data: Additional candidate data
            **kwargs: Additional parameters
            
        Returns:
            AgentResponse with results
        """
        try:
            if action == "evaluate_fit":
                return self._evaluate_fit(resume, job_requirements)
            elif action == "generate_questions":
                return self._generate_questions(resume, job_requirements)
            elif action == "identify_strengths":
                return self._identify_strengths(resume)
            elif action == "calculate_score":
                return self._calculate_score(resume, job_requirements)
            else:
                return AgentResponse(
                    success=False,
                    message=f"Unknown action: {action}",
                    error="Invalid action"
                )
        except Exception as e:
            return AgentResponse(
                success=False,
                message="Failed to process screening request",
                error=str(e)
            )
    
    def _evaluate_fit(
        self,
        resume: Optional[ParsedResume],
        job_requirements: Optional[Dict[str, Any]]
    ) -> AgentResponse:
        """
        Evaluate candidate fit for a position.
        
        Args:
            resume: Parsed resume
            job_requirements: Job requirements
            
        Returns:
            AgentResponse with evaluation
        """
        if not resume:
            return AgentResponse(
                success=False,
                message="Resume is required for evaluation",
                error="Missing resume"
            )
        
        prompt = f"""
        Evaluate the following candidate's fit for a position:
        
        Candidate Profile:
        - Name: {resume.name or 'Not provided'}
        - Skills: {', '.join(resume.skills) if resume.skills else 'Not specified'}
        - Resume Text: {resume.raw_text[:1000]}...
        
        Job Requirements:
        {job_requirements or 'Not specified'}
        
        Provide:
        1. Overall fit score (0-100)
        2. Key strengths that match requirements
        3. Gaps or missing qualifications
        4. Recommendation (Strong Fit / Moderate Fit / Poor Fit)
        5. Detailed reasoning
        
        Be objective and fair in your evaluation.
        """
        
        try:
            response = self._call_llm(prompt)
            
            return AgentResponse(
                success=True,
                message="Candidate evaluation complete",
                data={
                    "evaluation": response,
                    "candidate_name": resume.name,
                    "skills": resume.skills
                }
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                message="Failed to evaluate candidate",
                error=str(e)
            )
    
    def _generate_questions(
        self,
        resume: Optional[ParsedResume],
        job_requirements: Optional[Dict[str, Any]]
    ) -> AgentResponse:
        """
        Generate tailored interview questions.
        
        Args:
            resume: Parsed resume
            job_requirements: Job requirements
            
        Returns:
            AgentResponse with interview questions
        """
        if not resume:
            return AgentResponse(
                success=False,
                message="Resume is required to generate questions",
                error="Missing resume"
            )
        
        prompt = f"""
        Generate 5-7 tailored interview questions for this candidate:
        
        Candidate Profile:
        - Skills: {', '.join(resume.skills) if resume.skills else 'Not specified'}
        - Background: {resume.raw_text[:500]}...
        
        Job Requirements:
        {job_requirements or 'General technical position'}
        
        Questions should:
        1. Probe technical competency
        2. Explore relevant experience
        3. Assess problem-solving ability
        4. Evaluate cultural fit
        5. Address any gaps or concerns
        
        Provide specific, thoughtful questions with rationale.
        """
        
        try:
            response = self._call_llm(prompt)
            
            return AgentResponse(
                success=True,
                message="Interview questions generated",
                data={
                    "questions": response,
                    "candidate_name": resume.name
                }
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                message="Failed to generate questions",
                error=str(e)
            )
    
    def _identify_strengths(self, resume: Optional[ParsedResume]) -> AgentResponse:
        """
        Identify candidate strengths and unique qualities.
        
        Args:
            resume: Parsed resume
            
        Returns:
            AgentResponse with identified strengths
        """
        if not resume:
            return AgentResponse(
                success=False,
                message="Resume is required",
                error="Missing resume"
            )
        
        prompt = f"""
        Analyze this candidate's resume and identify key strengths:
        
        Resume:
        {resume.raw_text}
        
        Identify:
        1. Technical strengths
        2. Unique experiences or achievements
        3. Leadership qualities
        4. Areas of expertise
        5. Growth trajectory
        
        Focus on specific, evidence-based strengths.
        """
        
        try:
            response = self._call_llm(prompt)
            
            return AgentResponse(
                success=True,
                message="Strengths identified",
                data={
                    "strengths": response,
                    "candidate_name": resume.name,
                    "skills": resume.skills
                }
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                message="Failed to identify strengths",
                error=str(e)
            )
    
    def _calculate_score(
        self,
        resume: Optional[ParsedResume],
        job_requirements: Optional[Dict[str, Any]]
    ) -> AgentResponse:
        """
        Calculate an objective fit score.
        
        Args:
            resume: Parsed resume
            job_requirements: Job requirements
            
        Returns:
            AgentResponse with score breakdown
        """
        if not resume:
            return AgentResponse(
                success=False,
                message="Resume is required for scoring",
                error="Missing resume"
            )
        
        # Simple scoring based on skill matching
        # In production, this would be more sophisticated
        required_skills = []
        if job_requirements and 'skills' in job_requirements:
            required_skills = job_requirements['skills']
        
        matched_skills = 0
        if required_skills and resume.skills:
            resume_skills_lower = [s.lower() for s in resume.skills]
            for req_skill in required_skills:
                if req_skill.lower() in resume_skills_lower:
                    matched_skills += 1
        
        total_required = len(required_skills) if required_skills else 1
        skill_score = (matched_skills / total_required) * 100 if total_required > 0 else 50
        
        return AgentResponse(
            success=True,
            message="Score calculated",
            data={
                "overall_score": round(skill_score, 2),
                "skill_match_score": round(skill_score, 2),
                "matched_skills": matched_skills,
                "total_required_skills": total_required,
                "candidate_name": resume.name
            }
        )
