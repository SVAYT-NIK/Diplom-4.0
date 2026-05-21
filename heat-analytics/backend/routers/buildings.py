"""
Router for building management endpoints.
"""
import logging
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.services.db import async_session_maker
from backend.models.schemas import Building, BuildingResponse, BuildingCreate


logger = logging.getLogger(__name__)

router = APIRouter()


async def get_db_session():
    """Get database session."""
    async with async_session_maker() as session:
        yield session


@router.get("/buildings", response_model=List[BuildingResponse])
async def get_buildings(db: AsyncSession = Depends(get_db_session)):
    """
    Get all buildings in the database.
    
    Returns:
        List of BuildingResponse objects
    """
    result = await db.execute(select(Building).order_by(Building.created_at.desc()))
    buildings = result.scalars().all()
    return [BuildingResponse.model_validate(b) for b in buildings]


@router.get("/buildings/{building_id}", response_model=BuildingResponse)
async def get_building(building_id: int, db: AsyncSession = Depends(get_db_session)):
    """
    Get a specific building by ID.
    
    Args:
        building_id: Building ID
        db: Database session
    
    Returns:
        BuildingResponse object
    """
    result = await db.execute(select(Building).where(Building.id == building_id))
    building = result.scalar_one_or_none()
    
    if not building:
        raise HTTPException(status_code=404, detail=f"Building with id {building_id} not found")
    
    return BuildingResponse.model_validate(building)


@router.post("/buildings", response_model=BuildingResponse)
async def create_building(
    building_data: BuildingCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Create a new building.
    
    Args:
        building_data: Building data
        db: Database session
    
    Returns:
        BuildingResponse object
    """
    building = Building(**building_data.dict())
    db.add(building)
    await db.flush()
    await db.refresh(building)
    
    logger.info(f"Created building: {building.id}, {building.address}")
    
    return BuildingResponse.model_validate(building)


@router.delete("/buildings/{building_id}")
async def delete_building(building_id: int, db: AsyncSession = Depends(get_db_session)):
    """
    Delete a building and all its associated data.
    
    Args:
        building_id: Building ID
        db: Database session
    
    Returns:
        Success message
    """
    result = await db.execute(select(Building).where(Building.id == building_id))
    building = result.scalar_one_or_none()
    
    if not building:
        raise HTTPException(status_code=404, detail=f"Building with id {building_id} not found")
    
    await db.delete(building)
    await db.commit()
    
    logger.info(f"Deleted building: {building_id}")
    
    return {"message": f"Building {building_id} deleted successfully"}
