"""
File service endpoints

Provides access to generated files (videos, images, audio).
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from loguru import logger

router = APIRouter(prefix="/files", tags=["Files"])


@router.get("/{file_path:path}")
async def get_file(file_path: str):
    """
    Get file by path
    
    Serves files from the output directory only.
    
    - **file_path**: File name or path (e.g., "abc123.mp4" or "subfolder/abc123.mp4")
    
    Returns file for download or preview.
    """
    try:
        # Automatically prepend "output/" to the path
        full_path = f"output/{file_path}"
        abs_path = Path.cwd() / full_path
        
        if not abs_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        if not abs_path.is_file():
            raise HTTPException(status_code=400, detail=f"Path is not a file: {file_path}")
        
        # Security: only allow access to output directory
        try:
            rel_path = abs_path.relative_to(Path.cwd())
            if not str(rel_path).startswith("output"):
                raise HTTPException(status_code=403, detail="Access denied: only output directory is accessible")
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Determine media type
        suffix = abs_path.suffix.lower()
        media_types = {
            '.mp4': 'video/mp4',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
        }
        media_type = media_types.get(suffix, 'application/octet-stream')
        
        # Use inline disposition for browser preview
        return FileResponse(
            path=str(abs_path),
            media_type=media_type,
            headers={
                "Content-Disposition": f'inline; filename="{abs_path.name}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File access error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

