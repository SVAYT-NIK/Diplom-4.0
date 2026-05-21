"""
Router for retrieving analysis results.
"""
import logging
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.services.db import async_session_maker
from backend.models.schemas import AnalysisResult, AnalysisResultResponse


logger = logging.getLogger(__name__)

router = APIRouter()


async def get_db_session():
    """Get database session."""
    async with async_session_maker() as session:
        yield session


@router.get("/results/{run_id}", response_model=List[AnalysisResultResponse])
async def get_results(run_id: str, db: AsyncSession = Depends(get_db_session)):
    """
    Get all analysis results for a specific run.
    
    Args:
        run_id: Analysis run ID
        db: Database session
    
    Returns:
        List of AnalysisResultResponse objects
    """
    result = await db.execute(
        select(AnalysisResult)
        .where(AnalysisResult.run_id == run_id)
        .order_by(AnalysisResult.model_type, AnalysisResult.created_at)
    )
    results = result.scalars().all()
    
    if not results:
        # Check if run exists but has no results yet
        return []
    
    return [AnalysisResultResponse.model_validate(r) for r in results]


@router.get("/results/{run_id}/summary")
async def get_results_summary(run_id: str, db: AsyncSession = Depends(get_db_session)):
    """
    Get summarized analysis results with aggregated metrics.
    
    Args:
        run_id: Analysis run ID
        db: Database session
    
    Returns:
        Summary dictionary with aggregated metrics
    """
    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.run_id == run_id)
    )
    results = result.scalars().all()
    
    if not results:
        raise HTTPException(status_code=404, detail=f"No results found for run {run_id}")
    
    # Aggregate by model type
    models_summary = {}
    for res in results:
        if res.model_type not in models_summary:
            models_summary[res.model_type] = {
                "count": 0,
                "anomalies": 0,
                "avg_residual": 0.0,
                "avg_anomaly_score": 0.0,
            }
        
        models_summary[res.model_type]["count"] += 1
        if res.anomaly_flag:
            models_summary[res.model_type]["anomalies"] += 1
        
        if res.residual is not None:
            models_summary[res.model_type]["avg_residual"] += res.residual
        if res.anomaly_score is not None:
            models_summary[res.model_type]["avg_anomaly_score"] += res.anomaly_score
    
    # Calculate averages
    for model_type in models_summary:
        count = models_summary[model_type]["count"]
        if count > 0:
            models_summary[model_type]["avg_residual"] /= count
            models_summary[model_type]["avg_anomaly_score"] /= count
    
    # Overall statistics
    total_anomalies = sum(m["anomalies"] for m in models_summary.values())
    total_records = len(results)
    
    # Efficiency distribution
    efficiency_dist = {}
    for res in results:
        if res.efficiency_class:
            efficiency_dist[res.efficiency_class] = efficiency_dist.get(res.efficiency_class, 0) + 1
    
    return {
        "run_id": run_id,
        "building_id": results[0].building_id,
        "total_records": total_records,
        "models_run": list(models_summary.keys()),
        "models_summary": models_summary,
        "total_anomalies": total_anomalies,
        "anomaly_rate": total_anomalies / total_records if total_records > 0 else 0,
        "efficiency_distribution": efficiency_dist,
        "created_at": results[0].created_at,
    }


@router.get("/results/{run_id}/chart-data")
async def get_chart_data(run_id: str, db: AsyncSession = Depends(get_db_session)):
    """
    Get chart-ready data for visualization.
    
    Args:
        run_id: Analysis run ID
        db: Database session
    
    Returns:
        Dictionary with data formatted for Recharts
    """
    from sqlalchemy.orm import joinedload
    
    # Get building info
    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.run_id == run_id).limit(1)
    )
    sample_result = result.scalar_one_or_none()
    
    if not sample_result:
        raise HTTPException(status_code=404, detail=f"No results found for run {run_id}")
    
    building_id = sample_result.building_id
    
    # Get readings with analysis results
    from backend.models.schemas import DailyReading
    
    readings_result = await db.execute(
        select(DailyReading)
        .where(DailyReading.building_id == building_id)
        .order_by(DailyReading.date)
    )
    readings = readings_result.scalars().all()
    
    # Get analysis results for this building (latest run)
    analysis_result = await db.execute(
        select(AnalysisResult)
        .where(AnalysisResult.building_id == building_id)
        .order_by(AnalysisResult.created_at.desc())
        .limit(len(readings))
    )
    analyses = analysis_result.scalars().all()
    
    # Create date-indexed maps
    actual_data = []
    predicted_data = []
    anomaly_data = []
    
    for reading in readings:
        data_point = {
            "date": reading.date,
            "actual_q": reading.q,
        }
        
        # Find matching analysis result
        for analysis in analyses:
            if analysis.predicted_q is not None:
                data_point["predicted_q"] = analysis.predicted_q
                break
        
        if reading.q is not None:
            actual_data.append(data_point)
        
        # Anomaly data
        for analysis in analyses:
            if analysis.anomaly_score is not None:
                anomaly_data.append({
                    "date": reading.date,
                    "anomaly_score": analysis.anomaly_score,
                    "is_anomaly": bool(analysis.anomaly_flag),
                })
                break
    
    # Residual histogram data
    residuals = [a.residual for a in analyses if a.residual is not None]
    histogram_bins = {}
    if residuals:
        bin_size = max(0.1, (max(residuals) - min(residuals)) / 20)
        for r in residuals:
            bin_key = round(round(r / bin_size) * bin_size, 2)
            histogram_bins[bin_key] = histogram_bins.get(bin_key, 0) + 1
    
    return {
        "timeseries": actual_data,
        "anomalies": anomaly_data,
        "residual_histogram": [
            {"bin": k, "count": v} for k, v in sorted(histogram_bins.items())
        ],
        "efficiency_classes": list(set(a.efficiency_class for a in analyses if a.efficiency_class)),
    }
