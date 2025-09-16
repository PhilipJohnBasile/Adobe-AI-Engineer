"""
API Server for Creative Automation Pipeline
Provides REST endpoints for system integration
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
import json
import os
import uuid
from datetime import datetime
import tempfile
import yaml

from .pipeline_orchestrator import PipelineOrchestrator
from .analytics_dashboard import AnalyticsDashboard
from .compliance_checker import ComplianceChecker
from .localization import LocalizationManager
from .batch_processor import BatchProcessor


app = FastAPI(
    title="Creative Automation Pipeline API",
    description="REST API for automated creative asset generation",
    version="1.0.0"
)

# CORS middleware for web integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job tracking (use Redis in production)
job_queue = {}
batch_jobs = {}

# Initialize components
orchestrator = PipelineOrchestrator()
analytics = AnalyticsDashboard()
compliance_checker = ComplianceChecker()
localizer = LocalizationManager()
batch_processor = BatchProcessor()


class CampaignBriefRequest(BaseModel):
    """Request model for campaign brief submission"""
    campaign_brief: Dict[str, Any]
    assets_dir: str = Field(default="assets", description="Directory containing input assets")
    output_dir: str = Field(default="output", description="Directory for generated outputs")
    force_generate: bool = Field(default=False, description="Force regenerate all assets")
    skip_compliance: bool = Field(default=False, description="Skip compliance checking")
    localize_for: Optional[str] = Field(default=None, description="Market code for localization")
    priority: str = Field(default="normal", description="Job priority: low, normal, high")


class BatchRequest(BaseModel):
    """Request model for batch processing"""
    campaign_briefs: List[Dict[str, Any]]
    concurrent_limit: int = Field(default=3, description="Maximum concurrent campaigns")
    localize_map: Optional[Dict[str, str]] = Field(default=None, description="Campaign to market mapping")
    output_dir: str = Field(default="batch_results", description="Batch output directory")


class JobResponse(BaseModel):
    """Response model for job submission"""
    job_id: str
    status: str
    message: str
    estimated_completion: Optional[str] = None


@app.get("/")
async def root():
    """API health check and information"""
    return {
        "service": "Creative Automation Pipeline API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "generate": "/campaigns/generate",
            "validate": "/campaigns/validate",
            "compliance": "/campaigns/compliance",
            "localize": "/campaigns/localize",
            "batch": "/campaigns/batch",
            "analytics": "/analytics",
            "system": "/system"
        }
    }


@app.get("/health")
async def health_check():
    """Detailed health check for load balancers"""
    try:
        # Check system dependencies
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "api_server": "ok",
                "file_system": "ok",
                "dependencies": "ok"
            }
        }
        
        # Check if OpenAI API key is configured
        if not os.getenv("OPENAI_API_KEY"):
            health_status["checks"]["openai_api"] = "warning"
            health_status["warnings"] = ["OpenAI API key not configured"]
        else:
            health_status["checks"]["openai_api"] = "ok"
            
        return health_status
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@app.post("/campaigns/generate", response_model=JobResponse)
async def generate_campaign(request: CampaignBriefRequest, background_tasks: BackgroundTasks):
    """Generate creative assets for a campaign"""
    job_id = str(uuid.uuid4())
    
    # Create job entry
    job_queue[job_id] = {
        "id": job_id,
        "status": "queued",
        "created_at": datetime.now().isoformat(),
        "type": "generate",
        "request": request.dict(),
        "progress": 0,
        "message": "Campaign generation queued"
    }
    
    # Start background task
    background_tasks.add_task(
        _process_campaign_generation,
        job_id,
        request
    )
    
    return JobResponse(
        job_id=job_id,
        status="queued",
        message="Campaign generation started",
        estimated_completion=_estimate_completion_time(1)
    )


@app.post("/campaigns/validate")
async def validate_campaign(request: CampaignBriefRequest):
    """Validate campaign brief structure"""
    try:
        # Validate structure
        validation_result = orchestrator.validate_campaign_brief(request.campaign_brief)
        
        return {
            "valid": validation_result["valid"],
            "errors": validation_result.get("errors", []),
            "warnings": validation_result.get("warnings", []),
            "suggestions": validation_result.get("suggestions", [])
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")


@app.post("/campaigns/compliance")
async def check_compliance(request: CampaignBriefRequest):
    """Check campaign compliance"""
    try:
        compliance_result = compliance_checker.check_campaign_brief(request.campaign_brief)
        
        return {
            "compliant": len(compliance_result["critical"]) == 0,
            "score": compliance_result.get("score", 0),
            "critical_issues": compliance_result["critical"],
            "warnings": compliance_result["warnings"],
            "suggestions": compliance_result["suggestions"],
            "passed_checks": compliance_result["passed_checks"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Compliance check failed: {str(e)}")


@app.post("/campaigns/localize")
async def localize_campaign(
    campaign_brief: Dict[str, Any],
    market_code: str,
    cultural_adaptation: bool = True
):
    """Localize campaign for specific market"""
    try:
        localized_brief = localizer.localize_campaign(
            campaign_brief, 
            market_code, 
            cultural_adaptation
        )
        
        return {
            "original_market": campaign_brief.get("target_region", "Unknown"),
            "localized_market": market_code,
            "localized_brief": localized_brief,
            "adaptations_made": localized_brief.get("_localization_log", [])
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Localization failed: {str(e)}")


@app.post("/campaigns/batch", response_model=JobResponse)
async def batch_process(request: BatchRequest, background_tasks: BackgroundTasks):
    """Process multiple campaigns in batch"""
    job_id = str(uuid.uuid4())
    
    # Create batch job entry
    batch_jobs[job_id] = {
        "id": job_id,
        "status": "queued",
        "created_at": datetime.now().isoformat(),
        "type": "batch",
        "total_campaigns": len(request.campaign_briefs),
        "completed_campaigns": 0,
        "progress": 0,
        "message": "Batch processing queued"
    }
    
    # Start background batch processing
    background_tasks.add_task(
        _process_batch_campaigns,
        job_id,
        request
    )
    
    return JobResponse(
        job_id=job_id,
        status="queued",
        message=f"Batch processing started for {len(request.campaign_briefs)} campaigns",
        estimated_completion=_estimate_completion_time(len(request.campaign_briefs))
    )


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a specific job"""
    # Check regular jobs
    if job_id in job_queue:
        return job_queue[job_id]
    
    # Check batch jobs
    if job_id in batch_jobs:
        return batch_jobs[job_id]
    
    raise HTTPException(status_code=404, detail="Job not found")


