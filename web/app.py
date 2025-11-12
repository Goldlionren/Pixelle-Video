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
Pixelle-Video Web UI

A simple web interface for generating short videos from content.
"""

import sys
from pathlib import Path

# Add project root to sys.path for module imports
# This ensures imports work correctly in both development and packaged environments
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import asyncio
import base64
import os

import streamlit as st
from loguru import logger

# Import i18n and config manager
from web.i18n import load_locales, set_language, tr, get_available_languages, get_language
from pixelle_video.config import config_manager
from pixelle_video.models.progress import ProgressEvent

# Setup page config (must be first)
st.set_page_config(
    page_title="Pixelle-Video - AI Video Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================================
# Async Helper
# ============================================================================

def run_async(coro):
    """Run async coroutine in sync context"""
    return asyncio.run(coro)


def safe_rerun():
    """Safe rerun that works with both old and new Streamlit versions"""
    if hasattr(st, 'rerun'):
        st.rerun()
    else:
        st.experimental_rerun()


# ============================================================================
# Configuration & i18n Initialization
# ============================================================================

# Config manager is already a global singleton, use it directly


def init_i18n():
    """Initialize internationalization"""
    # Locales are already loaded and system language detected on import
    # Get language from session state or use auto-detected system language
    if "language" not in st.session_state:
        st.session_state.language = get_language()  # Use auto-detected language
    
    # Set current language
    set_language(st.session_state.language)


# ============================================================================
# Initialize Pixelle-Video
# ============================================================================

def get_pixelle_video():
    """Get initialized Pixelle-Video instance (no caching - always fresh)"""
    from pixelle_video.service import PixelleVideoCore
    
    logger.info("Initializing Pixelle-Video...")
    pixelle_video = PixelleVideoCore()
    run_async(pixelle_video.initialize())
    logger.info("Pixelle-Video initialized")
    
    return pixelle_video


# ============================================================================
# Session State
# ============================================================================

def init_session_state():
    """Initialize session state variables"""
    if "language" not in st.session_state:
        # Use auto-detected system language
        st.session_state.language = get_language()


# ============================================================================
# System Configuration (Required)
# ============================================================================

def render_advanced_settings():
    """Render system configuration (required) with 2-column layout"""
    # Check if system is configured
    is_configured = config_manager.validate()
    
    # Expand if not configured, collapse if configured
    with st.expander(tr("settings.title"), expanded=not is_configured):
        # 2-column layout: LLM | ComfyUI
        llm_col, comfyui_col = st.columns(2)
        
        # ====================================================================
        # Column 1: LLM Settings
        # ====================================================================
        with llm_col:
            with st.container(border=True):
                st.markdown(f"**{tr('settings.llm.title')}**")
                
                # Quick preset selection
                from pixelle_video.llm_presets import get_preset_names, get_preset, find_preset_by_base_url_and_model
                
                # Custom at the end
                preset_names = get_preset_names() + ["Custom"]
                
                # Get current config
                current_llm = config_manager.get_llm_config()
                
                # Auto-detect which preset matches current config
                current_preset = find_preset_by_base_url_and_model(
                    current_llm["base_url"], 
                    current_llm["model"]
                )
                
                # Determine default index based on current config
                if current_preset:
                    # Current config matches a preset
                    default_index = preset_names.index(current_preset)
                else:
                    # Current config doesn't match any preset -> Custom
                    default_index = len(preset_names) - 1
                
                selected_preset = st.selectbox(
                    tr("settings.llm.quick_select"),
                    options=preset_names,
                    index=default_index,
                    help=tr("settings.llm.quick_select_help"),
                    key="llm_preset_select"
                )
                
                # Auto-fill based on selected preset
                if selected_preset != "Custom":
                    # Preset selected
                    preset_config = get_preset(selected_preset)
                    
                    # If user switched to a different preset (not current one), clear API key
                    # If it's the same as current config, keep API key
                    if selected_preset == current_preset:
                        # Same preset as saved config: keep API key
                        default_api_key = current_llm["api_key"]
                    else:
                        # Different preset: clear API key
                        default_api_key = ""
                    
                    default_base_url = preset_config.get("base_url", "")
                    default_model = preset_config.get("model", "")
                    
                    # Show API key URL if available
                    if preset_config.get("api_key_url"):
                        st.markdown(f"🔑 [{tr('settings.llm.get_api_key')}]({preset_config['api_key_url']})")
                else:
                    # Custom: show current saved config (if any)
                    default_api_key = current_llm["api_key"]
                    default_base_url = current_llm["base_url"]
                    default_model = current_llm["model"]
                
                st.markdown("---")
                
                # API Key (use unique key to force refresh when switching preset)
                llm_api_key = st.text_input(
                    f"{tr('settings.llm.api_key')} *",
                    value=default_api_key,
                    type="password",
                    help=tr("settings.llm.api_key_help"),
                    key=f"llm_api_key_input_{selected_preset}"
                )
                
                # Base URL (use unique key based on preset to force refresh)
                llm_base_url = st.text_input(
                    f"{tr('settings.llm.base_url')} *",
                    value=default_base_url,
                    help=tr("settings.llm.base_url_help"),
                    key=f"llm_base_url_input_{selected_preset}"
                )
                
                # Model (use unique key based on preset to force refresh)
                llm_model = st.text_input(
                    f"{tr('settings.llm.model')} *",
                    value=default_model,
                    help=tr("settings.llm.model_help"),
                    key=f"llm_model_input_{selected_preset}"
                )
        
        # ====================================================================
        # Column 2: ComfyUI Settings
        # ====================================================================
        with comfyui_col:
            with st.container(border=True):
                st.markdown(f"**{tr('settings.comfyui.title')}**")
                
                # Get current configuration
                comfyui_config = config_manager.get_comfyui_config()
                
                # Local/Self-hosted ComfyUI configuration
                st.markdown(f"**{tr('settings.comfyui.local_title')}**")
                comfyui_url = st.text_input(
                    tr("settings.comfyui.comfyui_url"),
                    value=comfyui_config.get("comfyui_url", "http://127.0.0.1:8188"),
                    help=tr("settings.comfyui.comfyui_url_help"),
                    key="comfyui_url_input"
                )
                
                # Test connection button
                if st.button(tr("btn.test_connection"), key="test_comfyui", use_container_width=True):
                    try:
                        import requests
                        response = requests.get(f"{comfyui_url}/system_stats", timeout=5)
                        if response.status_code == 200:
                            st.success(tr("status.connection_success"))
                        else:
                            st.error(tr("status.connection_failed"))
                    except Exception as e:
                        st.error(f"{tr('status.connection_failed')}: {str(e)}")
                
                st.markdown("---")
                
                # RunningHub cloud configuration
                st.markdown(f"**{tr('settings.comfyui.cloud_title')}**")
                runninghub_api_key = st.text_input(
                    tr("settings.comfyui.runninghub_api_key"),
                    value=comfyui_config.get("runninghub_api_key", ""),
                    type="password",
                    help=tr("settings.comfyui.runninghub_api_key_help"),
                    key="runninghub_api_key_input"
                )
                st.caption(
                    f"{tr('settings.comfyui.runninghub_hint')} "
                    f"[{tr('settings.comfyui.runninghub_get_api_key')}]"
                    f"(https://www.runninghub{'.cn' if get_language() == 'zh_CN' else '.ai'}/?inviteCode=bozpdlbj)"
                )
        
        # ====================================================================
        # Action Buttons (full width at bottom)
        # ====================================================================
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(tr("btn.save_config"), use_container_width=True, key="save_config_btn"):
                try:
                    # Save LLM configuration
                    if llm_api_key and llm_base_url and llm_model:
                        config_manager.set_llm_config(llm_api_key, llm_base_url, llm_model)
                    
                    # Save ComfyUI configuration
                    config_manager.set_comfyui_config(
                        comfyui_url=comfyui_url if comfyui_url else None,
                        runninghub_api_key=runninghub_api_key if runninghub_api_key else None
                    )
                    
                    # Save to file
                    config_manager.save()
                    
                    st.success(tr("status.config_saved"))
                    safe_rerun()
                except Exception as e:
                    st.error(f"{tr('status.save_failed')}: {str(e)}")
        
        with col2:
            if st.button(tr("btn.reset_config"), use_container_width=True, key="reset_config_btn"):
                # Reset to default
                from pixelle_video.config.schema import PixelleVideoConfig
                config_manager.config = PixelleVideoConfig()
                config_manager.save()
                st.success(tr("status.config_reset"))
                safe_rerun()


# ============================================================================
# Language Selector
# ============================================================================

def render_language_selector():
    """Render language selector at the top"""
    languages = get_available_languages()
    lang_options = [f"{code} - {name}" for code, name in languages.items()]
    
    current_lang = st.session_state.get("language", "zh_CN")
    current_index = list(languages.keys()).index(current_lang) if current_lang in languages else 0
    
    selected = st.selectbox(
        tr("language.select"),
        options=lang_options,
        index=current_index,
        label_visibility="collapsed"
    )
    
    selected_code = selected.split(" - ")[0]
    if selected_code != current_lang:
        st.session_state.language = selected_code
        set_language(selected_code)
        safe_rerun()


# ============================================================================
# Main UI
# ============================================================================

def main():
    # Initialize
    init_session_state()
    init_i18n()
    
    # Top bar: Title + Language selector
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"<h3>{tr('app.title')}</h3>", unsafe_allow_html=True)
    with col2:
        render_language_selector()
    
    # Initialize Pixelle-Video
    pixelle_video = get_pixelle_video()
    
    # ========================================================================
    # System Configuration (Required)
    # Auto-expands if not configured, collapses if configured
    # ========================================================================
    render_advanced_settings()
    
    # Three-column layout
    left_col, middle_col, right_col = st.columns([1, 1, 1])
    
    # ========================================================================
    # Left Column: Content Input
    # ========================================================================
    with left_col:
        with st.container(border=True):
            st.markdown(f"**{tr('section.content_input')}**")
            
            # Processing mode selection
            mode = st.radio(
                "Processing Mode",
                ["generate", "fixed"],
                horizontal=True,
                format_func=lambda x: tr(f"mode.{x}"),
                label_visibility="collapsed"
            )
            
            # Text input (unified for both modes)
            text_placeholder = tr("input.topic_placeholder") if mode == "generate" else tr("input.content_placeholder")
            text_height = 120 if mode == "generate" else 200
            text_help = tr("input.text_help_generate") if mode == "generate" else tr("input.text_help_fixed")
            
            text = st.text_area(
                tr("input.text"),
                placeholder=text_placeholder,
                height=text_height,
                help=text_help
            )
            
            # Title input (optional for both modes)
            title = st.text_input(
                tr("input.title"),
                placeholder=tr("input.title_placeholder"),
                help=tr("input.title_help")
            )
            
            # Number of scenes (only show in generate mode)
            if mode == "generate":
                n_scenes = st.slider(
                    tr("video.frames"),
                    min_value=3,
                    max_value=30,
                    value=5,
                    help=tr("video.frames_help"),
                    label_visibility="collapsed"
                )
                st.caption(tr("video.frames_label", n=n_scenes))
            else:
                # Fixed mode: n_scenes is ignored, set default value
                n_scenes = 5
                st.info(tr("video.frames_fixed_mode_hint"))
        
        # ====================================================================
        # BGM Section
        # ====================================================================
        with st.container(border=True):
            st.markdown(f"**{tr('section.bgm')}**")
            
            with st.expander(tr("help.feature_description"), expanded=False):
                st.markdown(f"**{tr('help.what')}**")
                st.markdown(tr("bgm.what"))
                st.markdown(f"**{tr('help.how')}**")
                st.markdown(tr("bgm.how"))
            
            # Dynamically scan bgm folder for music files (merged from bgm/ and data/bgm/)
            from pixelle_video.utils.os_util import list_resource_files
            
            try:
                all_files = list_resource_files("bgm")
                # Filter to audio files only
                audio_extensions = ('.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg')
                bgm_files = sorted([f for f in all_files if f.lower().endswith(audio_extensions)])
            except Exception as e:
                st.warning(f"Failed to load BGM files: {e}")
                bgm_files = []
            
            # Add special "None" option
            bgm_options = [tr("bgm.none")] + bgm_files
            
            # Default to "default.mp3" if exists, otherwise first option
            default_index = 0
            if "default.mp3" in bgm_files:
                default_index = bgm_options.index("default.mp3")
            
            bgm_choice = st.selectbox(
                "BGM",
                bgm_options,
                index=default_index,
                label_visibility="collapsed"
            )
            
            # BGM preview button (only if BGM is not "None")
            if bgm_choice != tr("bgm.none"):
                if st.button(tr("bgm.preview"), key="preview_bgm", use_container_width=True):
                    from pixelle_video.utils.os_util import get_resource_path, resource_exists
                    try:
                        if resource_exists("bgm", bgm_choice):
                            bgm_file_path = get_resource_path("bgm", bgm_choice)
                            st.audio(bgm_file_path)
                        else:
                            st.error(tr("bgm.preview_failed", file=bgm_choice))
                    except Exception as e:
                        st.error(f"{tr('bgm.preview_failed', file=bgm_choice)}: {e}")
            
            # Use full filename for bgm_path (including extension)
            bgm_path = None if bgm_choice == tr("bgm.none") else bgm_choice
    
    # ========================================================================
    # Middle Column: TTS, Image Settings & Template
    # ========================================================================
    with middle_col:
        # ====================================================================
        # TTS Section (moved from left column)
        # ====================================================================
        with st.container(border=True):
            st.markdown(f"**{tr('section.tts')}**")
            
            with st.expander(tr("help.feature_description"), expanded=False):
                st.markdown(f"**{tr('help.what')}**")
                st.markdown(tr("tts.what"))
                st.markdown(f"**{tr('help.how')}**")
                st.markdown(tr("tts.how"))
            
            # Get TTS config
            comfyui_config = config_manager.get_comfyui_config()
            tts_config = comfyui_config["tts"]
            
            # Inference mode selection
            tts_mode = st.radio(
                tr("tts.inference_mode"),
                ["local", "comfyui"],
                horizontal=True,
                format_func=lambda x: tr(f"tts.mode.{x}"),
                index=0 if tts_config.get("inference_mode", "local") == "local" else 1,
                key="tts_inference_mode"
            )
            
            # Show hint based on mode
            if tts_mode == "local":
                st.caption(tr("tts.mode.local_hint"))
            else:
                st.caption(tr("tts.mode.comfyui_hint"))
            
            # ================================================================
            # Local Mode UI
            # ================================================================
            if tts_mode == "local":
                # Import voice configuration
                from pixelle_video.tts_voices import EDGE_TTS_VOICES, get_voice_display_name
                
                # Get saved voice from config
                local_config = tts_config.get("local", {})
                saved_voice = local_config.get("voice", "zh-CN-YunjianNeural")
                saved_speed = local_config.get("speed", 1.2)
                
                # Build voice options with i18n
                voice_options = []
                voice_ids = []
                default_voice_index = 0
                
                for idx, voice_config in enumerate(EDGE_TTS_VOICES):
                    voice_id = voice_config["id"]
                    display_name = get_voice_display_name(voice_id, tr, get_language())
                    voice_options.append(display_name)
                    voice_ids.append(voice_id)
                    
                    # Set default index if matches saved voice
                    if voice_id == saved_voice:
                        default_voice_index = idx
                
                # Two-column layout: Voice | Speed
                voice_col, speed_col = st.columns([1, 1])
                
                with voice_col:
                    # Voice selector
                    selected_voice_display = st.selectbox(
                        tr("tts.voice_selector"),
                        voice_options,
                        index=default_voice_index,
                        key="tts_local_voice"
                    )
                    
                    # Get actual voice ID
                    selected_voice_index = voice_options.index(selected_voice_display)
                    selected_voice = voice_ids[selected_voice_index]
                
                with speed_col:
                    # Speed slider
                    tts_speed = st.slider(
                        tr("tts.speed"),
                        min_value=0.5,
                        max_value=2.0,
                        value=saved_speed,
                        step=0.1,
                        format="%.1fx",
                        key="tts_local_speed"
                    )
                    st.caption(tr("tts.speed_label", speed=f"{tts_speed:.1f}"))
                
                # Variables for video generation
                tts_workflow_key = None
                ref_audio_path = None
            
            # ================================================================
            # ComfyUI Mode UI
            # ================================================================
            else:  # comfyui mode
                # Get available TTS workflows
                tts_workflows = pixelle_video.tts.list_workflows()
                
                # Build options for selectbox
                tts_workflow_options = [wf["display_name"] for wf in tts_workflows]
                tts_workflow_keys = [wf["key"] for wf in tts_workflows]
                
                # Default to saved workflow if exists
                default_tts_index = 0
                saved_tts_workflow = tts_config.get("comfyui", {}).get("default_workflow")
                if saved_tts_workflow and saved_tts_workflow in tts_workflow_keys:
                    default_tts_index = tts_workflow_keys.index(saved_tts_workflow)
                
                tts_workflow_display = st.selectbox(
                    "TTS Workflow",
                    tts_workflow_options if tts_workflow_options else ["No TTS workflows found"],
                    index=default_tts_index,
                    label_visibility="collapsed",
                    key="tts_workflow_select"
                )
                
                # Get the actual workflow key
                if tts_workflow_options:
                    tts_selected_index = tts_workflow_options.index(tts_workflow_display)
                    tts_workflow_key = tts_workflow_keys[tts_selected_index]
                else:
                    tts_workflow_key = "selfhost/tts_edge.json"  # fallback
                
                # Reference audio upload (optional, for voice cloning)
                ref_audio_file = st.file_uploader(
                    tr("tts.ref_audio"),
                    type=["mp3", "wav", "flac", "m4a", "aac", "ogg"],
                    help=tr("tts.ref_audio_help"),
                    key="ref_audio_upload"
                )
                
                # Save uploaded ref_audio to temp file if provided
                ref_audio_path = None
                if ref_audio_file is not None:
                    # Audio preview player (directly play uploaded file)
                    st.audio(ref_audio_file)
                    
                    # Save to temp directory
                    temp_dir = Path("temp")
                    temp_dir.mkdir(exist_ok=True)
                    ref_audio_path = temp_dir / f"ref_audio_{ref_audio_file.name}"
                    with open(ref_audio_path, "wb") as f:
                        f.write(ref_audio_file.getbuffer())
                
                # Variables for video generation
                selected_voice = None
                tts_speed = None
            
            # ================================================================
            # TTS Preview (works for both modes)
            # ================================================================
            with st.expander(tr("tts.preview_title"), expanded=False):
                # Preview text input
                preview_text = st.text_input(
                    tr("tts.preview_text"),
                    value="大家好，这是一段测试语音。",
                    placeholder=tr("tts.preview_text_placeholder"),
                    key="tts_preview_text"
                )
                
                # Preview button
                if st.button(tr("tts.preview_button"), key="preview_tts", use_container_width=True):
                    with st.spinner(tr("tts.previewing")):
                        try:
                            # Build TTS params based on mode
                            tts_params = {
                                "text": preview_text,
                                "inference_mode": tts_mode
                            }
                            
                            if tts_mode == "local":
                                tts_params["voice"] = selected_voice
                                tts_params["speed"] = tts_speed
                            else:  # comfyui
                                tts_params["workflow"] = tts_workflow_key
                                if ref_audio_path:
                                    tts_params["ref_audio"] = str(ref_audio_path)
                            
                            audio_path = run_async(pixelle_video.tts(**tts_params))
                            
                            # Play the audio
                            if audio_path:
                                st.success(tr("tts.preview_success"))
                                if os.path.exists(audio_path):
                                    st.audio(audio_path, format="audio/mp3")
                                elif audio_path.startswith('http'):
                                    st.audio(audio_path)
                                else:
                                    st.error("Failed to generate preview audio")
                                
                                # Show file path
                                st.caption(f"📁 {audio_path}")
                            else:
                                st.error("Failed to generate preview audio")
                        except Exception as e:
                            st.error(tr("tts.preview_failed", error=str(e)))
                            logger.exception(e)
        
        # ====================================================================
        # Storyboard Template Section
        # ====================================================================
        with st.container(border=True):
            st.markdown(f"**{tr('section.template')}**")
            
            with st.expander(tr("help.feature_description"), expanded=False):
                st.markdown(f"**{tr('help.what')}**")
                st.markdown(tr("template.what"))
                st.markdown(f"**{tr('help.how')}**")
                st.markdown(tr("template.how"))
            
            # Template preview link (based on language)
            current_lang = get_language()
            if current_lang == "zh_CN":
                template_docs_url = "https://aidc-ai.github.io/Pixelle-Video/zh/user-guide/templates/#_3"
            else:
                template_docs_url = "https://aidc-ai.github.io/Pixelle-Video/user-guide/templates/#built-in-template-preview"
            
            st.markdown(f"🔗 [{tr('template.preview_link')}]({template_docs_url})")
            
            # Import template utilities
            from pixelle_video.utils.template_util import get_templates_grouped_by_size
            
            # Get templates grouped by size
            grouped_templates = get_templates_grouped_by_size()
            
            if not grouped_templates:
                st.error("No templates found. Please ensure templates are in templates/ directory with proper structure (e.g., templates/1080x1920/default.html).")
                st.stop()
            
            # Build display options with group separators
            ORIENTATION_I18N = {
                'portrait': tr('orientation.portrait'),
                'landscape': tr('orientation.landscape'),
                'square': tr('orientation.square')
            }
            
            display_options = []
            template_paths_ordered = []  # Use ordered list instead of dict to avoid key conflicts
            default_index = 0
            current_index = 0
            
            # Get default template from config
            template_config = pixelle_video.config.get("template", {})
            config_default_template = template_config.get("default_template", "1080x1920/default.html")
            
            for size, templates in grouped_templates.items():
                if not templates:
                    continue
                
                # Get orientation from first template in group
                orientation = ORIENTATION_I18N.get(
                    templates[0].display_info.orientation, 
                    templates[0].display_info.orientation
                )
                width = templates[0].display_info.width
                height = templates[0].display_info.height
                
                # Add group separator
                separator = f"─── {orientation} {width}×{height} ───"
                display_options.append(separator)
                template_paths_ordered.append(None)  # Separator has no template path
                current_index += 1
                
                # Add templates in this group
                for t in templates:
                    display_name = f"  {t.display_info.name}"
                    display_options.append(display_name)
                    template_paths_ordered.append(t.template_path)  # Add to ordered list
                    
                    # Set default based on config (priority: config > first default.html in portrait)
                    if t.template_path == config_default_template:
                        default_index = current_index
                    elif default_index == 0 and "default.html" in t.display_info.name and t.display_info.orientation == 'portrait':
                        default_index = current_index
                    
                    current_index += 1
            
            # Dropdown with grouped display
            # Create unique display strings by appending hidden unique identifier
            # This ensures Streamlit doesn't confuse templates with same name in different groups
            unique_display_options = []
            for i, option in enumerate(display_options):
                # Add zero-width space characters as unique identifier (invisible to users)
                unique_option = option + ("\u200B" * i)  # \u200B is zero-width space
                unique_display_options.append(unique_option)
            
            selected_unique_option = st.selectbox(
                tr("template.select"),
                unique_display_options,
                index=default_index,
                label_visibility="collapsed",
                help=tr("template.select_help")
            )
            
            # Get index from selected unique option
            selected_index = unique_display_options.index(selected_unique_option)
            
            # Check if separator is selected (shouldn't happen, but handle it)
            if display_options[selected_index].startswith("───"):
                st.warning(tr("template.separator_selected"))
                st.stop()
            
            # Get full template path directly by index
            frame_template = template_paths_ordered[selected_index]
            
            # Display video size from template
            from pixelle_video.utils.template_util import parse_template_size
            video_width, video_height = parse_template_size(frame_template)
            st.caption(tr("template.video_size_info", width=video_width, height=video_height))
            
            # Custom template parameters (for video generation)
            from pixelle_video.services.frame_html import HTMLFrameGenerator
            # Resolve template path to support both data/templates/ and templates/
            from pixelle_video.utils.template_util import resolve_template_path
            template_path_for_params = resolve_template_path(frame_template)
            generator_for_params = HTMLFrameGenerator(template_path_for_params)
            custom_params_for_video = generator_for_params.parse_template_parameters()
            
            # Get media size from template (for image/video generation)
            media_width, media_height = generator_for_params.get_media_size()
            st.session_state['template_media_width'] = media_width
            st.session_state['template_media_height'] = media_height
            
            # Detect template media type
            from pathlib import Path
            template_name = Path(frame_template).name
            
            if template_name.startswith("video_"):
                # Video template
                template_media_type = "video"
                template_requires_media = True
            elif generator_for_params.requires_image():
                # Image template
                template_media_type = "image"
                template_requires_media = True
            else:
                # Text-only template
                template_media_type = "text"
                template_requires_media = False
            
            # Store in session state for workflow filtering
            st.session_state['template_media_type'] = template_media_type
            st.session_state['template_requires_media'] = template_requires_media
            
            # Backward compatibility
            st.session_state['template_requires_image'] = (template_media_type == "image")
            
            custom_values_for_video = {}
            if custom_params_for_video:
                st.markdown("📝 " + tr("template.custom_parameters"))
                
                # Render custom parameter inputs in 2 columns
                video_custom_col1, video_custom_col2 = st.columns(2)
                
                param_items = list(custom_params_for_video.items())
                mid_point = (len(param_items) + 1) // 2
                
                # Left column parameters
                with video_custom_col1:
                    for param_name, config in param_items[:mid_point]:
                        param_type = config['type']
                        default = config['default']
                        label = config['label']
                        
                        if param_type == 'text':
                            custom_values_for_video[param_name] = st.text_input(
                                label,
                                value=default,
                                key=f"video_custom_{param_name}"
                            )
                        elif param_type == 'number':
                            custom_values_for_video[param_name] = st.number_input(
                                label,
                                value=default,
                                key=f"video_custom_{param_name}"
                            )
                        elif param_type == 'color':
                            custom_values_for_video[param_name] = st.color_picker(
                                label,
                                value=default,
                                key=f"video_custom_{param_name}"
                            )
                        elif param_type == 'bool':
                            custom_values_for_video[param_name] = st.checkbox(
                                label,
                                value=default,
                                key=f"video_custom_{param_name}"
                            )
                
                # Right column parameters
                with video_custom_col2:
                    for param_name, config in param_items[mid_point:]:
                        param_type = config['type']
                        default = config['default']
                        label = config['label']
                        
                        if param_type == 'text':
                            custom_values_for_video[param_name] = st.text_input(
                                label,
                                value=default,
                                key=f"video_custom_{param_name}"
                            )
                        elif param_type == 'number':
                            custom_values_for_video[param_name] = st.number_input(
                                label,
                                value=default,
                                key=f"video_custom_{param_name}"
                            )
                        elif param_type == 'color':
                            custom_values_for_video[param_name] = st.color_picker(
                                label,
                                value=default,
                                key=f"video_custom_{param_name}"
                            )
                        elif param_type == 'bool':
                            custom_values_for_video[param_name] = st.checkbox(
                                label,
                                value=default,
                                key=f"video_custom_{param_name}"
                            )
            
            # Template preview expander
            with st.expander(tr("template.preview_title"), expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    preview_title = st.text_input(
                        tr("template.preview_param_title"), 
                        value=tr("template.preview_default_title"),
                        key="preview_title"
                    )
                    preview_image = st.text_input(
                        tr("template.preview_param_image"), 
                        value="resources/example.png",
                        help=tr("template.preview_image_help"),
                        key="preview_image"
                    )
                
                with col2:
                    preview_text = st.text_area(
                        tr("template.preview_param_text"), 
                        value=tr("template.preview_default_text"),
                        height=100,
                        key="preview_text"
                    )
                
                # Info: Size is auto-determined from template
                from pixelle_video.utils.template_util import parse_template_size, resolve_template_path
                template_width, template_height = parse_template_size(resolve_template_path(frame_template))
                st.info(f"📐 {tr('template.size_info')}: {template_width} × {template_height}")
                
                # Preview button
                if st.button(tr("template.preview_button"), key="btn_preview_template", use_container_width=True):
                    with st.spinner(tr("template.preview_generating")):
                        try:
                            from pixelle_video.services.frame_html import HTMLFrameGenerator

                            # Use the currently selected template (size is auto-parsed)
                            from pixelle_video.utils.template_util import resolve_template_path
                            template_path = resolve_template_path(frame_template)
                            generator = HTMLFrameGenerator(template_path)
                            
                            # Generate preview (use custom parameters from video generation section)
                            preview_path = run_async(generator.generate_frame(
                                title=preview_title,
                                text=preview_text,
                                image=preview_image,
                                ext=custom_values_for_video if custom_values_for_video else None
                            ))
                            
                            # Display preview
                            if preview_path:
                                st.success(tr("template.preview_success"))
                                st.image(
                                    preview_path, 
                                    caption=tr("template.preview_caption", template=frame_template),
                                )
                                
                                # Show file path
                                st.caption(f"📁 {preview_path}")
                            else:
                                st.error("Failed to generate preview")
                                
                        except Exception as e:
                            st.error(tr("template.preview_failed", error=str(e)))
                            logger.exception(e)
        
        # ====================================================================
        # Media Generation Section (conditional based on template)
        # ====================================================================
        # Check if current template requires media generation
        template_media_type = st.session_state.get('template_media_type', 'image')
        template_requires_media = st.session_state.get('template_requires_media', True)
        
        if template_requires_media:
            # Template requires media - show Media Generation Section
            with st.container(border=True):
                # Dynamic section title based on template type
                if template_media_type == "video":
                    section_title = tr('section.video')
                else:
                    section_title = tr('section.image')
                
                st.markdown(f"**{section_title}**")
            
                # 1. ComfyUI Workflow selection
                with st.expander(tr("help.feature_description"), expanded=False):
                    st.markdown(f"**{tr('help.what')}**")
                    if template_media_type == "video":
                        st.markdown(tr('style.video_workflow_what'))
                    else:
                        st.markdown(tr("style.workflow_what"))
                    st.markdown(f"**{tr('help.how')}**")
                    if template_media_type == "video":
                        st.markdown(tr('style.video_workflow_how'))
                    else:
                        st.markdown(tr("style.workflow_how"))
                    st.markdown(f"**{tr('help.note')}**")
                    if template_media_type == "video":
                        st.markdown(tr('style.video_size_note'))
                    else:
                        st.markdown(tr("style.image_size_note"))
            
                # Get available workflows and filter by template type
                all_workflows = pixelle_video.media.list_workflows()
                
                # Filter workflows based on template media type
                if template_media_type == "video":
                    # Only show video_ workflows
                    workflows = [wf for wf in all_workflows if "video_" in wf["key"].lower()]
                else:
                    # Only show image_ workflows (exclude video_)
                    workflows = [wf for wf in all_workflows if "video_" not in wf["key"].lower()]
            
                # Build options for selectbox
                # Display: "image_flux.json - Runninghub"
                # Value: "runninghub/image_flux.json"
                workflow_options = [wf["display_name"] for wf in workflows]
                workflow_keys = [wf["key"] for wf in workflows]
            
                # Default to first option (should be runninghub by sorting)
                default_workflow_index = 0
            
                # If user has a saved preference in config, try to match it
                comfyui_config = config_manager.get_comfyui_config()
                saved_workflow = comfyui_config["image"]["default_workflow"]
                if saved_workflow and saved_workflow in workflow_keys:
                    default_workflow_index = workflow_keys.index(saved_workflow)
            
                workflow_display = st.selectbox(
                    "Workflow",
                    workflow_options if workflow_options else ["No workflows found"],
                    index=default_workflow_index,
                    label_visibility="collapsed",
                    key="image_workflow_select"
                )
            
                # Get the actual workflow key (e.g., "runninghub/image_flux.json")
                if workflow_options:
                    workflow_selected_index = workflow_options.index(workflow_display)
                    workflow_key = workflow_keys[workflow_selected_index]
                else:
                    workflow_key = "runninghub/image_flux.json"  # fallback
            
                # Get media size from template
                image_width = st.session_state.get('template_media_width', 1024)
                image_height = st.session_state.get('template_media_height', 1024)
                
                # Display media size info (read-only)
                if template_media_type == "video":
                    size_info_text = tr('style.video_size_info', width=image_width, height=image_height)
                else:
                    size_info_text = tr('style.image_size_info', width=image_width, height=image_height)
                st.info(f"📐 {size_info_text}")
            
                # Prompt prefix input
                # Get current prompt_prefix from config
                current_prefix = comfyui_config["image"]["prompt_prefix"]
            
                # Prompt prefix input (temporary, not saved to config)
                prompt_prefix = st.text_area(
                    tr('style.prompt_prefix'),
                    value=current_prefix,
                    placeholder=tr("style.prompt_prefix_placeholder"),
                    height=80,
                    label_visibility="visible",
                    help=tr("style.prompt_prefix_help")
                )
            
                # Media preview expander
                preview_title = tr("style.video_preview_title") if template_media_type == "video" else tr("style.preview_title")
                with st.expander(preview_title, expanded=False):
                    # Test prompt input
                    if template_media_type == "video":
                        test_prompt_label = tr("style.test_video_prompt")
                        test_prompt_value = "a dog running in the park"
                    else:
                        test_prompt_label = tr("style.test_prompt")
                        test_prompt_value = "a dog"
                    
                    test_prompt = st.text_input(
                        test_prompt_label,
                        value=test_prompt_value,
                        help=tr("style.test_prompt_help"),
                        key="style_test_prompt"
                    )
                
                    # Preview button
                    preview_button_label = tr("style.video_preview") if template_media_type == "video" else tr("style.preview")
                    if st.button(preview_button_label, key="preview_style", use_container_width=True):
                        previewing_text = tr("style.video_previewing") if template_media_type == "video" else tr("style.previewing")
                        with st.spinner(previewing_text):
                            try:
                                from pixelle_video.utils.prompt_helper import build_image_prompt
                            
                                # Build final prompt with prefix
                                final_prompt = build_image_prompt(test_prompt, prompt_prefix)
                            
                                # Generate preview media (use user-specified size and media type)
                                media_result = run_async(pixelle_video.media(
                                    prompt=final_prompt,
                                    workflow=workflow_key,
                                    media_type=template_media_type,
                                    width=int(image_width),
                                    height=int(image_height)
                                ))
                                preview_media_path = media_result.url
                            
                                # Display preview (support both URL and local path)
                                if preview_media_path:
                                    success_text = tr("style.video_preview_success") if template_media_type == "video" else tr("style.preview_success")
                                    st.success(success_text)
                                
                                    if template_media_type == "video":
                                        # Display video
                                        st.video(preview_media_path)
                                    else:
                                        # Display image
                                        if preview_media_path.startswith('http'):
                                            # URL - use directly
                                            img_html = f'<div class="preview-image"><img src="{preview_media_path}" alt="Style Preview"/></div>'
                                        else:
                                            # Local file - encode as base64
                                            with open(preview_media_path, 'rb') as f:
                                                img_data = base64.b64encode(f.read()).decode()
                                            img_html = f'<div class="preview-image"><img src="data:image/png;base64,{img_data}" alt="Style Preview"/></div>'
                                        
                                        st.markdown(img_html, unsafe_allow_html=True)
                                
                                    # Show the final prompt used
                                    st.info(f"**{tr('style.final_prompt_label')}**\n{final_prompt}")
                                
                                    # Show file path
                                    st.caption(f"📁 {preview_media_path}")
                                else:
                                    st.error(tr("style.preview_failed_general"))
                            except Exception as e:
                                st.error(tr("style.preview_failed", error=str(e)))
                                logger.exception(e)
            
        
        else:
            # Template doesn't need images - show simplified message
            with st.container(border=True):
                st.markdown(f"**{tr('section.image')}**")
                st.info("ℹ️ " + tr("image.not_required"))
                st.caption(tr("image.not_required_hint"))
                
                # Get media size from template (even though not used, for consistency)
                image_width = st.session_state.get('template_media_width', 1024)
                image_height = st.session_state.get('template_media_height', 1024)
                
                # Set default values for later use
                workflow_key = None
                prompt_prefix = ""
        

    # ========================================================================
    # Right Column: Generate Button + Progress + Video Preview
    # ========================================================================
    with right_col:
        with st.container(border=True):
            st.markdown(f"**{tr('section.video_generation')}**")
            
            # Check if system is configured
            if not config_manager.validate():
                st.warning(tr("settings.not_configured"))
            
            # Generate Button
            if st.button(tr("btn.generate"), type="primary", use_container_width=True):
                # Validate system configuration
                if not config_manager.validate():
                    st.error(tr("settings.not_configured"))
                    st.stop()
                
                # Validate input
                if not text:
                    st.error(tr("error.input_required"))
                    st.stop()
                
                # Show progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Record start time for generation
                import time
                start_time = time.time()
                
                try:
                    # Progress callback to update UI
                    def update_progress(event: ProgressEvent):
                        """Update progress bar and status text from ProgressEvent"""
                        # Translate event to user-facing message
                        if event.event_type == "frame_step":
                            # Frame step: "分镜 3/5 - 步骤 2/4: 生成插图"
                            action_key = f"progress.step_{event.action}"
                            action_text = tr(action_key)
                            message = tr(
                                "progress.frame_step",
                                current=event.frame_current,
                                total=event.frame_total,
                                step=event.step,
                                action=action_text
                            )
                        elif event.event_type == "processing_frame":
                            # Processing frame: "分镜 3/5"
                            message = tr(
                                "progress.frame",
                                current=event.frame_current,
                                total=event.frame_total
                            )
                        else:
                            # Simple events: use i18n key directly
                            message = tr(f"progress.{event.event_type}")
                        
                        # Append extra_info if available (e.g., batch progress)
                        if event.extra_info:
                            message = f"{message} - {event.extra_info}"
                        
                        status_text.text(message)
                        progress_bar.progress(min(int(event.progress * 100), 99))  # Cap at 99% until complete
                    
                    # Generate video (directly pass parameters)
                    # Note: image_width and image_height are now auto-determined from template
                    video_params = {
                        "text": text,
                        "mode": mode,
                        "title": title if title else None,
                        "n_scenes": n_scenes,
                        "image_workflow": workflow_key,
                        "frame_template": frame_template,
                        "prompt_prefix": prompt_prefix,
                        "bgm_path": bgm_path,
                        "progress_callback": update_progress,
                    }
                    
                    # Add TTS parameters based on mode
                    video_params["tts_inference_mode"] = tts_mode
                    if tts_mode == "local":
                        video_params["tts_voice"] = selected_voice
                        video_params["tts_speed"] = tts_speed
                    else:  # comfyui
                        video_params["tts_workflow"] = tts_workflow_key
                        if ref_audio_path:
                            video_params["ref_audio"] = str(ref_audio_path)
                    
                    # Add custom template parameters if any
                    if custom_values_for_video:
                        video_params["template_params"] = custom_values_for_video
                    
                    result = run_async(pixelle_video.generate_video(**video_params))
                    
                    # Calculate total generation time
                    total_generation_time = time.time() - start_time
                    
                    progress_bar.progress(100)
                    status_text.text(tr("status.success"))
                    
                    # Display success message
                    st.success(tr("status.video_generated", path=result.video_path))
                    
                    st.markdown("---")
                    
                    # Video information (compact display)
                    file_size_mb = result.file_size / (1024 * 1024)
                    
                    # Parse video size from template path
                    from pixelle_video.utils.template_util import parse_template_size, resolve_template_path
                    template_path = resolve_template_path(result.storyboard.config.frame_template)
                    video_width, video_height = parse_template_size(template_path)
                    
                    info_text = (
                        f"⏱️ {tr('info.generation_time')} {total_generation_time:.1f}s   "
                        f"📦 {file_size_mb:.2f}MB   "
                        f"🎬 {len(result.storyboard.frames)}{tr('info.scenes_unit')}   "
                        f"📐 {video_width}x{video_height}"
                    )
                    st.caption(info_text)
                    
                    st.markdown("---")
                    
                    # Video preview
                    if os.path.exists(result.video_path):
                        st.video(result.video_path)
                    else:
                        st.error(tr("status.video_not_found", path=result.video_path))
                    
                except Exception as e:
                    status_text.text("")
                    progress_bar.empty()
                    st.error(tr("status.error", error=str(e)))
                    logger.exception(e)
                    st.stop()


if __name__ == "__main__":
    main()

