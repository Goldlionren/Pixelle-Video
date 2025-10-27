"""
Base schemas
"""

from typing import Any, Optional
from pydantic import BaseModel


class BaseResponse(BaseModel):
    """Base API response"""
    success: bool = True
    message: str = "Success"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = False
    message: str
    error: Optional[str] = None

