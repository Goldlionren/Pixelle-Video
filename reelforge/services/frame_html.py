"""
HTML-based Frame Generator Service

Renders HTML templates to frame images with variable substitution

Linux Environment Requirements:
    - fontconfig package must be installed
    - Basic fonts (e.g., fonts-liberation, fonts-noto) recommended
    
    Ubuntu/Debian: sudo apt-get install -y fontconfig fonts-liberation fonts-noto-cjk
    CentOS/RHEL: sudo yum install -y fontconfig liberation-fonts google-noto-cjk-fonts
"""

import os
import uuid
from typing import Dict, Any, Optional
from pathlib import Path
from html2image import Html2Image
from loguru import logger


class HTMLFrameGenerator:
    """
    HTML-based frame generator
    
    Renders HTML templates to frame images with variable substitution.
    Users can create custom templates using any HTML/CSS.
    
    Usage:
        >>> generator = HTMLFrameGenerator("templates/modern.html")
        >>> frame_path = await generator.generate_frame(
        ...     topic="Why reading matters",
        ...     text="Reading builds new neural pathways...",
        ...     image="/path/to/image.png",
        ...     ext={"content_title": "Sample Title", "content_author": "Author Name"}
        ... )
    """
    
    def __init__(self, template_path: str):
        """
        Initialize HTML frame generator
        
        Args:
            template_path: Path to HTML template file
        """
        self.template_path = template_path
        self.template = self._load_template(template_path)
        self.hti = None  # Lazy init to avoid overhead
        self._check_linux_dependencies()
        logger.debug(f"Loaded HTML template: {template_path}")
    
    def _check_linux_dependencies(self):
        """Check Linux system dependencies and warn if missing"""
        if os.name != 'posix':
            return
        
        try:
            import subprocess
            
            # Check fontconfig
            result = subprocess.run(
                ['fc-list'], 
                capture_output=True, 
                timeout=2
            )
            
            if result.returncode != 0:
                logger.warning(
                    "⚠️  fontconfig not found or not working properly. "
                    "Install with: sudo apt-get install -y fontconfig fonts-liberation fonts-noto-cjk"
                )
            elif not result.stdout:
                logger.warning(
                    "⚠️  No fonts detected by fontconfig. "
                    "Install fonts with: sudo apt-get install -y fonts-liberation fonts-noto-cjk"
                )
            else:
                logger.debug(f"✓ Fontconfig detected {len(result.stdout.splitlines())} fonts")
                
        except FileNotFoundError:
            logger.warning(
                "⚠️  fontconfig (fc-list) not found on system. "
                "Install with: sudo apt-get install -y fontconfig"
            )
        except Exception as e:
            logger.debug(f"Could not check fontconfig status: {e}")
    
    def _load_template(self, template_path: str) -> str:
        """Load HTML template from file"""
        path = Path(template_path)
        if not path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.debug(f"Template loaded: {len(content)} chars")
        return content
    
    def _find_chrome_executable(self) -> Optional[str]:
        """
        Find suitable Chrome/Chromium executable, preferring non-snap versions
        
        Returns:
            Path to Chrome executable or None to use default
        """
        if os.name != 'posix':
            return None
        
        import subprocess
        
        # Preferred browsers (non-snap versions)
        candidates = [
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
            '/usr/local/bin/chrome',
            '/usr/local/bin/chromium',
        ]
        
        # Check each candidate
        for path in candidates:
            if os.path.exists(path) and os.access(path, os.X_OK):
                try:
                    # Verify it's not a snap by checking the path
                    result = subprocess.run(
                        ['readlink', '-f', path],
                        capture_output=True,
                        text=True,
                        timeout=1
                    )
                    real_path = result.stdout.strip()
                    
                    if '/snap/' not in real_path:
                        logger.info(f"✓ Found non-snap browser: {path} -> {real_path}")
                        return path
                    else:
                        logger.debug(f"✗ Skipping snap browser: {path}")
                except Exception as e:
                    logger.debug(f"Error checking {path}: {e}")
        
        # Warn if no suitable browser found
        logger.warning(
            "⚠️  No non-snap Chrome/Chromium found. Snap browsers have AppArmor restrictions.\n"
            "   Install system Chrome with:\n"
            "   wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb\n"
            "   sudo dpkg -i google-chrome-stable_current_amd64.deb\n"
            "   Or install Chromium: sudo apt-get install -y chromium-browser"
        )
        return None
    
    def _ensure_hti(self, width: int, height: int):
        """Lazily initialize Html2Image instance"""
        if self.hti is None:
            # Configure Chrome flags for Linux headless environment
            custom_flags = [
                '--no-sandbox',  # Bypass AppArmor/sandbox restrictions
                '--disable-dev-shm-usage',  # Avoid shared memory issues
                '--disable-gpu',  # Disable GPU acceleration
                '--disable-software-rasterizer',  # Disable software rasterizer
                '--disable-extensions',  # Disable extensions
                '--disable-setuid-sandbox',  # Additional sandbox bypass
                '--disable-dbus',  # Disable DBus to avoid permission errors
                '--hide-scrollbars',  # Hide scrollbars for cleaner output
                '--mute-audio',  # Mute audio
                '--disable-background-networking',  # Disable background networking
                '--disable-features=TranslateUI',  # Disable translate UI
                '--disable-ipc-flooding-protection',  # Improve performance
                '--no-first-run',  # Skip first run dialogs
                '--no-default-browser-check',  # Skip default browser check
                '--disable-backgrounding-occluded-windows',  # Improve performance
                '--disable-renderer-backgrounding',  # Improve performance
            ]
            
            # Try to find non-snap browser
            browser_path = self._find_chrome_executable()
            
            kwargs = {
                'size': (width, height),
                'custom_flags': custom_flags
            }
            
            if browser_path:
                kwargs['browser_executable'] = browser_path
            
            self.hti = Html2Image(**kwargs)
            
            if browser_path:
                logger.debug(f"Initialized Html2Image with size ({width}, {height}), {len(custom_flags)} custom flags, using browser: {browser_path}")
            else:
                logger.debug(f"Initialized Html2Image with size ({width}, {height}) and {len(custom_flags)} custom flags")
    
    async def generate_frame(
        self,
        title: str,
        text: str,
        image: str,
        ext: Optional[Dict[str, Any]] = None,
        width: int = 1080,
        height: int = 1920,
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate frame from HTML template
        
        Args:
            title: Video title
            text: Narration text for this frame
            image: Path to AI-generated image (supports relative path, absolute path, or HTTP URL)
            ext: Additional data (content_title, content_author, etc.)
            width: Frame width in pixels
            height: Frame height in pixels
            output_path: Custom output path (auto-generated if None)
        
        Returns:
            Path to generated frame image
        """
        # Convert image path to absolute path or file:// URL for html2image
        if image and not image.startswith(('http://', 'https://', 'data:', 'file://')):
            # Local file path - convert to absolute path and file:// URL
            image_path = Path(image)
            if not image_path.is_absolute():
                # Relative to current working directory (project root)
                image_path = Path.cwd() / image
            
            # Ensure the file exists
            if not image_path.exists():
                logger.warning(f"Image file not found: {image_path}")
            else:
                # Convert to file:// URL for html2image compatibility
                image = image_path.as_uri()
                logger.debug(f"Converted image path to: {image}")
        
        # Build variable context
        context = {
            # Required variables
            "title": title,
            "text": text,
            "image": image,
        }
        
        # Add all ext fields
        if ext:
            context.update(ext)
        
        # Replace variables in HTML
        html = self.template
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            html = html.replace(placeholder, str(value) if value is not None else "")
        
        # Use provided output path or auto-generate
        if output_path is None:
            # Fallback: auto-generate (for backward compatibility)
            from reelforge.utils.os_util import get_output_path
            output_filename = f"frame_{uuid.uuid4().hex[:16]}.png"
            output_path = get_output_path(output_filename)
        else:
            # Ensure parent directory exists
            import os
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Extract filename from output_path for html2image
        import os
        output_filename = os.path.basename(output_path)
        output_dir = os.path.dirname(output_path)
        
        # Ensure Html2Image is initialized
        self._ensure_hti(width, height)
        
        # Render HTML to image
        logger.debug(f"Rendering HTML template to {output_path}")
        try:
            self.hti.screenshot(
                html_str=html,
                save_as=output_filename,
                size=(width, height)
            )
            
            # html2image saves to current directory by default, move to target directory
            import shutil
            temp_file = os.path.join(os.getcwd(), output_filename)
            if os.path.exists(temp_file) and temp_file != output_path:
                shutil.move(temp_file, output_path)
            
            logger.info(f"✅ Frame generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to render HTML template: {e}")
            raise RuntimeError(f"HTML rendering failed: {e}")

