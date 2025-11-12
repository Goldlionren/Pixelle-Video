# Copyright (C) 2025 AIDC-AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Standard Video Generation Pipeline

Standard workflow for generating short videos from topic or fixed script.
This is the default pipeline for general-purpose video generation.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Literal, Dict, Any

from loguru import logger

from pixelle_video.pipelines.base import BasePipeline
from pixelle_video.models.progress import ProgressEvent
from pixelle_video.models.storyboard import (
    Storyboard,
    StoryboardFrame,
    StoryboardConfig,
    ContentMetadata,
    VideoGenerationResult
)
from pixelle_video.utils.content_generators import (
    generate_title,
    generate_narrations_from_topic,
    split_narration_script,
    generate_image_prompts,
)


class StandardPipeline(BasePipeline):
    """
    Standard video generation pipeline
    
    Workflow:
    1. Generate/determine title
    2. Generate narrations (from topic or split fixed script)
    3. Generate image prompts for each narration
    4. For each frame:
       - Generate audio (TTS)
       - Generate image
       - Compose frame with template
       - Create video segment
    5. Concatenate all segments
    6. Add BGM (optional)
    
    Supports two modes:
    - "generate": LLM generates narrations from topic
    - "fixed": Use provided script as-is (each line = one narration)
    """
    
    async def __call__(
        self,
        # === Input ===
        text: str,
        
        # === Processing Mode ===
        mode: Literal["generate", "fixed"] = "generate",
        
        # === Optional Title ===
        title: Optional[str] = None,
        
        # === Basic Config ===
        n_scenes: int = 5,  # Only used in generate mode; ignored in fixed mode
        
        # === TTS Parameters ===
        tts_inference_mode: Optional[str] = None,  # "local" or "comfyui"
        tts_voice: Optional[str] = None,  # For local mode: Edge TTS voice ID
        tts_speed: Optional[float] = None,  # Speed multiplier (0.5-2.0)
        tts_workflow: Optional[str] = None,  # For ComfyUI mode: workflow path
        ref_audio: Optional[str] = None,  # For ComfyUI mode: reference audio
        
        # Deprecated (kept for backward compatibility)
        voice_id: Optional[str] = None,
        
        output_path: Optional[str] = None,
        
        # === LLM Parameters ===
        min_narration_words: int = 5,
        max_narration_words: int = 20,
        min_image_prompt_words: int = 30,
        max_image_prompt_words: int = 60,
        
        # === Image Parameters ===
        # Note: image_width and image_height are now auto-determined from template meta tags
        image_workflow: Optional[str] = None,
        
        # === Video Parameters ===
        video_fps: int = 30,
        
        # === Frame Template (determines video size) ===
        frame_template: Optional[str] = None,
        template_params: Optional[Dict[str, Any]] = None,  # Custom template parameters
        
        # === Image Style ===
        prompt_prefix: Optional[str] = None,
        
        # === BGM Parameters ===
        bgm_path: Optional[str] = None,
        bgm_volume: float = 0.2,
        bgm_mode: Literal["once", "loop"] = "loop",
        
        # === Advanced Options ===
        content_metadata: Optional[ContentMetadata] = None,
        progress_callback: Optional[Callable[[ProgressEvent], None]] = None,
    ) -> VideoGenerationResult:
        """
        Generate short video from text input
        
        Args:
            text: Text input (required)
                  - For generate mode: topic/theme (e.g., "如何提高学习效率")
                  - For fixed mode: complete narration script (each line is a narration)
            
            mode: Processing mode (default "generate")
                  - "generate": LLM generates narrations from topic, creates n_scenes
                  - "fixed": Use existing script as-is, each line becomes a narration
                  
                  Note: In fixed mode, n_scenes is ignored (uses actual line count)
            
            title: Video title (optional)
                   - If provided, use it as the video title
                   - If not provided:
                     * generate mode → use text as title
                     * fixed mode → LLM generates title from script
            
            n_scenes: Number of storyboard scenes (default 5)
                      Only effective in generate mode; ignored in fixed mode
            
            voice_id: TTS voice ID (default "[Chinese] zh-CN Yunjian")
            tts_workflow: TTS workflow filename (e.g., "tts_edge.json", None = use default)
            tts_speed: TTS speed multiplier (1.0 = normal, 1.2 = 20% faster, default 1.2)
            ref_audio: Reference audio path for voice cloning (optional)
            output_path: Output video path (auto-generated if None)
            
            min_narration_words: Min narration length (generate mode only)
            max_narration_words: Max narration length (generate mode only)
            min_image_prompt_words: Min image prompt length
            max_image_prompt_words: Max image prompt length
            
            image_workflow: Image workflow filename (e.g., "image_flux.json", None = use default)
                           Note: Image/video size is now auto-determined from template meta tags
            
            video_fps: Video frame rate (default 30)
            
            frame_template: HTML template path with size (None = use default "1080x1920/default.html")
                           Format: "SIZExSIZE/template.html" (e.g., "1080x1920/default.html", "1920x1080/modern.html")
                           Video size is automatically determined from template path
            
            prompt_prefix: Image prompt prefix (overrides config.yaml if provided)
                          e.g., "anime style, vibrant colors" or "" for no prefix
            
            bgm_path: BGM path (filename like "default.mp3", custom path, or None)
            bgm_volume: BGM volume 0.0-1.0 (default 0.2)
            bgm_mode: BGM mode "once" or "loop" (default "loop")
            
            content_metadata: Content metadata (optional, for display)
            progress_callback: Progress callback function(ProgressEvent)
        
        Returns:
            VideoGenerationResult with video path and metadata
        """
        # ========== Step 0: Process text and determine title ==========
        logger.info(f"🚀 Starting StandardPipeline in '{mode}' mode")
        logger.info(f"   Text length: {len(text)} chars")
        
        # Determine final title
        if title:
            final_title = title
            logger.info(f"   Title: '{title}' (user-specified)")
        else:
            self._report_progress(progress_callback, "generating_title", 0.01)
            if mode == "generate":
                final_title = await generate_title(self.llm, text, strategy="auto")
                logger.info(f"   Title: '{final_title}' (auto-generated)")
            else:  # fixed
                final_title = await generate_title(self.llm, text, strategy="llm")
                logger.info(f"   Title: '{final_title}' (LLM-generated)")
        
        # ========== Step 0.5: Create isolated task directory ==========
        from pixelle_video.utils.os_util import (
            create_task_output_dir,
            get_task_final_video_path
        )
        
        task_dir, task_id = create_task_output_dir()
        logger.info(f"📁 Task directory created: {task_dir}")
        logger.info(f"   Task ID: {task_id}")
        
        # Determine final video path
        user_specified_output = None
        if output_path is None:
            output_path = get_task_final_video_path(task_id)
        else:
            user_specified_output = output_path
            output_path = get_task_final_video_path(task_id)
            logger.info(f"   Will copy final video to: {user_specified_output}")
        
        # Determine TTS inference mode and parameters
        # Priority: explicit params > backward compatibility > config defaults
        if tts_inference_mode is None:
            # Check if user provided ComfyUI-specific params
            if tts_workflow is not None or ref_audio is not None:
                tts_inference_mode = "comfyui"
            # Check if user provided old voice_id param (backward compatibility)
            elif voice_id is not None:
                tts_inference_mode = "comfyui"
                if tts_voice is None:
                    tts_voice = voice_id
            else:
                # Use config default
                tts_config = self.core.config.get("comfyui", {}).get("tts", {})
                tts_inference_mode = tts_config.get("inference_mode", "local")
        
        # Set voice_id based on mode for StoryboardConfig
        final_voice_id = None
        if tts_inference_mode == "local":
            final_voice_id = tts_voice or voice_id
        else:  # comfyui
            final_voice_id = voice_id  # For ComfyUI, might be None
        
        # Determine frame template
        # Priority: explicit param > config default > hardcoded default
        if frame_template is None:
            template_config = self.core.config.get("template", {})
            frame_template = template_config.get("default_template", "1080x1920/default.html")
        
        # Read media size from template meta tags
        from pixelle_video.services.frame_html import HTMLFrameGenerator
        from pixelle_video.utils.template_util import resolve_template_path
        
        template_path = resolve_template_path(frame_template)
        temp_generator = HTMLFrameGenerator(template_path)
        image_width, image_height = temp_generator.get_media_size()
        
        logger.info(f"📐 Media size from template: {image_width}x{image_height}")
        
        # Create storyboard config
        config = StoryboardConfig(
            task_id=task_id,
            n_storyboard=n_scenes,
            min_narration_words=min_narration_words,
            max_narration_words=max_narration_words,
            min_image_prompt_words=min_image_prompt_words,
            max_image_prompt_words=max_image_prompt_words,
            video_fps=video_fps,
            tts_inference_mode=tts_inference_mode,
            voice_id=final_voice_id,
            tts_workflow=tts_workflow,
            tts_speed=tts_speed,
            ref_audio=ref_audio,
            image_width=image_width,
            image_height=image_height,
            image_workflow=image_workflow,
            frame_template=frame_template,
            template_params=template_params
        )
        
        # Create storyboard
        storyboard = Storyboard(
            title=final_title,
            config=config,
            content_metadata=content_metadata,
            created_at=datetime.now()
        )
        
        # ========== Step 0.8: Check template requirements ==========
        template_media_type = self._check_template_media_type(config.frame_template)
        if template_media_type == "video":
            logger.info(f"🎬 Template requires video generation")
        elif template_media_type == "image":
            logger.info(f"📸 Template requires image generation")
        else:  # text
            logger.info(f"⚡ Template does not require media - skipping media generation pipeline")
            logger.info(f"   💡 Benefits: Faster generation + Lower cost + No ComfyUI dependency")
        
        try:
            # ========== Step 1: Generate/Split narrations ==========
            if mode == "generate":
                self._report_progress(progress_callback, "generating_narrations", 0.05)
                narrations = await generate_narrations_from_topic(
                    self.llm,
                    topic=text,
                    n_scenes=n_scenes,
                    min_words=min_narration_words,
                    max_words=max_narration_words
                )
                logger.info(f"✅ Generated {len(narrations)} narrations")
            else:  # fixed
                self._report_progress(progress_callback, "splitting_script", 0.05)
                narrations = await split_narration_script(text)
                logger.info(f"✅ Split script into {len(narrations)} segments (by lines)")
                logger.info(f"   Note: n_scenes={n_scenes} is ignored in fixed mode")
            
            # ========== Step 2: Generate media prompts (conditional) ==========
            if template_media_type == "video":
                # Video template: generate video prompts
                self._report_progress(progress_callback, "generating_video_prompts", 0.15)
                
                from pixelle_video.utils.content_generators import generate_video_prompts
                
                # Override prompt_prefix if provided
                original_prefix = None
                if prompt_prefix is not None:
                    image_config = self.core.config.get("comfyui", {}).get("image", {})
                    original_prefix = image_config.get("prompt_prefix")
                    image_config["prompt_prefix"] = prompt_prefix
                    logger.info(f"Using custom prompt_prefix: '{prompt_prefix}'")
                
                try:
                    # Create progress callback wrapper for video prompt generation
                    def video_prompt_progress(completed: int, total: int, message: str):
                        batch_progress = completed / total if total > 0 else 0
                        overall_progress = 0.15 + (batch_progress * 0.15)
                        self._report_progress(
                            progress_callback,
                            "generating_video_prompts",
                            overall_progress,
                            extra_info=message
                        )
                    
                    # Generate base video prompts
                    base_image_prompts = await generate_video_prompts(
                        self.llm,
                        narrations=narrations,
                        min_words=min_image_prompt_words,
                        max_words=max_image_prompt_words,
                        progress_callback=video_prompt_progress
                    )
                    
                    # Apply prompt prefix
                    from pixelle_video.utils.prompt_helper import build_image_prompt
                    image_config = self.core.config.get("comfyui", {}).get("image", {})
                    prompt_prefix_to_use = prompt_prefix if prompt_prefix is not None else image_config.get("prompt_prefix", "")
                    
                    image_prompts = []
                    for base_prompt in base_image_prompts:
                        final_prompt = build_image_prompt(base_prompt, prompt_prefix_to_use)
                        image_prompts.append(final_prompt)
                    
                finally:
                    # Restore original prompt_prefix
                    if original_prefix is not None:
                        image_config["prompt_prefix"] = original_prefix
                
                logger.info(f"✅ Generated {len(image_prompts)} video prompts")
            
            elif template_media_type == "image":
                # Image template: generate image prompts
                self._report_progress(progress_callback, "generating_image_prompts", 0.15)
                
                # Override prompt_prefix if provided
                original_prefix = None
                if prompt_prefix is not None:
                    image_config = self.core.config.get("comfyui", {}).get("image", {})
                    original_prefix = image_config.get("prompt_prefix")
                    image_config["prompt_prefix"] = prompt_prefix
                    logger.info(f"Using custom prompt_prefix: '{prompt_prefix}'")
                
                try:
                    # Create progress callback wrapper for image prompt generation
                    def image_prompt_progress(completed: int, total: int, message: str):
                        batch_progress = completed / total if total > 0 else 0
                        overall_progress = 0.15 + (batch_progress * 0.15)
                        self._report_progress(
                            progress_callback,
                            "generating_image_prompts",
                            overall_progress,
                            extra_info=message
                        )
                    
                    # Generate base image prompts
                    base_image_prompts = await generate_image_prompts(
                        self.llm,
                        narrations=narrations,
                        min_words=min_image_prompt_words,
                        max_words=max_image_prompt_words,
                        progress_callback=image_prompt_progress
                    )
                    
                    # Apply prompt prefix
                    from pixelle_video.utils.prompt_helper import build_image_prompt
                    image_config = self.core.config.get("comfyui", {}).get("image", {})
                    prompt_prefix_to_use = prompt_prefix if prompt_prefix is not None else image_config.get("prompt_prefix", "")
                    
                    image_prompts = []
                    for base_prompt in base_image_prompts:
                        final_prompt = build_image_prompt(base_prompt, prompt_prefix_to_use)
                        image_prompts.append(final_prompt)
                    
                finally:
                    # Restore original prompt_prefix
                    if original_prefix is not None:
                        image_config["prompt_prefix"] = original_prefix
                
                logger.info(f"✅ Generated {len(image_prompts)} image prompts")
            
            else:  # text
                # Text-only template: skip media prompt generation
                image_prompts = [None] * len(narrations)
                self._report_progress(progress_callback, "preparing_frames", 0.15)
                logger.info(f"⚡ Skipped media prompt generation (text-only template)")
                logger.info(f"   💡 Savings: {len(narrations)} LLM calls + {len(narrations)} media generations")
            
            # ========== Step 3: Create frames ==========
            for i, (narration, image_prompt) in enumerate(zip(narrations, image_prompts)):
                frame = StoryboardFrame(
                    index=i,
                    narration=narration,
                    image_prompt=image_prompt,
                    created_at=datetime.now()
                )
                storyboard.frames.append(frame)
            
            # ========== Step 4: Process each frame ==========
            for i, frame in enumerate(storyboard.frames):
                base_progress = 0.2
                frame_range = 0.6
                per_frame_progress = frame_range / len(storyboard.frames)
                
                # Create frame-specific progress callback
                def frame_progress_callback(event: ProgressEvent):
                    overall_progress = base_progress + (per_frame_progress * i) + (per_frame_progress * event.progress)
                    if progress_callback:
                        adjusted_event = ProgressEvent(
                            event_type=event.event_type,
                            progress=overall_progress,
                            frame_current=event.frame_current,
                            frame_total=event.frame_total,
                            step=event.step,
                            action=event.action
                        )
                        progress_callback(adjusted_event)
                
                # Report frame start
                self._report_progress(
                    progress_callback,
                    "processing_frame",
                    base_progress + (per_frame_progress * i),
                    frame_current=i+1,
                    frame_total=len(storyboard.frames)
                )
                
                processed_frame = await self.core.frame_processor(
                    frame=frame,
                    storyboard=storyboard,
                    config=config,
                    total_frames=len(storyboard.frames),
                    progress_callback=frame_progress_callback
                )
                storyboard.total_duration += processed_frame.duration
                logger.info(f"✅ Frame {i+1} completed ({processed_frame.duration:.2f}s)")
            
            # ========== Step 5: Concatenate videos ==========
            self._report_progress(progress_callback, "concatenating", 0.85)
            segment_paths = [frame.video_segment_path for frame in storyboard.frames]
            
            from pixelle_video.services.video import VideoService
            video_service = VideoService()
            
            final_video_path = video_service.concat_videos(
                videos=segment_paths,
                output=output_path,
                bgm_path=bgm_path,
                bgm_volume=bgm_volume,
                bgm_mode=bgm_mode
            )
            
            storyboard.final_video_path = final_video_path
            storyboard.completed_at = datetime.now()
            
            # Copy to user-specified path if provided
            if user_specified_output:
                import shutil
                Path(user_specified_output).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(final_video_path, user_specified_output)
                logger.info(f"📹 Final video copied to: {user_specified_output}")
                final_video_path = user_specified_output
                storyboard.final_video_path = user_specified_output
            
            logger.success(f"🎬 Video generation completed: {final_video_path}")
            
            # ========== Step 6: Create result ==========
            self._report_progress(progress_callback, "completed", 1.0)
            
            video_path_obj = Path(final_video_path)
            file_size = video_path_obj.stat().st_size
            
            result = VideoGenerationResult(
                video_path=final_video_path,
                storyboard=storyboard,
                duration=storyboard.total_duration,
                file_size=file_size
            )
            
            logger.info(f"✅ Generated video: {final_video_path}")
            logger.info(f"   Duration: {storyboard.total_duration:.2f}s")
            logger.info(f"   Size: {file_size / (1024*1024):.2f} MB")
            logger.info(f"   Frames: {len(storyboard.frames)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Video generation failed: {e}")
            raise
    
    def _check_template_media_type(self, frame_template: str) -> str:
        """
        Check template media type requirement
        
        This is checked at pipeline level to avoid unnecessary:
        - LLM calls (generating media prompts)
        - Media generation API calls
        - ComfyUI dependency
        
        Template naming rules:
        - video_*.html: Video template (returns "video")
        - Other templates with {{image}}: Image template (returns "image")
        - Other templates without {{image}}: Text-only template (returns "text")
        
        Args:
            frame_template: Template path (e.g., "1080x1920/default.html" or "1080x1920/video_default.html")
        
        Returns:
            "video", "image", or "text"
        """
        from pixelle_video.services.frame_html import HTMLFrameGenerator
        from pixelle_video.utils.template_util import resolve_template_path
        
        # Check if template name starts with video_
        template_name = Path(frame_template).name
        if template_name.startswith("video_"):
            logger.debug(f"Template '{frame_template}' is video template (video_ prefix)")
            return "video"
        
        # Check if template contains {{image}}
        template_path = resolve_template_path(frame_template)
        generator = HTMLFrameGenerator(template_path)
        
        requires_image = generator.requires_image()
        if requires_image:
            logger.debug(f"Template '{frame_template}' is image template (has {{image}})")
            return "image"
        else:
            logger.debug(f"Template '{frame_template}' is text-only template")
            return "text"

