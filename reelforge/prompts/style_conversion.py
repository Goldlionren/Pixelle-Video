"""
Style conversion prompt

For converting user's custom style description to image generation prompt.
"""


STYLE_CONVERSION_PROMPT = """Convert this style description into a detailed image generation prompt for Stable Diffusion/FLUX:

Style Description: {description}

Requirements:
- Focus on visual elements, colors, lighting, mood, atmosphere
- Be specific and detailed
- Use professional photography/art terminology
- Output ONLY the prompt in English (no explanations)
- Keep it under 100 words
- Use comma-separated descriptive phrases

Image Prompt:"""


def build_style_conversion_prompt(description: str) -> str:
    """
    Build style conversion prompt
    
    Converts user's custom style description (in any language) to an English
    image generation prompt suitable for Stable Diffusion/FLUX models.
    
    Args:
        description: User's style description in any language
    
    Returns:
        Formatted prompt
    
    Example:
        >>> build_style_conversion_prompt("赛博朋克风格，霓虹灯，未来感")
        # Returns prompt that will convert to: "cyberpunk style, neon lights, futuristic..."
    """
    return STYLE_CONVERSION_PROMPT.format(description=description)

