<div align="center">
<h1 align="center">Pixelle-Video 🎬</h1>

<p align="center">
  <a href="https://github.com/PixelleLab/Pixelle-Video/stargazers"><img src="https://img.shields.io/github/stars/PixelleLab/Pixelle-Video.svg?style=for-the-badge" alt="Stargazers"></a>
  <a href="https://github.com/PixelleLab/Pixelle-Video/issues"><img src="https://img.shields.io/github/issues/PixelleLab/Pixelle-Video.svg?style=for-the-badge" alt="Issues"></a>
  <a href="https://github.com/PixelleLab/Pixelle-Video/network/members"><img src="https://img.shields.io/github/forks/PixelleLab/Pixelle-Video.svg?style=for-the-badge" alt="Forks"></a>
  <a href="https://github.com/PixelleLab/Pixelle-Video/blob/main/LICENSE"><img src="https://img.shields.io/github/license/PixelleLab/Pixelle-Video.svg?style=for-the-badge" alt="License"></a>
</p>

<br>

<h3 align="center">🚀 AI 视频创作工具 - 3 分钟生成一个短视频</h3>

<br>

只需输入一个 **主题**，Pixelle-Video 就能自动完成：
- ✍️ 撰写视频文案
- 🎨 生成 AI 配图  
- 🗣️ 合成语音解说
- 🎵 添加背景音乐
- 🎬 一键合成视频

<br>

**零门槛，零剪辑经验**，让视频创作成为一句话的事！

</div>

---

## ✨ 功能亮点

- ✅ **全自动生成** - 输入主题，3 分钟自动生成完整视频
- ✅ **AI 智能文案** - 根据主题智能创作解说词，无需自己写脚本
- ✅ **AI 生成配图** - 每句话都配上精美的 AI 插图
- ✅ **真人语音** - 100+ 种真人声音可选，告别机械音
- ✅ **背景音乐** - 支持添加 BGM，让视频更有氛围
- ✅ **视觉风格** - 多种模板可选，打造独特视频风格
- ✅ **灵活尺寸** - 支持竖屏、横屏等多种视频尺寸
- ✅ **多种 AI 模型** - 支持 GPT、通义千问、DeepSeek、Ollama 等
- ✅ **原子能力灵活组合** - 基于 ComfyUI 架构，可使用预置工作流，也可自定义任意能力（如替换生图模型为 FLUX、替换 TTS 为 ChatTTS 等）

---

## 🎬 视频示例

> 待补充：这里可以添加一些生成的视频示例

---

## 🚀 快速开始

### 第一步：下载项目

```bash
git clone https://github.com/PixelleLab/Pixelle-Video.git
cd Pixelle-Video
```

### 第二步：启动 Web 界面

```bash
# 使用 uv 运行（推荐，会自动安装依赖）
uv run streamlit run web/app.py
```

浏览器会自动打开 http://localhost:8501

### 第三步：在 Web 界面配置

首次使用时，展开「⚙️ 系统配置」面板，填写：
- **LLM 配置**: 选择 AI 模型（如通义千问、GPT 等）并填入 API Key
- **图像配置**: 如需生成图片，配置 ComfyUI 地址或 RunningHub API Key

配置好后点击「保存配置」，就可以开始生成视频了！

---

## 💻 使用方法

打开 Web 界面后，你会看到三栏布局，下面详细讲解每个部分：

---

### ⚙️ 系统配置（首次必填）

首次使用时需要配置，点击展开「⚙️ 系统配置」面板：

#### 1. LLM 配置（大语言模型）
用于生成视频文案的 AI。

**快速选择预设**  
- 通过下拉菜单选择预设模型（通义千问、GPT-4o、DeepSeek 等）
- 选择后会自动填充 base_url 和 model
- 点击「🔑 获取 API Key」链接去注册并获取密钥

**手动配置**  
- API Key: 填入你的密钥
- Base URL: API 地址
- Model: 模型名称

#### 2. 图像配置
用于生成视频配图的 AI。

**本地部署（推荐）**  
- ComfyUI URL: 本地 ComfyUI 服务地址（默认 http://127.0.0.1:8188）
- 点击「测试连接」确认服务可用

**云端部署**  
- RunningHub API Key: 云端图像生成服务的密钥

配置完成后点击「保存配置」。

---

### 📝 内容输入（左侧栏）

#### 生成模式
- **AI 生成内容**: 输入主题，AI 自动创作文案
  - 适合：想快速生成视频，让 AI 写稿
  - 例如：「为什么要养成阅读习惯」
