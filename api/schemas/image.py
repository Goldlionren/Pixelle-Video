"""
Image generation API schemas
"""

from typing import Optional
from pydantic import BaseModel, Field


class ImageGenerateRequest(BaseModel):
    """Image generation request"""
    prompt: str = Field(..., description="Image generation prompt")
    width: int = Field(1024, ge=512, le=2048, description="Image width")
    height: int = Field(1024, ge=512, le=2048, description="Image height")
    workflow: Optional[str] = Field(None, description="Custom workflow filename")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "A serene mountain landscape at sunset, photorealistic style",
                "width": 1024,
                "height": 1024
            }
        }


class ImageGenerateResponse(BaseModel):
    """Image generation response"""
    success: bool = True
    message: str = "Success"
    image_path: str = Field(..., description="Path to generated image")

