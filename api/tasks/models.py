"""
Task data models
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Task type"""
    VIDEO_GENERATION = "video_generation"


class TaskProgress(BaseModel):
    """Task progress information"""
    current: int = 0
    total: int = 0
    percentage: float = 0.0
    message: str = ""


class Task(BaseModel):
    """Task model"""
    task_id: str
    task_type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    
    # Progress tracking
    progress: Optional[TaskProgress] = None
    
    # Result
    result: Optional[Any] = None
    error: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Request parameters (for reference)
    request_params: Optional[dict] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

