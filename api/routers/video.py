"""
Video generation endpoints

Supports both synchronous and asynchronous video generation.
"""

import os
from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from api.dependencies import ReelForgeDep
from api.schemas.video import (
    VideoGenerateRequest,
    VideoGenerateResponse,
    VideoGenerateAsyncResponse,
)
from api.tasks import task_manager, TaskType

router = APIRouter(prefix="/video", tags=["Video Generation"])


def path_to_url(request: Request, file_path: str) -> str:
    """Convert file path to accessible URL"""
    # file_path is like "output/abc123.mp4"
    # Remove "output/" prefix for cleaner URL
    if file_path.startswith("output/"):
        file_path = file_path[7:]  # Remove "output/"
    base_url = str(request.base_url).rstrip('/')
    return f"{base_url}/api/files/{file_path}"


@router.post("/generate/sync", response_model=VideoGenerateResponse)
async def generate_video_sync(
    request_body: VideoGenerateRequest,
    reelforge: ReelForgeDep,
    request: Request
):
    """
    Generate video synchronously
    
    This endpoint blocks until video generation is complete.
    Suitable for small videos (< 30 seconds).
    
    **Note**: May timeout for large videos. Use `/generate/async` instead.
    
    Request body includes all video generation parameters.
    See VideoGenerateRequest schema for details.
    
    Returns path to generated video, duration, and file size.
    """
    try:
        logger.info(f"Sync video generation: {request_body.text[:50]}...")
        
        # Call video generator service
        result = await reelforge.generate_video(
            text=request_body.text,
            mode=request_body.mode,
            title=request_body.title,
            n_scenes=request_body.n_scenes,
            voice_id=request_body.voice_id,
            use_uuid_filename=True,  # API mode: use UUID filename
            min_narration_words=request_body.min_narration_words,
            max_narration_words=request_body.max_narration_words,
            min_image_prompt_words=request_body.min_image_prompt_words,
            max_image_prompt_words=request_body.max_image_prompt_words,
            image_width=request_body.image_width,
            image_height=request_body.image_height,
            image_workflow=request_body.image_workflow,
            video_width=request_body.video_width,
            video_height=request_body.video_height,
            video_fps=request_body.video_fps,
            frame_template=request_body.frame_template,
            prompt_prefix=request_body.prompt_prefix,
            bgm_path=request_body.bgm_path,
            bgm_volume=request_body.bgm_volume,
        )
        
        # Get file size
        file_size = os.path.getsize(result.video_path) if os.path.exists(result.video_path) else 0
        
        # Convert path to URL
        video_url = path_to_url(request, result.video_path)
        
        return VideoGenerateResponse(
            video_url=video_url,
            duration=result.duration,
            file_size=file_size
        )
        
    except Exception as e:
        logger.error(f"Sync video generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/async", response_model=VideoGenerateAsyncResponse)
async def generate_video_async(
    request_body: VideoGenerateRequest,
    reelforge: ReelForgeDep,
    request: Request
):
    """
    Generate video asynchronously
    
    Creates a background task for video generation.
    Returns immediately with a task_id for tracking progress.
    
    **Workflow:**
    1. Submit video generation request
    2. Receive task_id in response
    3. Poll `/api/tasks/{task_id}` to check status
    4. When status is "completed", retrieve video from result
    
    Request body includes all video generation parameters.
    See VideoGenerateRequest schema for details.
    
    Returns task_id for tracking progress.
    """
    try:
        logger.info(f"Async video generation: {request_body.text[:50]}...")
        
        # Create task
        task = task_manager.create_task(
            task_type=TaskType.VIDEO_GENERATION,
            request_params=request_body.model_dump()
        )
        
        # Define async execution function
        async def execute_video_generation():
            """Execute video generation in background"""
            result = await reelforge.generate_video(
                text=request_body.text,
                mode=request_body.mode,
                title=request_body.title,
                n_scenes=request_body.n_scenes,
                voice_id=request_body.voice_id,
                use_uuid_filename=True,  # API mode: use UUID filename
                min_narration_words=request_body.min_narration_words,
                max_narration_words=request_body.max_narration_words,
                min_image_prompt_words=request_body.min_image_prompt_words,
                max_image_prompt_words=request_body.max_image_prompt_words,
                image_width=request_body.image_width,
                image_height=request_body.image_height,
                image_workflow=request_body.image_workflow,
                video_width=request_body.video_width,
                video_height=request_body.video_height,
                video_fps=request_body.video_fps,
                frame_template=request_body.frame_template,
                prompt_prefix=request_body.prompt_prefix,
                bgm_path=request_body.bgm_path,
                bgm_volume=request_body.bgm_volume,
                # Progress callback can be added here if needed
                # progress_callback=lambda event: task_manager.update_progress(...)
            )
            
            # Get file size
            file_size = os.path.getsize(result.video_path) if os.path.exists(result.video_path) else 0
            
            # Convert path to URL
            video_url = path_to_url(request, result.video_path)
            
            return {
                "video_url": video_url,
                "duration": result.duration,
                "file_size": file_size
            }
        
        # Start execution
        await task_manager.execute_task(
            task_id=task.task_id,
            coro_func=execute_video_generation
        )
        
        return VideoGenerateAsyncResponse(
            task_id=task.task_id
        )
        
    except Exception as e:
        logger.error(f"Async video generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

