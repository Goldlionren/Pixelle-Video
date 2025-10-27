"""
Health check and system info endpoints
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str = "0.1.0"
    service: str = "ReelForge API"


class CapabilitiesResponse(BaseModel):
    """Capabilities response"""
    success: bool = True
    capabilities: dict


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns service status and version information.
    """
    return HealthResponse()


@router.get("/version", response_model=HealthResponse)
async def get_version():
    """
    Get API version
    
    Returns version information.
    """
    return HealthResponse()

