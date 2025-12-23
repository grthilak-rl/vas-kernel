"""
Configuration management for VAS backend.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Dict, Any
import json


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database
    database_url: str = Field(default="postgresql://vas:vas_password@localhost:5432/vas_db", alias="DATABASE_URL")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    
    # MediaSoup
    mediasoup_worker_options: Dict[str, Any] = Field(
        default={"logLevel": "debug", "rtcMinPort": 40000, "rtcMaxPort": 49999},
        alias="MEDIASOUP_WORKER_OPTIONS"
    )
    
    # API
    api_port: int = Field(default=8080, alias="API_PORT")
    websocket_port: int = Field(default=8081, alias="WEBSOCKET_PORT")
    
    # Security
    secret_key: str = Field(default="your-secret-key", alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = 30
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")
    
    # Recording
    recordings_path: str = Field(default="/app/recordings", alias="RECORDINGS_PATH")
    hls_segment_duration: int = Field(default=10, alias="HLS_SEGMENT_DURATION")
    retention_days: int = Field(default=7, alias="RETENTION_DAYS")
    
    # Storage
    storage_type: str = Field(default="local", alias="STORAGE_TYPE")
    s3_bucket: str = Field(default="", alias="S3_BUCKET")
    s3_region: str = Field(default="", alias="S3_REGION")
    s3_access_key: str = Field(default="", alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(default="", alias="S3_SECRET_KEY")
    minio_endpoint: str = Field(default="", alias="MINIO_ENDPOINT")
    
    @classmethod
    def load_mediasoup_options(cls, value: str) -> Dict[str, Any]:
        """Parse MediaSoup worker options from string."""
        if isinstance(value, str):
            return json.loads(value)
        return value
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


