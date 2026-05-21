"""
SQLAlchemy database models for heat analytics.
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON,
    create_engine, event
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from pydantic import BaseModel, Field
from typing import Optional as PydanticOptional


Base = declarative_base()


class Building(Base):
    """Building model representing a multi-apartment building (МКД)."""
    
    __tablename__ = "buildings"
    
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String(500), nullable=False, index=True)
    area_m2 = Column(Float, nullable=False)
    year_built = Column(Integer, nullable=True)
    heating_type = Column(String(100), default="central")
    norm_gcal_m2 = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    daily_readings = relationship("DailyReading", back_populates="building", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="building", cascade="all, delete-orphan")


class DailyReading(Base):
    """Daily reading model for heat consumption data."""
    
    __tablename__ = "daily_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=False, index=True)
    date = Column(String(20), nullable=False, index=True)  # YYYY-MM-DD format
    t1 = Column(Float, nullable=True)  # Supply temperature
    t2 = Column(Float, nullable=True)  # Return temperature
    p1 = Column(Float, nullable=True)  # Supply pressure
    p2 = Column(Float, nullable=True)  # Return pressure
    v1 = Column(Float, nullable=True)  # Supply volume flow
    v2 = Column(Float, nullable=True)  # Return volume flow
    m1 = Column(Float, nullable=True)  # Supply mass flow
    m2 = Column(Float, nullable=True)  # Return mass flow
    q = Column(Float, nullable=True)   # Heat energy (Gcal)
    dt = Column(Float, nullable=True)  # Temperature difference
    dv = Column(Float, nullable=True)  # Volume difference
    dm = Column(Float, nullable=True)  # Mass difference
    imbalance = Column(Float, nullable=True)  # Imbalance value
    ns_codes = Column(Text, nullable=True)  # Comma-separated NS codes
    status = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    building = relationship("Building", back_populates="daily_readings")


class AnalysisResult(Base):
    """Analysis results from various models and algorithms."""
    
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=False, index=True)
    run_id = Column(String(100), nullable=False, index=True)  # Unique identifier for analysis run
    model_type = Column(String(100), nullable=False)  # ols, huber, ridge, lasso, etc.
    predicted_q = Column(Float, nullable=True)
    residual = Column(Float, nullable=True)
    anomaly_score = Column(Float, nullable=True)
    anomaly_flag = Column(Integer, default=0)  # 0 = normal, 1 = anomaly
    cluster_id = Column(Integer, nullable=True)
    efficiency_class = Column(String(50), nullable=True)  # excellent, good, normal, poor, critical
    norm_deviation_pct = Column(Float, nullable=True)
    params = Column(JSON, nullable=True)  # Model parameters and hyperparameters
    metrics = Column(JSON, nullable=True)  # Performance metrics (R2, MAE, etc.)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    building = relationship("Building", back_populates="analysis_results")


class AuditLog(Base):
    """Audit log for tracking user actions."""
    
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=True)


# Pydantic schemas for API requests/responses

class BuildingBase(BaseModel):
    """Base schema for building data."""
    address: str
    area_m2: float
    year_built: PydanticOptional[int] = None
    heating_type: str = "central"
    norm_gcal_m2: PydanticOptional[float] = None


class BuildingCreate(BuildingBase):
    """Schema for creating a new building."""
    pass


class BuildingResponse(BuildingBase):
    """Schema for building response with ID."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class DailyReadingBase(BaseModel):
    """Base schema for daily reading data."""
    date: str
    t1: PydanticOptional[float] = None
    t2: PydanticOptional[float] = None
    p1: PydanticOptional[float] = None
    p2: PydanticOptional[float] = None
    v1: PydanticOptional[float] = None
    v2: PydanticOptional[float] = None
    m1: PydanticOptional[float] = None
    m2: PydanticOptional[float] = None
    q: PydanticOptional[float] = None
    dt: PydanticOptional[float] = None
    dv: PydanticOptional[float] = None
    dm: PydanticOptional[float] = None
    imbalance: PydanticOptional[float] = None
    ns_codes: PydanticOptional[str] = None
    status: PydanticOptional[str] = None


class DailyReadingResponse(DailyReadingBase):
    """Schema for daily reading response with ID."""
    id: int
    building_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisRequest(BaseModel):
    """Schema for analysis request."""
    building_id: int
    models: List[str] = ["ols", "huber", "isolation_forest", "kmeans"]


class AnalysisResultResponse(BaseModel):
    """Schema for analysis result response."""
    id: int
    building_id: int
    run_id: str
    model_type: str
    predicted_q: PydanticOptional[float] = None
    residual: PydanticOptional[float] = None
    anomaly_score: PydanticOptional[float] = None
    anomaly_flag: int
    cluster_id: PydanticOptional[int] = None
    efficiency_class: PydanticOptional[str] = None
    norm_deviation_pct: PydanticOptional[float] = None
    params: PydanticOptional[dict] = None
    metrics: PydanticOptional[dict] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    """Schema for file upload response."""
    status: str
    building_id: int
    rows_parsed: int
    message: str = ""


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    db_path: str
