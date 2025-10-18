"""Main application entry point for AI Recruiter Copilot."""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel
import os
import tempfile

from workflows.orchestrator import RecruitmentOrchestrator
from configs import get_llm_config, get_app_config

# Initialize FastAPI app
app = FastAPI(
    title="AI Recruiter Copilot",
    description="AI-powered recruitment copilot with multi-LLM orchestration",
    version="1.0.0"
)

# Initialize orchestrator
orchestrator = RecruitmentOrchestrator()


class JobCreationRequest(BaseModel):
    """Request model for job creation."""
    job_description: str
    location: Optional[str] = None


class MarketInsightsRequest(BaseModel):
    """Request model for market insights."""
    skills: List[str]
    location: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Recruiter Copilot API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/jobs/create")
async def create_job(request: JobCreationRequest):
    """
    Create a job posting and generate sourcing strategies.
    
    Args:
        request: Job creation request with description and location
        
    Returns:
        Job requirements and sourcing strategies
    """
    try:
        result = orchestrator.create_job_and_source(
            job_description=request.job_description,
            location=request.location
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/candidates/screen")
async def screen_candidate(
    resume: UploadFile = File(...),
    job_requirements: Optional[str] = None
):
    """
    Screen a candidate by uploading their resume.
    
    Args:
        resume: Resume file (PDF, DOCX, or TXT)
        job_requirements: Optional job requirements JSON
        
    Returns:
        Screening results with evaluation and score
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=os.path.splitext(resume.filename)[1]
        ) as temp_file:
            content = await resume.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Parse job requirements if provided
        job_reqs = None
        if job_requirements:
            import json
            job_reqs = json.loads(job_requirements)
        
        # Screen the candidate
        result = orchestrator.screen_candidate(
            resume_file_path=temp_file_path,
            job_requirements=job_reqs
        )
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/market/insights")
async def get_market_insights(request: MarketInsightsRequest):
    """
    Get market insights for recruitment planning.
    
    Args:
        request: Market insights request with skills and location
        
    Returns:
        Market analysis and insights
    """
    try:
        result = orchestrator.generate_market_insights(
            skills=request.skills,
            location=request.location
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config")
async def get_configuration():
    """
    Get current configuration (without sensitive data).
    
    Returns:
        Configuration summary
    """
    llm_config = get_llm_config()
    app_config = get_app_config()
    
    return {
        "llm": {
            "provider": llm_config.default_provider,
            "model": llm_config.openai_model if llm_config.default_provider == "openai" else llm_config.anthropic_model,
            "temperature": llm_config.temperature,
            "max_tokens": llm_config.max_tokens
        },
        "app": {
            "env": app_config.app_env,
            "debug": app_config.debug
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    config = get_app_config()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.debug
    )
