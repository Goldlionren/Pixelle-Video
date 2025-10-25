# Prompts Directory

Centralized prompt management for all LLM interactions in ReelForge.

## Structure

Each prompt is in its own file for easy maintenance and modification:

```
prompts/
├── __init__.py                  # Exports all builder functions
├── topic_narration.py           # Generate narrations from topic
├── content_narration.py         # Extract/refine narrations from content
├── script_split.py              # Split fixed script into segments
├── title_generation.py          # Generate video title from content
├── image_generation.py          # Generate image prompts from narrations
└── style_conversion.py          # Convert style description to image prompt
```

## Usage

All builder functions are exported from the package root:

```python
from reelforge.prompts import (
    build_topic_narration_prompt,
    build_content_narration_prompt,
    build_script_split_prompt,
    build_title_generation_prompt,
    build_image_prompt_prompt,
    build_style_conversion_prompt,
)
```

## Prompt Files

### Narration Prompts

1. **topic_narration.py**
   - Purpose: Generate engaging narrations from a topic/theme
   - Input: topic, n_storyboard, min_words, max_words
   - Output: JSON with narrations array

2. **content_narration.py**
   - Purpose: Extract and refine narrations from user content
   - Input: content, n_storyboard, min_words, max_words
   - Output: JSON with narrations array

3. **script_split.py**
   - Purpose: Split fixed script into natural segments (no modification)
   - Input: script, min_words (reference), max_words (reference)
   - Output: JSON with narrations array

4. **title_generation.py**
   - Purpose: Generate short, attractive video title
   - Input: content, max_length
   - Output: Plain text title

### Image Prompts

5. **image_generation.py**
   - Purpose: Generate English image prompts from narrations
   - Input: narrations, min_words, max_words, style_preset/style_description
   - Output: JSON with image_prompts array
   - Contains: IMAGE_STYLE_PRESETS dictionary

6. **style_conversion.py**
   - Purpose: Convert custom style description to English image prompt
   - Input: description (any language)
   - Output: Plain text English image prompt

## Modifying Prompts

To modify a prompt:

1. Locate the relevant file (e.g., `topic_narration.py`)
2. Edit the prompt constant (e.g., `TOPIC_NARRATION_PROMPT`)
3. Changes take effect immediately (no need to modify service code)

## Adding New Prompts

To add a new prompt:

1. Create a new file (e.g., `my_new_prompt.py`)
2. Define the prompt constant and builder function
3. Export the builder function in `__init__.py`
4. Use it in service code:
   ```python
   from reelforge.prompts import build_my_new_prompt
   ```

## Design Principles

- **One File, One Prompt**: Each prompt has its own file for clarity
- **Builder Functions**: Each file exports a `build_*_prompt()` function
- **Centralized Exports**: All builders are exported from `__init__.py`
- **Consistent Format**: All prompts follow similar structure and style
- **Easy Maintenance**: Modify prompts without touching service code

