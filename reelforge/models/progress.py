"""
Progress event models for video generation

Provides structured progress events for UI layer to consume and translate.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ProgressEvent:
    """
    Structured progress event for video generation
    
    Attributes:
        event_type: Type of event (e.g., "generating_narrations", "frame_step", "concatenating")
        progress: Progress value from 0.0 to 1.0
        frame_current: Current frame number (1-based, optional)
        frame_total: Total number of frames (optional)
        step: Current step within frame (1-4, optional)
        action: Action being performed (e.g., "audio", "image", "compose", "video", optional)
    
    Examples:
        # Simple progress event
        ProgressEvent(event_type="generating_narrations", progress=0.05)
        
        # Frame step event
        ProgressEvent(
            event_type="frame_step",
            progress=0.23,
            frame_current=1,
            frame_total=5,
            step=1,
            action="audio"
        )
    """
    event_type: str
    progress: float
    
    # Optional frame-related fields
    frame_current: Optional[int] = None
    frame_total: Optional[int] = None
    step: Optional[int] = None  # 1-4 for frame processing steps
    action: Optional[str] = None  # "audio", "image", "compose", "video"
    extra_info: Optional[str] = None  # Additional information (e.g., batch progress)
    
    def __post_init__(self):
        """Validate progress value"""
        if not 0.0 <= self.progress <= 1.0:
            raise ValueError(f"Progress must be between 0.0 and 1.0, got {self.progress}")

