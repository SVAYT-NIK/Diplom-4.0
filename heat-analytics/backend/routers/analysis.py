"""
Router for analysis endpoints.
"""
import logging
import uuid
from typing import List

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.services.db import async_session_maker
from backend.models.schemas import Building, DailyReading, AnalysisResult, AnalysisRequest
from backend.services.analytics_runner import run_analysis_pipeline


logger = logging.getLogger(__name__)

router = APIRouter()


async def get_db_session():
    """Get database session."""
    async with async_session_maker() as session:
        yield session


@router.post("/analyze")
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Start analysis pipeline for a building.
    
    Args:
        request: Analysis request with building_id and models to run
        background_tasks: FastAPI background tasks
        db: Database session
    
    Returns:
        Run ID for tracking analysis progress
    """
    # Verify building exists
    result = await db.execute(select(Building).where(Building.id == request.building_id))
    building = result.scalar_one_or_none()
    
    if not building:
        raise HTTPException(status_code=404, detail=f"Building with id {request.building_id} not found")
    
    # Verify building has data
    readings_result = await db.execute(
        select(DailyReading).where(DailyReading.building_id == request.building_id)
    )
    readings = readings_result.scalars().all()
    
    if not readings:
        raise HTTPException(status_code=400, detail="Building has no readings data")
    
    # Generate unique run ID
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    
    logger.info(f"Starting analysis run {run_id} for building {request.building_id}")
    logger.info(f"Models to run: {request.models}")
    
    # Run analysis in background
    background_tasks.add_task(
        run_analysis_pipeline,
        building_id=request.building_id,
        run_id=run_id,
        model_types=request.models,
        db_session_maker=async_session_maker,
    )
    
    return {
        "run_id": run_id,
        "building_id": request.building_id,
        "status": "started",
        "models": request.models,
        "message": "Analysis started in background"
    }


@router.get("/analysis/status/{run_id}")
async def get_analysis_status(run_id: str, db: AsyncSession = Depends(get_db_session)):
    """
    Get status of an analysis run.
    
    Args:
        run_id: Analysis run ID
        db: Database session
    
    Returns:
        Status information
    """
    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.run_id == run_id).limit(1)
    )
    analysis_record = result.scalar_one_or_none()
    
    if not analysis_record:
        # Check if run_id is valid format but results not ready yet
        if run_id.startswith("run_"):
            return {
                "run_id": run_id,
                "status": "processing",
                "message": "Analysis is still processing"
            }
        raise HTTPException(status_code=404, detail=f"Analysis run {run_id} not found")
    
    # Count total results for this run
    count_result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.run_id == run_id)
    )
    total_results = len(count_result.scalars().all())
    
    return {
        "run_id": run_id,
        "building_id": analysis_record.building_id,
        "status": "completed",
        "results_count": total_results,
        "created_at": analysis_record.created_at,
    }
