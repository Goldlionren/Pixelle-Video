"""
LLM API schemas
"""

from typing import Optional
from pydantic import BaseModel, Field


class LLMChatRequest(BaseModel):
    """LLM chat request"""
    prompt: str = Field(..., description="User prompt")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperature (0.0-2.0)")
    max_tokens: int = Field(2000, ge=1, le=32000, description="Maximum tokens")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Explain the concept of atomic habits in 3 sentences",
                "temperature": 0.7,
                "max_tokens": 2000
            }
        }


class LLMChatResponse(BaseModel):
    """LLM chat response"""
    success: bool = True
    message: str = "Success"
    content: str = Field(..., description="Generated response")
    tokens_used: Optional[int] = Field(None, description="Tokens used (if available)")

