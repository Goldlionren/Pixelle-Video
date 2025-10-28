"""
OS utilities for file and path management

Provides utilities for managing paths and files in ReelForge.
Inspired by Pixelle-MCP's os_util.py.
"""

import os
import random
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Literal


def get_reelforge_root_path() -> str:
    """
    Get ReelForge root path - current working directory
    
    Returns:
        Current working directory as string
    """
    return str(Path.cwd())


def ensure_reelforge_root_path() -> str:
    """
    Ensure ReelForge root path exists and return the path
    
    Returns:
        Root path as string
    """
    root_path = get_reelforge_root_path()
    root_path_obj = Path(root_path)
    output_dir = root_path_obj / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return root_path


def get_root_path(*paths: str) -> str:
    """
    Get path relative to ReelForge root path
    
    Args:
        *paths: Path components to join
    
    Returns:
        Absolute path as string
    
    Example:
        get_root_path("temp", "audio.mp3")
        # Returns: "/path/to/project/temp/audio.mp3"
    """
    root_path = ensure_reelforge_root_path()
    if paths:
        return os.path.join(root_path, *paths)
    return root_path


def get_temp_path(*paths: str) -> str:
    """
    Get path relative to ReelForge temp folder
    
    Args:
        *paths: Path components to join
    
    Returns:
        Absolute path to temp directory or file
    
    Example:
        get_temp_path("audio.mp3")
        # Returns: "/path/to/project/temp/audio.mp3"
    """
    temp_path = get_root_path("temp")
    if paths:
        return os.path.join(temp_path, *paths)
    return temp_path


def get_data_path(*paths: str) -> str:
    """
    Get path relative to ReelForge data folder
    
    Args:
        *paths: Path components to join
    
    Returns:
        Absolute path to data directory or file
    
    Example:
        get_data_path("videos", "output.mp4")
        # Returns: "/path/to/project/data/videos/output.mp4"
    """
    data_path = get_root_path("data")
    if paths:
        return os.path.join(data_path, *paths)
    return data_path


def get_output_path(*paths: str) -> str:
    """
    Get path relative to ReelForge output folder
    
    Args:
        *paths: Path components to join
    
    Returns:
        Absolute path to output directory or file
    
    Example:
        get_output_path("video.mp4")
        # Returns: "/path/to/project/output/video.mp4"
    """
    output_path = get_root_path("output")
    if paths:
        return os.path.join(output_path, *paths)
    return output_path


def save_bytes_to_file(data: bytes, file_path: str) -> str:
    """
    Save bytes data to file
    
    Creates parent directories if they don't exist.
    
    Args:
        data: Binary data to save
        file_path: Target file path
    
    Returns:
        Absolute path of saved file
    
    Example:
        save_bytes_to_file(audio_data, get_temp_path("audio.mp3"))
    """
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Write binary data
    with open(file_path, "wb") as f:
        f.write(data)
    
    return os.path.abspath(file_path)


def ensure_dir(path: str) -> str:
    """
    Ensure directory exists, create if not
    
    Args:
        path: Directory path
    
    Returns:
        Absolute path of directory
    """
    os.makedirs(path, exist_ok=True)
    return os.path.abspath(path)


# ========== Task Directory Management ==========

def create_task_id() -> str:
    """
    Create unique task ID with timestamp + random suffix
    
    Format: {timestamp}_{random_hex}
    Example: "20251028_143052_ab3d"
    
    Collision probability: < 0.0001% (65536 combinations per second)
    
    Returns:
        Task ID string
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_suffix = f"{random.randint(0, 0xFFFF):04x}"  # 4-digit hex (0000-ffff)
    return f"{timestamp}_{random_suffix}"


def create_task_output_dir(task_id: Optional[str] = None) -> Tuple[str, str]:
    """
    Create isolated output directory for single video generation task
    
    Directory structure:
        output/{task_id}/
        ├── final.mp4           # Final video output
        ├── frames/             # All frame-related files
        │   ├── 0_audio.mp3
        │   ├── 0_image.png
        │   ├── 0_composed.png
        │   ├── 0_segment.mp4
        │   └── ...
        └── metadata.json       # Optional: task metadata
    
    Args:
        task_id: Optional task ID (auto-generated if None)
    
    Returns:
        (task_dir, task_id) tuple
        
    Example:
        >>> task_dir, task_id = create_task_output_dir()
        >>> # task_dir = "/path/to/project/output/20251028_143052_ab3d"
        >>> # task_id = "20251028_143052_ab3d"
    """
    if task_id is None:
        task_id = create_task_id()
    
    task_dir = get_output_path(task_id)
    frames_dir = os.path.join(task_dir, "frames")
    
    # Create directories
    os.makedirs(frames_dir, exist_ok=True)
    
    return task_dir, task_id


def get_task_path(task_id: str, *paths: str) -> str:
    """
    Get path within task directory
    
    Args:
        task_id: Task ID
        *paths: Path components to join
    
    Returns:
        Absolute path within task directory
        
    Example:
        >>> get_task_path("20251028_143052_ab3d", "final.mp4")
        >>> # Returns: "/path/to/project/output/20251028_143052_ab3d/final.mp4"
    """
    task_dir = get_output_path(task_id)
    if paths:
        return os.path.join(task_dir, *paths)
    return task_dir


def get_task_frame_path(
    task_id: str, 
    frame_index: int, 
    file_type: Literal["audio", "image", "composed", "segment"]
) -> str:
    """
    Get frame file path within task directory
    
    Args:
        task_id: Task ID
        frame_index: Frame index (0-based)
        file_type: File type (audio/image/composed/segment)
    
    Returns:
        Absolute path to frame file
        
    Example:
        >>> get_task_frame_path("20251028_143052_ab3d", 0, "audio")
        >>> # Returns: ".../output/20251028_143052_ab3d/frames/0_audio.mp3"
    """
    ext_map = {
        "audio": "mp3",
        "image": "png",
        "composed": "png",
        "segment": "mp4"
    }
    
    filename = f"{frame_index}_{file_type}.{ext_map[file_type]}"
    return get_task_path(task_id, "frames", filename)


def get_task_final_video_path(task_id: str) -> str:
    """
    Get final video path within task directory
    
    Args:
        task_id: Task ID
    
    Returns:
        Absolute path to final video
        
    Example:
        >>> get_task_final_video_path("20251028_143052_ab3d")
        >>> # Returns: ".../output/20251028_143052_ab3d/final.mp4"
    """
    return get_task_path(task_id, "final.mp4")

