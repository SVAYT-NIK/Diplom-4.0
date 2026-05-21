"""
Router for file upload endpoints.
"""
import logging
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.services.db import async_session_maker
from backend.models.schemas import Building, BuildingCreate, DailyReading, UploadResponse
from backend.services.parser import parse_excel_file, get_building_info_from_metadata
from backend.config.settings import settings


logger = logging.getLogger(__name__)

router = APIRouter()


async def get_db_session():
    """Get database session."""
    async with async_session_maker() as session:
        yield session


@router.post("/upload", response_model=UploadResponse)
async def upload_excel(
    file: UploadFile = File(..., description="Excel file with heat consumption data"),
    building_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Upload Excel file with heat consumption data.
    
    - Parses the Excel file
    - Creates or updates building information
    - Saves daily readings to database
    - Deletes temporary file after processing
    
    Args:
        file: Excel file to upload (multipart/form-data)
        building_id: Optional existing building ID (if None, creates new building)
        db: Database session
    
    Returns:
        UploadResponse with status, building_id, and rows_parsed count
    """
    logger.info(f"Received file upload: {file.filename}, content_type: {file.content_type}, size: {file.size}")
    
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed")
    
    # Create upload directory
    upload_dir = settings.upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save uploaded file temporarily - use safe filename
    safe_filename = f"{uuid.uuid4()}_{Path(file.filename).name}"
    temp_file_path = upload_dir / safe_filename
    
    try:
        # Read file content and save
        content = await file.read()
        logger.info(f"Read {len(content)} bytes from file")
        
        with open(temp_file_path, "wb") as buffer:
            buffer.write(content)
        
        logger.info(f"Saved temporary file: {temp_file_path}")
        
        # Parse Excel file
        metadata, readings = parse_excel_file(temp_file_path)
        
        if not readings:
            raise HTTPException(status_code=400, detail="No valid data rows found in file")
        
        # Get or create building
        if building_id:
            # Use existing building
            result = await db.execute(select(Building).where(Building.id == building_id))
            building = result.scalar_one_or_none()
            
            if not building:
                raise HTTPException(status_code=404, detail=f"Building with id {building_id} not found")
        else:
            # Extract building info from metadata or create default
            building_info = get_building_info_from_metadata(metadata)
            
            # If no address found, use filename as placeholder
            if not building_info.get("address"):
                building_info["address"] = Path(file.filename).stem
            
            # Set default area if not found
            if not building_info.get("area_m2"):
                building_info["area_m2"] = 1000.0  # Default placeholder
            
            # Create new building
            building_data = BuildingCreate(**building_info)
            building = Building(**building_data.dict())
            
            db.add(building)
            await db.flush()  # Get the ID
            await db.refresh(building)
            
            logger.info(f"Created new building: {building.id}, {building.address}")
        
        # Save readings to database
        readings_count = 0
        for reading_data in readings:
            reading = DailyReading(
                building_id=building.id,
                **reading_data.dict(),
            )
            db.add(reading)
            readings_count += 1
        
        await db.commit()
        
        logger.info(f"Saved {readings_count} readings for building {building.id}")
        
        # Delete temporary file
        temp_file_path.unlink(missing_ok=True)
        logger.info(f"Deleted temporary file: {temp_file_path}")
        
        return UploadResponse(
            status="success",
            building_id=building.id,
            rows_parsed=readings_count,
            message=f"Successfully uploaded {readings_count} readings for building at {building.address}"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing upload: {e}", exc_info=True)
        # Clean up temp file on error
        if 'temp_file_path' in locals() and temp_file_path.exists():
            temp_file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