- **固定文案内容**: 直接输入完整文案，跳过 AI 创作
  - 适合：已有现成文案，直接生成视频

---

### 🎵 音频设置（左侧栏）

#### 语音选择
- 从下拉菜单选择解说声音
- 提供 4 种精选声音（男声/女声、专业/年轻）
- 点击「试听语音」可以预览效果

#### 背景音乐
- **无 BGM**: 纯人声解说
- **内置音乐**: 选择预置的背景音乐（如 default.mp3）
- **自定义音乐**: 将你的音乐文件（MP3/WAV 等）放到 `bgm/` 文件夹
- 点击「试听 BGM」可以预览音乐

---

### 🎨 视觉设置（中间栏）

#### 视觉风格
决定 AI 生成什么风格的配图。

**ComfyUI 工作流**  
- 选择图像生成的工作流文件
- 默认使用 `image_flux.json`
- 如果懂 ComfyUI，可以放自己的工作流到 `workflows/` 文件夹

**提示词前缀（Prompt Prefix）**  
- 控制图像的整体风格（语言需要是英文的）
- 例如：Minimalist black-and-white stick figure illustration on a plain white background, clean thin lines, simple sketch style
- 点击「预览风格」可以测试效果

#### 视频模板
决定视频画面的布局和设计。

- 从下拉菜单选择模板（default.html、modern.html、classic.html 等）
- 点击「预览模板」可以自定义参数测试效果
- 如果懂 HTML，可以在 `templates/` 文件夹创建自己的模板

---

### 🎬 生成视频（右侧栏）

#### 生成按钮
- 配置好所有参数后，点击「🎬 生成视频」
- 会显示实时进度（生成文案 → 生成配图 → 合成语音 → 合成视频）
- 生成完成后自动显示视频预览

#### 进度显示
- 实时显示当前步骤
- 例如：「分镜 3/5 - 生成插图」

#### 视频预览
- 生成完成后自动播放
- 显示视频时长、文件大小、分镜数等信息
- 视频文件保存在 `output/` 文件夹

---

### ❓ 常见问题

**Q: 第一次使用需要多久？**  
A: 生成一个 3 段视频大约需要 2-5 分钟，取决于你的网络和 AI 推理速度。

**Q: 视频效果不满意怎么办？**  
A: 可以尝试：
1. 更换 LLM 模型（不同模型文案风格不同）
2. 调整提示词前缀（改变配图风格）
3. 更换语音（不同声音适合不同内容）
4. 尝试不同的视频模板

**Q: 费用大概多少？**  
A: **本项目完全支持免费运行！**

- **完全免费方案**: LLM 使用 Ollama（本地运行）+ ComfyUI 本地部署 = 0 元
- **推荐方案**: LLM 使用通义千问（生成一个 3 段视频约 0.01-0.05 元）+ ComfyUI 本地部署
- **云端方案**: LLM 使用 OpenAI + 图像使用 RunningHub（费用较高但无需本地环境）

**选择建议**：本地有显卡建议完全免费方案，否则推荐使用通义千问（性价比高）

---

## 🤝 参考项目

Pixelle-Video 的设计受到以下优秀开源项目的启发：

- [Pixelle-MCP](https://github.com/AIDC-AI/Pixelle-MCP) - ComfyUI MCP 服务器，让 AI 助手直接调用 ComfyUI
- [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) - 优秀的视频生成工具
- [NarratoAI](https://github.com/linyqh/NarratoAI) - 影视解说自动化工具
- [MoneyPrinterPlus](https://github.com/ddean2009/MoneyPrinterPlus) - 视频创作平台
- [ComfyKit](https://github.com/puke3615/ComfyKit) - ComfyUI 工作流封装库

感谢这些项目的开源精神！🙏

---

## 📢 反馈与支持

- 🐛 **遇到问题**: 提交 [Issue](https://github.com/PixelleLab/Pixelle-Video/issues)
- 💡 **功能建议**: 提交 [Feature Request](https://github.com/PixelleLab/Pixelle-Video/issues)
- ⭐ **给个 Star**: 如果这个项目对你有帮助，欢迎给个 Star 支持一下！

---

## 📝 许可证

本项目采用 MIT 许可证，详情请查看 [LICENSE](LICENSE) 文件。

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=PixelleLab/Pixelle-Video&type=Date)](https://star-history.com/#PixelleLab/Pixelle-Video&Date)

---

<div align="center">
  <p>Made with ❤️ by PixelleLab</p>
  <p>
    <a href="#top">回到顶部 ⬆️</a>
  </p>
</div>