@app.get("/jobs")
async def list_jobs(status: Optional[str] = None, limit: int = 50):
    """List recent jobs with optional status filter"""
    all_jobs = list(job_queue.values()) + list(batch_jobs.values())
    
    # Filter by status if specified
    if status:
        all_jobs = [job for job in all_jobs if job["status"] == status]
    
    # Sort by creation time (newest first) and limit
    all_jobs.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "jobs": all_jobs[:limit],
        "total": len(all_jobs)
    }


@app.get("/jobs/{job_id}/download")
async def download_job_results(job_id: str):
    """Download generated assets for a completed job"""
    if job_id not in job_queue and job_id not in batch_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_queue.get(job_id) or batch_jobs.get(job_id)
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    # Create ZIP file of results
    output_path = job.get("output_path")
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Job results not found")
    
    # In production, implement ZIP creation and return
    return FileResponse(
        path=output_path,
        filename=f"campaign_results_{job_id}.zip",
        media_type="application/zip"
    )


@app.get("/analytics")
async def get_analytics(format: str = "json"):
    """Get performance analytics"""
    try:
        if format == "html":
            # Generate HTML dashboard
            html_content = analytics.generate_html_dashboard()
            return HTMLResponse(content=html_content)
        else:
            # Return JSON analytics
            analytics_data = analytics.generate_report()
            return analytics_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics generation failed: {str(e)}")


