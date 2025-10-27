"""
FastAPI Dependencies

Provides dependency injection for ReelForgeCore and other services.
"""

from typing import Annotated
from fastapi import Depends
from loguru import logger

from reelforge.service import ReelForgeCore


# Global ReelForge instance
_reelforge_instance: ReelForgeCore = None


async def get_reelforge() -> ReelForgeCore:
    """
    Get ReelForge core instance (dependency injection)
    
    Returns:
        ReelForgeCore instance
    """
    global _reelforge_instance
    
    if _reelforge_instance is None:
        _reelforge_instance = ReelForgeCore()
        await _reelforge_instance.initialize()
        logger.info("✅ ReelForge initialized for API")
    
    return _reelforge_instance


async def shutdown_reelforge():
    """Shutdown ReelForge instance"""
    global _reelforge_instance
    if _reelforge_instance:
        logger.info("Shutting down ReelForge...")
        _reelforge_instance = None


# Type alias for dependency injection
ReelForgeDep = Annotated[ReelForgeCore, Depends(get_reelforge)]

