"""Recruitment Flow Orchestrator
This module defines the end-to-end recruitment workflow, from resume parsing
to candidate scoring and email notification.
"""
import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlowStage(str, Enum):
    """Stages in the recruitment flow."""
    INTAKE = "intake"
    PARSE = "parse"
    ENRICH = "enrich"
    ANALYZE = "analyze"
    SCORE = "score"
    REVIEW = "review"
    NOTIFY = "notify"
    COMPLETE = "complete"

class FlowStatus(str, Enum):
    """Status of a flow execution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    SUCCESS = "success"
    FAILED = "failed"

@dataclass
class FlowContext:
    """Context object passed through the workflow."""
    flow_id: str
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None
    resume_path: Optional[str] = None
    parsed_resume: Optional[Dict] = None
    enriched_data: Optional[Dict] = None
    analysis: Optional[Dict] = None
    score: Optional[float] = None
    stage: FlowStage = FlowStage.INTAKE
    status: FlowStatus = FlowStatus.PENDING
    errors: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}

class RecruitmentFlow:
    """Orchestrate the end-to-end recruitment process."""
    
    def __init__(self, pdf_parser, enricher, analyzer, scorer, notifier):
        """
        Initialize the recruitment flow with required components.
        
        Args:
            pdf_parser: PDF parsing component
            enricher: Data enrichment component
            analyzer: Resume analysis component
            scorer: Candidate scoring component
            notifier: Notification component
        """
        self.pdf_parser = pdf_parser
        self.enricher = enricher
        self.analyzer = analyzer
        self.scorer = scorer
        self.notifier = notifier
        self.active_flows: Dict[str, FlowContext] = {}
    
    def start_flow(self, flow_id: str, resume_path: str, job_id: str) -> FlowContext:
        """
        Start a new recruitment flow.
        
        Args:
            flow_id: Unique identifier for this flow
            resume_path: Path to resume file
            job_id: Job posting identifier
            
        Returns:
            FlowContext object
        """
        logger.info(f"Starting flow {flow_id} for job {job_id}")
        
        context = FlowContext(
            flow_id=flow_id,
            job_id=job_id,
            resume_path=resume_path,
            status=FlowStatus.IN_PROGRESS
        )
        
        self.active_flows[flow_id] = context
        return context
    
    def execute_flow(self, context: FlowContext) -> FlowContext:
        """
        Execute all stages of the recruitment flow.
        
        Args:
            context: FlowContext object
            
        Returns:
            Updated FlowContext object
        """
        try:
            # Stage 1: Parse resume
            context = self._parse_resume(context)
            if context.status == FlowStatus.FAILED:
                return context
            
            # Stage 2: Enrich candidate data
            context = self._enrich_data(context)
            if context.status == FlowStatus.FAILED:
                return context
            
            # Stage 3: Analyze resume
            context = self._analyze_resume(context)
            if context.status == FlowStatus.FAILED:
                return context
            
            # Stage 4: Score candidate
            context = self._score_candidate(context)
            if context.status == FlowStatus.FAILED:
                return context
            
            # Stage 5: Review (approval gate check)
            context = self._review_candidate(context)
            if context.status == FlowStatus.PAUSED:
                logger.info(f"Flow {context.flow_id} paused for review")
                return context
            
            # Stage 6: Notify stakeholders
            context = self._notify_stakeholders(context)
            
            # Mark as complete
            context.stage = FlowStage.COMPLETE
            context.status = FlowStatus.SUCCESS
            logger.info(f"Flow {context.flow_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Flow {context.flow_id} failed: {e}")
            context.status = FlowStatus.FAILED
            context.errors.append(str(e))
        
        return context
    
    def _parse_resume(self, context: FlowContext) -> FlowContext:
        """Parse resume PDF."""
        logger.info(f"Flow {context.flow_id}: Parsing resume")
        context.stage = FlowStage.PARSE
        
        try:
            parsed = self.pdf_parser.parse_pdf(context.resume_path)
            if "error" in parsed:
                raise Exception(parsed["error"])
            
            context.parsed_resume = parsed
            context.candidate_id = self._extract_candidate_id(parsed)
            
        except Exception as e:
            logger.error(f"Parse failed: {e}")
            context.status = FlowStatus.FAILED
            context.errors.append(f"Parse error: {e}")
        
        return context
    
    def _enrich_data(self, context: FlowContext) -> FlowContext:
        """Enrich candidate data from external sources."""
        logger.info(f"Flow {context.flow_id}: Enriching data")
        context.stage = FlowStage.ENRICH
        
        try:
            linkedin_url = context.parsed_resume.get("contact_info", {}).get("linkedin")
            if linkedin_url:
                enriched = self.enricher.enrich(linkedin_url)
                context.enriched_data = enriched
            else:
                logger.warning("No LinkedIn URL found, skipping enrichment")
                context.enriched_data = {}
        
        except Exception as e:
            logger.error(f"Enrichment failed: {e}")
            # Non-critical, continue flow
            context.enriched_data = {}
        
        return context
    
    def _analyze_resume(self, context: FlowContext) -> FlowContext:
        """Analyze resume content."""
        logger.info(f"Flow {context.flow_id}: Analyzing resume")
        context.stage = FlowStage.ANALYZE
        
        try:
            analysis = self.analyzer.analyze(
                resume_data=context.parsed_resume,
                job_id=context.job_id
            )
            context.analysis = analysis
        
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            context.status = FlowStatus.FAILED
            context.errors.append(f"Analysis error: {e}")
        
        return context
    
    def _score_candidate(self, context: FlowContext) -> FlowContext:
        """Score candidate based on analysis."""
        logger.info(f"Flow {context.flow_id}: Scoring candidate")
        context.stage = FlowStage.SCORE
        
        try:
            score = self.scorer.score(
                analysis=context.analysis,
                enriched_data=context.enriched_data,
                job_id=context.job_id
            )
            context.score = score
        
        except Exception as e:
            logger.error(f"Scoring failed: {e}")
            context.status = FlowStatus.FAILED
            context.errors.append(f"Scoring error: {e}")
        
        return context
    
    def _review_candidate(self, context: FlowContext) -> FlowContext:
        """Check if manual review is required."""
        logger.info(f"Flow {context.flow_id}: Reviewing candidate")
        context.stage = FlowStage.REVIEW
        
        # Check score threshold
        REVIEW_THRESHOLD = 0.7
        if context.score and context.score >= REVIEW_THRESHOLD:
            logger.info(f"Candidate passed automatic review (score: {context.score})")
        else:
            logger.info(f"Candidate requires manual review (score: {context.score})")
            context.status = FlowStatus.PAUSED
        
        return context
    
    def _notify_stakeholders(self, context: FlowContext) -> FlowContext:
        """Send notifications to relevant stakeholders."""
        logger.info(f"Flow {context.flow_id}: Sending notifications")
        context.stage = FlowStage.NOTIFY
        
        try:
            notification_data = {
                "candidate_id": context.candidate_id,
                "job_id": context.job_id,
                "score": context.score,
                "summary": context.analysis.get("summary", "No summary available")
            }
            
            self.notifier.notify(notification_data)
        
        except Exception as e:
            logger.error(f"Notification failed: {e}")
            # Non-critical, don't fail the flow
        
        return context
    
    def _extract_candidate_id(self, parsed_resume: Dict) -> str:
        """Extract or generate candidate ID."""
        email = parsed_resume.get("contact_info", {}).get("email")
        if email:
            return email.split("@")[0]
        return f"candidate_{datetime.now().timestamp()}"
    
    def get_flow_status(self, flow_id: str) -> Optional[FlowContext]:
        """Get status of a flow."""
        return self.active_flows.get(flow_id)
    
    def resume_flow(self, flow_id: str, approved: bool) -> FlowContext:
        """Resume a paused flow after review."""
        context = self.active_flows.get(flow_id)
        if not context:
            raise ValueError(f"Flow {flow_id} not found")
        
        if context.status != FlowStatus.PAUSED:
            raise ValueError(f"Flow {flow_id} is not paused")
        
        if not approved:
            context.status = FlowStatus.FAILED
            context.errors.append("Rejected during manual review")
            return context
        
        context.status = FlowStatus.IN_PROGRESS
        
        # Continue from notify stage
        context = self._notify_stakeholders(context)
        context.stage = FlowStage.COMPLETE
        context.status = FlowStatus.SUCCESS
        
        return context

def main_workflow(flow_id: str = "main-001", resume_path: str = "resume.pdf", job_id: str = "job-123") -> FlowContext:
    """
    Main workflow function that creates mock components and runs the recruitment flow.
    This function is importable for use in main.py.
    
    Args:
        flow_id: Unique identifier for this flow
        resume_path: Path to resume file
        job_id: Job posting identifier
        
    Returns:
        Final FlowContext object
    """
    # Mock components
    class MockParser:
        def parse_pdf(self, path):
            return {"contact_info": {"email": "test@example.com"}}
    
    class MockEnricher:
        def enrich(self, url):
            return {"years_experience": 5}
    
    class MockAnalyzer:
        def analyze(self, resume_data, job_id):
            return {"summary": "Strong candidate"}
    
    class MockScorer:
        def score(self, analysis, enriched_data, job_id):
            return 0.85
    
    class MockNotifier:
        def notify(self, data):
            print(f"Notification: {data}")
    
    # Create RecruitmentFlow instance
    flow = RecruitmentFlow(
        MockParser(), MockEnricher(), MockAnalyzer(),
        MockScorer(), MockNotifier()
    )
    
    # Run the flow
    ctx = flow.start_flow(flow_id, resume_path, job_id)
    ctx = flow.execute_flow(ctx)
    
    return ctx

if __name__ == "__main__":
    # Mock components for testing
    class MockParser:
        def parse_pdf(self, path):
            return {"contact_info": {"email": "test@example.com"}}
    
    class MockEnricher:
        def enrich(self, url):
            return {"years_experience": 5}
    
    class MockAnalyzer:
        def analyze(self, resume_data, job_id):
            return {"summary": "Strong candidate"}
    
    class MockScorer:
        def score(self, analysis, enriched_data, job_id):
            return 0.85
    
    class MockNotifier:
        def notify(self, data):
            print(f"Notification: {data}")
    
    # Test flow
    flow = RecruitmentFlow(
        MockParser(), MockEnricher(), MockAnalyzer(),
        MockScorer(), MockNotifier()
    )
    
    ctx = flow.start_flow("test-001", "resume.pdf", "job-123")
    ctx = flow.execute_flow(ctx)
    print(f"Flow status: {ctx.status}, Score: {ctx.score}")
