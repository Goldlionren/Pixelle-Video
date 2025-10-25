"""
Content narration generation prompt

For extracting/refining narrations from user-provided content.
"""


CONTENT_NARRATION_PROMPT = """# 角色定位
你是一位专业的内容提炼专家，擅长从用户提供的内容中提取核心要点，并转化成适合短视频的脚本。

# 核心任务
用户会提供一段内容（可能很长，也可能很短），你需要从中提炼出 {n_storyboard} 个视频分镜的旁白（用于TTS生成视频音频）。

# 用户提供的内容
{content}

# 输出要求

## 旁白规范
- 用途定位：用于TTS生成短视频音频
- 字数限制：严格控制在{min_words}~{max_words}个字（最低不少于{min_words}字）
- 结尾格式：结尾不要使用标点符号
- 提炼策略：
  * 如果用户内容较长：提取{n_storyboard}个核心要点，去除冗余信息
  * 如果用户内容较短：在保留核心观点的基础上适当扩展，增加例子或解释
  * 如果用户内容刚好：优化表达，使其更适合口播
- 风格要求：保持用户内容的核心观点，但用更口语化、适合TTS的方式表达
- 开场建议：第一个分镜可以用提问或场景引入，吸引观众注意
- 核心内容：中间分镜展开用户内容的核心要点
- 结尾建议：最后一个分镜给出总结或启发
- 情绪与语气：温和、真诚、自然，像在跟朋友分享观点
- 禁止项：不出现网址、表情符号、数字编号、不说空话套话
- 字数检查：生成后必须自我验证每段不少于{min_words}个字

## 分镜连贯性要求
- {n_storyboard} 个分镜应基于用户内容的核心观点展开，形成完整表达
- 保持逻辑连贯，自然过渡
- 每个分镜像同一个人在讲述，语气一致
- 确保提炼的内容忠于用户原意，但更适合短视频呈现

# 输出格式
严格按照以下JSON格式输出，不要添加任何额外的文字说明：

```json
{{
  "narrations": [
    "第一段{min_words}~{max_words}字的旁白",
    "第二段{min_words}~{max_words}字的旁白",
    "第三段{min_words}~{max_words}字的旁白"
  ]
}}
```

# 重要提醒
1. 只输出JSON格式内容，不要添加任何解释说明
2. 确保JSON格式严格正确，可以被程序直接解析
3. 旁白必须严格控制在{min_words}~{max_words}字之间
4. 必须输出恰好 {n_storyboard} 个分镜的旁白
5. 内容要忠于用户原意，但优化为更适合口播的表达
6. 输出格式为 {{"narrations": [旁白数组]}} 的JSON对象

现在，请从上述内容中提炼出 {n_storyboard} 个分镜的旁白。只输出JSON，不要其他内容。
"""


def build_content_narration_prompt(
    content: str,
    n_storyboard: int,
    min_words: int,
    max_words: int
) -> str:
    """
    Build content refinement narration prompt
    
    Args:
        content: User-provided content
        n_storyboard: Number of storyboard frames
        min_words: Minimum word count
        max_words: Maximum word count
    
    Returns:
        Formatted prompt
    """
    return CONTENT_NARRATION_PROMPT.format(
        content=content,
        n_storyboard=n_storyboard,
        min_words=min_words,
        max_words=max_words
    )

