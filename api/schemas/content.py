"""
Content generation API schemas
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Narration Generation
# ============================================================================

class NarrationGenerateRequest(BaseModel):
    """Narration generation request"""
    text: str = Field(..., description="Source text to generate narrations from")
    n_scenes: int = Field(5, ge=1, le=20, description="Number of scenes")
    min_words: int = Field(5, ge=1, le=100, description="Minimum words per narration")
    max_words: int = Field(20, ge=1, le=200, description="Maximum words per narration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Atomic Habits is about making small changes that lead to remarkable results.",
                "n_scenes": 5,
                "min_words": 5,
                "max_words": 20
            }
        }


class NarrationGenerateResponse(BaseModel):
    """Narration generation response"""
    success: bool = True
    message: str = "Success"
    narrations: List[str] = Field(..., description="Generated narrations")


# ============================================================================
# Image Prompt Generation
# ============================================================================

class ImagePromptGenerateRequest(BaseModel):
    """Image prompt generation request"""
    narrations: List[str] = Field(..., description="List of narrations")
    min_words: int = Field(30, ge=10, le=100, description="Minimum words per prompt")
    max_words: int = Field(60, ge=10, le=200, description="Maximum words per prompt")
    
    class Config:
        json_schema_extra = {
            "example": {
                "narrations": [
                    "Small habits compound over time",
                    "Focus on systems, not goals"
                ],
                "min_words": 30,
                "max_words": 60
            }
        }


class ImagePromptGenerateResponse(BaseModel):
    """Image prompt generation response"""
    success: bool = True
    message: str = "Success"
    image_prompts: List[str] = Field(..., description="Generated image prompts")


# ============================================================================
# Title Generation
# ============================================================================

class TitleGenerateRequest(BaseModel):
    """Title generation request"""
    text: str = Field(..., description="Source text")
    style: Optional[str] = Field(None, description="Title style (e.g., 'engaging', 'formal')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Atomic Habits is about making small changes that lead to remarkable results.",
                "style": "engaging"
            }
        }


class TitleGenerateResponse(BaseModel):
    """Title generation response"""
    success: bool = True
    message: str = "Success"
    title: str = Field(..., description="Generated title")