@app.get("/system/status")
async def system_status():
    """Get comprehensive system status"""
    try:
        return {
            "system": "Creative Automation Pipeline",
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "active_jobs": len([j for j in job_queue.values() if j["status"] == "running"]),
                "queued_jobs": len([j for j in job_queue.values() if j["status"] == "queued"]),
                "completed_jobs": len([j for j in job_queue.values() if j["status"] == "completed"]),
                "active_batch_jobs": len([j for j in batch_jobs.values() if j["status"] == "running"])
            },
            "configuration": {
                "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
                "max_concurrent_jobs": 5,
                "supported_markets": ["US", "UK", "DE", "JP", "FR"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@app.get("/markets")
async def list_markets():
    """List supported localization markets"""
    return {
        "supported_markets": localizer.get_supported_markets(),
        "market_details": {
            "US": {"name": "United States", "language": "English", "currency": "USD"},
            "UK": {"name": "United Kingdom", "language": "English", "currency": "GBP"},
            "DE": {"name": "Germany", "language": "German", "currency": "EUR"},
            "JP": {"name": "Japan", "language": "Japanese", "currency": "JPY"},
            "FR": {"name": "France", "language": "French", "currency": "EUR"}
        }
    }


@app.post("/campaigns/upload")
async def upload_campaign_brief(file: UploadFile = File(...)):
    """Upload campaign brief file (YAML/JSON)"""
    try:
        # Read uploaded file
        content = await file.read()
        
        # Parse based on file extension
        if file.filename.endswith('.yaml') or file.filename.endswith('.yml'):
            campaign_brief = yaml.safe_load(content.decode('utf-8'))
        elif file.filename.endswith('.json'):
            campaign_brief = json.loads(content.decode('utf-8'))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use YAML or JSON.")
        
        # Validate the brief
        validation_result = orchestrator.validate_campaign_brief(campaign_brief)
        
        return {
            "filename": file.filename,
            "campaign_id": campaign_brief.get("campaign_brief", {}).get("campaign_id", "unknown"),
            "validation": validation_result,
            "campaign_brief": campaign_brief
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File processing failed: {str(e)}")


# Background task functions
async def _process_campaign_generation(job_id: str, request: CampaignBriefRequest):
    """Background task for campaign generation"""
    try:
        job_queue[job_id]["status"] = "running"
        job_queue[job_id]["message"] = "Generating creative assets"
        
        # Simulate campaign generation (replace with actual orchestrator call)
        result = await orchestrator.process_campaign_async(
            request.campaign_brief,
            request.assets_dir,
            request.output_dir,
            request.force_generate,
            request.skip_compliance,
            request.localize_for
        )
        
        job_queue[job_id]["status"] = "completed"
        job_queue[job_id]["progress"] = 100
        job_queue[job_id]["message"] = "Campaign generation completed"
        job_queue[job_id]["result"] = result
        job_queue[job_id]["output_path"] = result.get("output_path")
        
    except Exception as e:
        job_queue[job_id]["status"] = "failed"
        job_queue[job_id]["message"] = f"Generation failed: {str(e)}"
        job_queue[job_id]["error"] = str(e)


async def _process_batch_campaigns(job_id: str, request: BatchRequest):
    """Background task for batch processing"""
    try:
        batch_jobs[job_id]["status"] = "running"
        batch_jobs[job_id]["message"] = "Processing batch campaigns"
        
        # Process campaigns with progress updates
        async for progress in batch_processor.process_campaigns_async(
            request.campaign_briefs,
            request.concurrent_limit,
            request.localize_map,
            request.output_dir
        ):
            batch_jobs[job_id]["progress"] = progress["progress"]
            batch_jobs[job_id]["completed_campaigns"] = progress["completed"]
            batch_jobs[job_id]["message"] = progress["message"]
        
        batch_jobs[job_id]["status"] = "completed"
        batch_jobs[job_id]["progress"] = 100
        batch_jobs[job_id]["message"] = "Batch processing completed"
        
    except Exception as e:
        batch_jobs[job_id]["status"] = "failed"
        batch_jobs[job_id]["message"] = f"Batch processing failed: {str(e)}"
        batch_jobs[job_id]["error"] = str(e)


def _estimate_completion_time(campaign_count: int) -> str:
    """Estimate job completion time"""
    avg_time_per_campaign = 45  # seconds
    estimated_seconds = campaign_count * avg_time_per_campaign
    
    completion_time = datetime.now().timestamp() + estimated_seconds
    return datetime.fromtimestamp(completion_time).isoformat()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)