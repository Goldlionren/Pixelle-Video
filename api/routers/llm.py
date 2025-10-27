"""
LLM (Large Language Model) endpoints
"""

from fastapi import APIRouter, HTTPException
from loguru import logger

from api.dependencies import ReelForgeDep
from api.schemas.llm import LLMChatRequest, LLMChatResponse

router = APIRouter(prefix="/llm", tags=["LLM"])


@router.post("/chat", response_model=LLMChatResponse)
async def llm_chat(
    request: LLMChatRequest,
    reelforge: ReelForgeDep
):
    """
    LLM chat endpoint
    
    Generate text response using configured LLM.
    
    - **prompt**: User prompt/question
    - **temperature**: Creativity level (0.0-2.0, lower = more deterministic)
    - **max_tokens**: Maximum response length
    
    Returns generated text response.
    """
    try:
        logger.info(f"LLM chat request: {request.prompt[:50]}...")
        
        # Call LLM service
        response = await reelforge.llm(
            prompt=request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return LLMChatResponse(
            content=response,
            tokens_used=None  # Can add token counting if needed
        )
        
    except Exception as e:
        logger.error(f"LLM chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

