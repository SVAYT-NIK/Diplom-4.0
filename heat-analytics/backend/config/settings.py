"""
Application settings and configuration.
"""
import os
from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    db_path: str = Field(
        default="/app/data/heat_analytics.db",
        description="Path to SQLite database file"
    )

    # Analytics parameters
    norm_hdd: int = Field(
        default=4500,
        description="Normal heating degree days for Abakan region"
    )
    anomaly_threshold: float = Field(
        default=3.0,
        description="Standard deviations threshold for anomaly detection"
    )
    cluster_k: int = Field(
        default=4,
        description="Number of clusters for K-Means clustering"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    # Upload settings
    upload_dir: Path = Field(
        default=Path("/app/data/uploads"),
        description="Directory for temporary file uploads"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
