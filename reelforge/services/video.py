"""
Video Processing Service

High-performance video composition service built on ffmpeg-python.

Features:
- Video concatenation
- Audio/video merging
- Background music addition
- Image to video conversion

Note: Requires FFmpeg to be installed on the system.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Literal, Optional

import ffmpeg
from loguru import logger


def check_ffmpeg() -> None:
    """
    Check if FFmpeg is installed on the system
    
    Raises:
        RuntimeError: If FFmpeg is not found
    """
    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "FFmpeg not found. Please install it:\n"
            "  macOS: brew install ffmpeg\n"
            "  Ubuntu/Debian: apt-get install ffmpeg\n"
            "  Windows: https://ffmpeg.org/download.html"
        )


# Check FFmpeg availability on module import
check_ffmpeg()


class VideoService:
    """
    Video compositor for common video processing tasks
    
    Uses ffmpeg-python for high-performance video processing.
    All operations preserve video quality when possible (stream copy).
    
    Examples:
        >>> compositor = VideoCompositor()
        >>> 
        >>> # Concatenate videos
        >>> compositor.concat_videos(
        ...     ["intro.mp4", "main.mp4", "outro.mp4"],
        ...     "final.mp4"
        ... )
        >>> 
        >>> # Add voiceover
        >>> compositor.merge_audio_video(
        ...     "visual.mp4",
        ...     "voiceover.mp3",
        ...     "final.mp4"
        ... )
        >>> 
        >>> # Add background music
        >>> compositor.add_bgm(
        ...     "video.mp4",
        ...     "music.mp3",
        ...     "final.mp4",
        ...     bgm_volume=0.3
        ... )
        >>> 
        >>> # Create video from image + audio
        >>> compositor.create_video_from_image(
        ...     "frame.png",
        ...     "narration.mp3",
        ...     "segment.mp4"
        ... )
    """
    
    def concat_videos(
        self,
        videos: List[str],
        output: str,
        method: Literal["demuxer", "filter"] = "demuxer",
        bgm_path: Optional[str] = None,
        bgm_volume: float = 0.2,
        bgm_mode: Literal["once", "loop"] = "loop"
    ) -> str:
        """
        Concatenate multiple videos into one
        
        Args:
            videos: List of video file paths to concatenate
            output: Output video file path
            method: Concatenation method
                - "demuxer": Fast, no re-encoding (requires identical formats)
                - "filter": Slower but handles different formats
            bgm_path: Background music file path (optional)
                - None: No BGM
                - Filename (e.g., "default.mp3", "happy.mp3"): Use built-in BGM from bgm/ folder
                - Custom path: Use custom BGM file
            bgm_volume: BGM volume level (0.0-1.0), default 0.2
            bgm_mode: BGM playback mode
                - "once": Play BGM once
                - "loop": Loop BGM to match video duration
        
        Returns:
            Path to the output video file
        
        Raises:
            ValueError: If videos list is empty
            RuntimeError: If FFmpeg execution fails
        
        Note:
            - demuxer method requires all videos to have identical:
              resolution, codec, fps, etc.
            - filter method re-encodes videos, slower but more compatible
        """
        if not videos:
            raise ValueError("Videos list cannot be empty")
        
        if len(videos) == 1:
            logger.info(f"Only one video provided, copying to {output}")
            shutil.copy(videos[0], output)
            return output
        
        logger.info(f"Concatenating {len(videos)} videos using {method} method")
        
        # Step 1: Concatenate videos
        if bgm_path:
            # If BGM needed, concatenate to temp file first
            temp_output = output.replace('.mp4', '_no_bgm.mp4')
            concat_result = self._concat_demuxer(videos, temp_output) if method == "demuxer" else self._concat_filter(videos, temp_output)
            
            # Step 2: Add BGM
            logger.info(f"Adding BGM: {bgm_path} (volume={bgm_volume}, mode={bgm_mode})")
            final_result = self._add_bgm_to_video(
                video=concat_result,
                bgm_path=bgm_path,
                output=output,
                volume=bgm_volume,
                mode=bgm_mode
            )
            
            # Clean up temp file
            if os.path.exists(temp_output):
                os.unlink(temp_output)
            
            return final_result
        else:
            # No BGM, direct concatenation
            if method == "demuxer":
                return self._concat_demuxer(videos, output)
            else:
                return self._concat_filter(videos, output)
    
    def _concat_demuxer(self, videos: List[str], output: str) -> str:
        """
        Concatenate using concat demuxer (fast, no re-encoding)
        
        FFmpeg equivalent:
            ffmpeg -f concat -safe 0 -i filelist.txt -c copy output.mp4
        """
        # Create temporary file list
        with tempfile.NamedTemporaryFile(
            mode='w',
            delete=False,
            suffix='.txt',
            encoding='utf-8'
        ) as f:
            for video in videos:
                abs_path = Path(video).absolute()
                escaped_path = str(abs_path).replace("'", "'\\''")
                f.write(f"file '{escaped_path}'\n")
            filelist = f.name
        
        try:
            logger.debug(f"Created filelist: {filelist}")
            (
                ffmpeg
                .input(filelist, format='concat', safe=0)
                .output(output, c='copy')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            logger.success(f"Videos concatenated successfully: {output}")
            return output
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"FFmpeg concat error: {error_msg}")
            raise RuntimeError(f"Failed to concatenate videos: {error_msg}")
        finally:
            if os.path.exists(filelist):
                os.unlink(filelist)
    
    def _concat_filter(self, videos: List[str], output: str) -> str:
        """
        Concatenate using concat filter (slower but handles different formats)
        
        FFmpeg equivalent:
            ffmpeg -i v1.mp4 -i v2.mp4 -filter_complex "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]"
                   -map "[v]" -map "[a]" output.mp4
        """
        try:
            inputs = [ffmpeg.input(v) for v in videos]
            (
                ffmpeg
                .concat(*inputs, v=1, a=1)
                .output(output)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            logger.success(f"Videos concatenated successfully: {output}")
            return output
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"FFmpeg concat filter error: {error_msg}")
            raise RuntimeError(f"Failed to concatenate videos: {error_msg}")
    
    def merge_audio_video(
        self,
        video: str,
        audio: str,
        output: str,
        replace_audio: bool = True,
        audio_volume: float = 1.0,
        video_volume: float = 0.0,
    ) -> str:
        """
        Merge audio with video
        
        Args:
            video: Video file path
            audio: Audio file path
            output: Output video file path
            replace_audio: If True, replace video's audio; if False, mix with original
            audio_volume: Volume of the new audio (0.0 to 1.0+)
            video_volume: Volume of original video audio (0.0 to 1.0+)
                         Only used when replace_audio=False
        
        Returns:
            Path to the output video file
        
        Raises:
            RuntimeError: If FFmpeg execution fails
        
        Note:
            - When replace_audio=True, video's original audio is removed
            - When replace_audio=False, original and new audio are mixed
            - Audio is trimmed/extended to match video duration
        """
        logger.info(f"Merging audio with video (replace={replace_audio})")
        
        try:
            input_video = ffmpeg.input(video)
            input_audio = ffmpeg.input(audio)
            
            if replace_audio:
                # Replace audio: use only new audio, ignore original
                (
                    ffmpeg
                    .output(
                        input_video.video,
                        input_audio.audio.filter('volume', audio_volume),
                        output,
                        vcodec='copy',
                        acodec='aac',
                        audio_bitrate='192k',
                        shortest=None
                    )
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
            else:
                # Mix audio: combine original and new audio
                mixed_audio = ffmpeg.filter(
                    [
                        input_video.audio.filter('volume', video_volume),
                        input_audio.audio.filter('volume', audio_volume)
                    ],
                    'amix',
                    inputs=2,
                    duration='first'
                )
                
                (
                    ffmpeg
                    .output(
                        input_video.video,
                        mixed_audio,
                        output,
                        vcodec='copy',
                        acodec='aac',
                        audio_bitrate='192k'
                    )
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
            
            logger.success(f"Audio merged successfully: {output}")
            return output
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"FFmpeg merge error: {error_msg}")
            raise RuntimeError(f"Failed to merge audio and video: {error_msg}")
    
    def create_video_from_image(
        self,
        image: str,
        audio: str,
        output: str,
        fps: int = 30,
    ) -> str:
        """
        Create video from static image and audio
        
        Args:
            image: Image file path
            audio: Audio file path
            output: Output video path
            fps: Frames per second
        
        Returns:
            Path to the output video
        
        Raises:
            RuntimeError: If FFmpeg execution fails
        
        Note:
            - Image is displayed as static frame for the duration of audio
            - Video duration matches audio duration
            - Useful for creating video segments from storyboard frames
        
        Example:
            >>> compositor.create_video_from_image(
            ...     "frame.png",
            ...     "narration.mp3",
            ...     "segment.mp4"
            ... )
        """
        logger.info("Creating video from image and audio")
        
        try:
            # Get audio duration to ensure exact video duration match
            probe = ffmpeg.probe(audio)
            audio_duration = float(probe['format']['duration'])
            logger.debug(f"Audio duration: {audio_duration:.3f}s")
            
            # Input image with loop (loop=1 means loop indefinitely)
            # Use framerate to set input framerate
            input_image = ffmpeg.input(image, loop=1, framerate=fps)
            input_audio = ffmpeg.input(audio)
            
            # Combine image and audio
            # Use -t to explicitly set video duration = audio duration
            (
                ffmpeg
                .output(
                    input_image,
                    input_audio,
                    output,
                    t=audio_duration,  # Force video duration to match audio exactly
                    vcodec='libx264',
                    acodec='aac',
                    pix_fmt='yuv420p',
                    audio_bitrate='192k',
                    preset='medium',
                    crf=23,
                    **{'b:v': '2M'}  # Video bitrate
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            logger.success(f"Video created from image: {output} (duration: {audio_duration:.3f}s)")
            return output
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"FFmpeg error creating video from image: {error_msg}")
            raise RuntimeError(f"Failed to create video from image: {error_msg}")
    
    def add_bgm(
        self,
        video: str,
        bgm: str,
        output: str,
        bgm_volume: float = 0.3,
        loop: bool = True,
        fade_in: float = 0.0,
        fade_out: float = 0.0,
    ) -> str:
        """
        Add background music to video
        
        Args:
            video: Video file path
            bgm: Background music file path
            output: Output video file path
            bgm_volume: BGM volume relative to original (0.0 to 1.0+)
            loop: If True, loop BGM to match video duration
            fade_in: BGM fade-in duration in seconds
            fade_out: BGM fade-out duration in seconds (not yet implemented)
        
        Returns:
            Path to the output video file
        
        Raises:
            RuntimeError: If FFmpeg execution fails
        
        Note:
            - BGM is mixed with original video audio
            - If loop=True, BGM repeats until video ends
            - Fade effects are applied to BGM only
        """
        logger.info(f"Adding BGM to video (volume={bgm_volume}, loop={loop})")
        
        try:
            input_video = ffmpeg.input(video)
            
            # Configure BGM input with looping if needed
            bgm_input = ffmpeg.input(
                bgm,
                stream_loop=-1 if loop else 0  # -1 = infinite loop
            )
            
            # Apply volume adjustment to BGM
            bgm_audio = bgm_input.audio.filter('volume', bgm_volume)
            
            # Apply fade effects if specified
            if fade_in > 0:
                bgm_audio = bgm_audio.filter('afade', type='in', duration=fade_in)
            # Note: fade_out at the end requires knowing the duration, which is complex
            # For now, we skip fade_out in this implementation
            # A more advanced implementation would need to:
            # 1. Get video duration
            # 2. Calculate fade_out start time
            # 3. Apply fade filter with specific start_time
            
            # Mix original audio with BGM
            mixed_audio = ffmpeg.filter(
                [input_video.audio, bgm_audio],
                'amix',
                inputs=2,
                duration='first'  # Use video's duration
            )
            
            (
                ffmpeg
                .output(
                    input_video.video,
                    mixed_audio,
                    output,
                    vcodec='copy',
                    acodec='aac',
                    audio_bitrate='192k'
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            logger.success(f"BGM added successfully: {output}")
            return output
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"FFmpeg BGM error: {error_msg}")
            raise RuntimeError(f"Failed to add BGM: {error_msg}")
    
    def _add_bgm_to_video(
        self,
        video: str,
        bgm_path: str,
        output: str,
        volume: float = 0.2,
        mode: Literal["once", "loop"] = "loop"
    ) -> str:
        """
        Internal helper to add BGM to video with path resolution
        
        Args:
            video: Video file path
            bgm_path: BGM path (can be preset name or custom path)
            output: Output file path
            volume: BGM volume (0.0-1.0)
            mode: "once" or "loop"
        
        Returns:
            Path to output video
        
        Raises:
            FileNotFoundError: If BGM file not found
        """
        # Resolve BGM path (raises FileNotFoundError if not found)
        resolved_bgm = self._resolve_bgm_path(bgm_path)
        
        # Add BGM using existing method
        loop = (mode == "loop")
        return self.add_bgm(
            video=video,
            bgm=resolved_bgm,
            output=output,
            bgm_volume=volume,
            loop=loop,
            fade_in=0.0
        )
    
    def _resolve_bgm_path(self, bgm_path: str) -> str:
        """
        Resolve BGM path (filename or custom path)
        
        Args:
            bgm_path: Can be:
                - Filename with extension (e.g., "default.mp3", "happy.mp3"): auto-resolved from bgm/ directory
                - Custom file path (absolute or relative)
        
        Returns:
            Resolved absolute path
        
        Raises:
            FileNotFoundError: If BGM file not found
        """
        # Try direct path first (absolute or relative)
        if os.path.exists(bgm_path):
            return os.path.abspath(bgm_path)
        
        # Try as filename in bgm/ directory
        preset_path = f"bgm/{bgm_path}"
        if os.path.exists(preset_path):
            return os.path.abspath(preset_path)
        
        # Not found - provide helpful error message
        tried_paths = [
            os.path.abspath(bgm_path),
            os.path.abspath(preset_path)
        ]
        
        # List available BGM files
        available_bgm = self._list_available_bgm()
        available_msg = f"\n  Available BGM files: {', '.join(available_bgm)}" if available_bgm else ""
        
        raise FileNotFoundError(
            f"BGM file not found: '{bgm_path}'\n"
            f"  Tried paths:\n"
            f"    1. {tried_paths[0]}\n"
            f"    2. {tried_paths[1]}"
            f"{available_msg}"
        )
    
    def _list_available_bgm(self) -> list[str]:
        """
        List available BGM files in bgm/ directory
        
        Returns:
            List of filenames (with extensions)
        """
        bgm_dir = "bgm"
        if not os.path.exists(bgm_dir):
            return []
        
        try:
            files = os.listdir(bgm_dir)
            # Return all audio files (mp3, wav, ogg, flac, etc.)
            audio_extensions = ('.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac')
            return [f for f in files if f.lower().endswith(audio_extensions)]
        except Exception:
            return []

