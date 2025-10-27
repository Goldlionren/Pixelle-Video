"""
ReelForge API Layer

FastAPI-based REST API for video generation services.
"""

# Lazy import to avoid loading dependencies until needed
def get_app():
    """Get FastAPI app instance (lazy loading)"""
    from api.app import app
    return app


__all__ = ["get_app"]

