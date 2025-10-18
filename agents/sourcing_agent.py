"""Sourcing agent for finding and attracting candidates."""

from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent, AgentResponse
from configs.llm_config import LLMConfig


class SourcingAgent(BaseAgent):
    """
    Sourcing agent for candidate discovery and attraction.
    
    Responsibilities:
    - Generate search queries for candidate sourcing
    - Identify candidate sources (job boards, LinkedIn, etc.)
    - Optimize search strategies
    - Analyze market availability
    """
    
    def __init__(self, llm_config: LLMConfig):
        """
        Initialize the sourcing agent.
        
        Args:
            llm_config: LLM configuration
        """
        super().__init__(llm_config)
    
    @property
    def name(self) -> str:
        """Get the agent name."""
        return "SourcingAgent"
    
    @property
    def description(self) -> str:
        """Get the agent description."""
        return "Agent specialized in candidate sourcing and discovery"
    
    def process(
        self,
        action: str,
        job_requirements: Optional[Dict[str, Any]] = None,
        skills: Optional[List[str]] = None,
        location: Optional[str] = None,
        **kwargs
    ) -> AgentResponse:
        """
        Process a sourcing request.
        
        Args:
            action: Action to perform
            job_requirements: Job requirements for sourcing
            skills: List of skills to search for
            location: Location filter
            **kwargs: Additional parameters
            
        Returns:
            AgentResponse with results
        """
        try:
            if action == "generate_search_query":
                return self._generate_search_query(job_requirements, skills, location)
            elif action == "recommend_sources":
                return self._recommend_sources(skills)
            elif action == "analyze_market":
                return self._analyze_market(skills, location)
            else:
                return AgentResponse(
                    success=False,
                    message=f"Unknown action: {action}",
                    error="Invalid action"
                )
        except Exception as e:
            return AgentResponse(
                success=False,
                message="Failed to process sourcing request",
                error=str(e)
            )
    
    def _generate_search_query(
        self,
        job_requirements: Optional[Dict[str, Any]],
        skills: Optional[List[str]],
        location: Optional[str]
    ) -> AgentResponse:
        """
        Generate optimized search queries for candidate sourcing.
        
        Args:
            job_requirements: Job requirements
            skills: Required skills
            location: Location filter
            
        Returns:
            AgentResponse with search queries
        """
        prompt = f"""
        Generate effective Boolean search queries for finding candidates with the following criteria:
        
        Job Requirements: {job_requirements or 'Not specified'}
        Skills: {', '.join(skills) if skills else 'Not specified'}
        Location: {location or 'Any'}
        
        Provide:
        1. A LinkedIn search query
        2. A GitHub search query (for technical roles)
        3. A general job board search query
        4. Alternative search terms and synonyms
        
        Make the queries specific and effective for finding qualified candidates.
        """
        
        try:
            response = self._call_llm(prompt)
            
            return AgentResponse(
                success=True,
                message="Search queries generated successfully",
                data={
                    "queries": response,
                    "skills": skills,
                    "location": location
                }
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                message="Failed to generate search queries",
                error=str(e)
            )
    
    def _recommend_sources(self, skills: Optional[List[str]]) -> AgentResponse:
        """
        Recommend best sourcing channels based on skills.
        
        Args:
            skills: Required skills
            
        Returns:
            AgentResponse with recommended sources
        """
        prompt = f"""
        Recommend the best sourcing channels and platforms for finding candidates with these skills:
        
        Skills: {', '.join(skills) if skills else 'General'}
        
        Consider:
        1. Job boards (Indeed, LinkedIn, etc.)
        2. Professional networks
        3. Community forums and groups
        4. Universities and bootcamps (for junior roles)
        5. Conferences and events
        
        Provide specific recommendations with rationale.
        """
        
        try:
            response = self._call_llm(prompt)
            
            return AgentResponse(
                success=True,
                message="Source recommendations generated",
                data={
                    "recommendations": response,
                    "skills": skills
                }
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                message="Failed to recommend sources",
                error=str(e)
            )
    
    def _analyze_market(
        self,
        skills: Optional[List[str]],
        location: Optional[str]
    ) -> AgentResponse:
        """
        Analyze market availability for candidates.
        
        Args:
            skills: Required skills
            location: Location
            
        Returns:
            AgentResponse with market analysis
        """
        prompt = f"""
        Provide a market analysis for candidates with these characteristics:
        
        Skills: {', '.join(skills) if skills else 'General'}
        Location: {location or 'Any'}
        
        Analyze:
        1. Supply and demand dynamics
        2. Typical salary ranges
        3. Competition for these candidates
        4. Best recruitment strategies for this market
        5. Timeline expectations
        
        Provide realistic insights based on current market conditions.
        """
        
        try:
            response = self._call_llm(prompt)
            
            return AgentResponse(
                success=True,
                message="Market analysis complete",
                data={
                    "analysis": response,
                    "skills": skills,
                    "location": location
                }
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                message="Failed to analyze market",
                error=str(e)
            )
