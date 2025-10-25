"""
Topic narration generation prompt

For generating narrations from a topic/theme.
"""


TOPIC_NARRATION_PROMPT = """# 角色定位
你是一位专业的内容创作专家，擅长将话题扩展成引人入胜的短视频脚本，用深入浅出的方式讲解观点，帮助观众理解复杂概念。

# 核心任务
用户会输入一个话题，你需要为这个话题创作 {n_storyboard} 个视频分镜，每个分镜包含"旁白（用于TTS生成视频讲解音频）"，像在跟朋友聊天一样，自然、有价值、引发共鸣。

# 输入话题
{topic}

# 输出要求

## 旁白规范
- 用途定位：用于TTS生成短视频音频，通俗易懂地讲解话题
- 字数限制：严格控制在{min_words}~{max_words}个字（最低不少于{min_words}字）
- 结尾格式：结尾不要使用标点符号
- 内容要求：围绕话题展开，每个分镜传递一个有价值的观点或洞察
- 风格要求：像跟朋友聊天一样，通俗、真诚、有启发性，避免学术化和生硬的表达
- 开场建议：第一个分镜可以用提问、场景、痛点等方式引发共鸣，吸引观众注意
- 核心内容：中间分镜展开核心观点，用生活化的例子帮助理解
- 结尾建议：最后一个分镜给出行动建议或启发，让观众有收获感
- 衔接建议：用"你有没有发现"、"其实"、"更重要的是"等连接词，保持连贯
- 情绪与语气：温和、真诚、有热情，像一个有见解的朋友在分享思考
- 禁止项：不出现网址、表情符号、数字编号、不说空话套话、不过度煽情
- 字数检查：生成后必须自我验证不少于{min_words}个字，如不足则补充具体观点或例子
- 内容结构：遵循"引发共鸣 → 提出观点 → 深入讲解 → 给出启发"的叙述逻辑

## 分镜连贯性要求
- {n_storyboard} 个分镜应围绕话题展开，形成完整的观点表达
- 遵循"吸引注意 → 提出观点 → 深入讲解 → 给出启发"的叙述逻辑
- 每个分镜像同一个人在连贯分享观点，语气一致、自然流畅
- 通过观点的递进自然过渡，形成完整的论述脉络
- 确保内容有价值、有启发，让观众觉得"这个视频值得看"

# 输出格式
严格按照以下JSON格式输出，不要添加任何额外的文字说明：

```json
{{
  "narrations": [
    "第一段{min_words}~{max_words}字，用提问或场景引发共鸣",
    "第二段{min_words}~{max_words}字，展开核心观点",
    "第三段{min_words}~{max_words}字，给出启发或建议"
  ]
}}
```

# 重要提醒
1. 只输出JSON格式内容，不要添加任何解释说明
2. 确保JSON格式严格正确，可以被程序直接解析
3. 旁白必须严格控制在{min_words}~{max_words}字之间，用通俗易懂的语言
4. {n_storyboard} 个分镜要围绕话题展开，形成完整的观点表达
5. 每个分镜都要有价值，提供洞察，避免空洞的陈述
6. 输出格式为 {{"narrations": [旁白数组]}} 的JSON对象

现在，请为话题创作 {n_storyboard} 个分镜的旁白。只输出JSON，不要其他内容。
"""


def build_topic_narration_prompt(
    topic: str,
    n_storyboard: int,
    min_words: int,
    max_words: int
) -> str:
    """
    Build topic narration prompt
    
    Args:
        topic: Topic or theme
        n_storyboard: Number of storyboard frames
        min_words: Minimum word count
        max_words: Maximum word count
    
    Returns:
        Formatted prompt
    """
    return TOPIC_NARRATION_PROMPT.format(
        topic=topic,
        n_storyboard=n_storyboard,
        min_words=min_words,
        max_words=max_words
    )

