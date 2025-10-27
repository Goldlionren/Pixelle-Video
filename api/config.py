"""
API Configuration
"""

from typing import Optional
from pydantic import BaseModel


class APIConfig(BaseModel):
    """API configuration"""
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # CORS settings
    cors_enabled: bool = True
    cors_origins: list[str] = ["*"]
    
    # Task settings
    max_concurrent_tasks: int = 5
    task_cleanup_interval: int = 3600  # Clean completed tasks every hour
    task_retention_time: int = 86400   # Keep task results for 24 hours
    
    # File upload settings
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    
    # API settings
    api_prefix: str = "/api"
    docs_url: Optional[str] = "/docs"
    redoc_url: Optional[str] = "/redoc"
    openapi_url: Optional[str] = "/openapi.json"


# Global config instance
api_config = APIConfig()

