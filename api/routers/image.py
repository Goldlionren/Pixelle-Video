"""
Image generation endpoints
"""

from fastapi import APIRouter, HTTPException
from loguru import logger

from api.dependencies import ReelForgeDep
from api.schemas.image import ImageGenerateRequest, ImageGenerateResponse

router = APIRouter(prefix="/image", tags=["Image"])


@router.post("/generate", response_model=ImageGenerateResponse)
async def image_generate(
    request: ImageGenerateRequest,
    reelforge: ReelForgeDep
):
    """
    Image generation endpoint
    
    Generate image from text prompt using ComfyKit.
    
    - **prompt**: Image description/prompt
    - **width**: Image width (512-2048)
    - **height**: Image height (512-2048)
    - **workflow**: Optional custom workflow filename
    
    Returns path to generated image.
    """
    try:
        logger.info(f"Image generation request: {request.prompt[:50]}...")
        
        # Call image service
        image_path = await reelforge.image(
            prompt=request.prompt,
            width=request.width,
            height=request.height,
            workflow=request.workflow
        )
        
        return ImageGenerateResponse(
            image_path=image_path
        )
        
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

