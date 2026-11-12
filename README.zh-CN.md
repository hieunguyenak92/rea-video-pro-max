# REA-Video-Pro-Max

## 解读剪辑方法，用相同风格创作新内容。

**把参考视频变成有证据的时间线和可复用风格模板，再绑定不同的脚本与素材，渲染你自己的视频。**

[English](README.md) · [Tiếng Việt](README.vi.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [简体中文](README.zh-CN.md) · [ไทย](README.th.md) · [Français](README.fr.md)

[录制示例](docs/index.html) · [视频 A](docs/media/reference.mp4) · [视频 B](docs/media/adapted.mp4) · [验证记录 (English)](docs/VALIDATION.md)

好的剪辑包含很多判断：在哪里切镜头、字幕如何分组、哪个词高亮、动作何时落定、画面如何与声音配合。REA-Video-Pro-Max 让支持范围内的这些判断可以检查和复用。

```text
视频 A → 分析＋推断时间线 → 风格模板＋新内容 → 可编辑项目 → 视频 B
```

示例使用项目拥有的合成媒体。A 和 B 的文字及素材不同。静态网站展示已记录的结果，不运行实时推理，也不上传访问者的视频。

## 可以提出哪些任务？

- 把整条视频拆成镜头、字幕样式、运动、音频提示和带时间戳证据的时间线。
- 分析单帧的字体、布局和颜色；单张图片不能确定动画时长或声音。
- 将提取的风格用于新脚本、图片或视频素材，创作不同的作品。
- 仅请求 REA 时，时间线和分析文件本身就是完整交付。

```text
用 REA-Video-Pro-Max 分析 reference.mp4 的时间线与风格。使用我的新脚本和素材生成另一条视频，保留类似的字幕、运动和剪辑节奏。交付模板、可编辑项目、视频以及尚未验证的限制。
```

## 获得第一个结果

需要 Python 3.11+、FFmpeg 和 FFprobe。Python 运行时使用 Pillow、NumPy、PyAV。Tesseract 是可选 OCR 依赖，实际可运行的语言由已安装的语言数据决定。请查看[支持边界 (English)](docs/SUPPORT-MATRIX.md)。

macOS 是已实测的开发平台。Linux 是计划中的 CI 目标；Windows 原生渲染尚未认证。创作验证需要与项目及输出哈希一致的渲染记录，并独立执行 OCR，因此完整示例需要安装 Tesseract 和 `eng` 数据。

```sh
python -m venv .venv
# macOS / Linux
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e .
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py doctor
```

```sh
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py analyze examples/reference.mp4 --out ./work/analysis --ocr auto --ocr-lang eng
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py template ./work/analysis/analysis.json --out ./work/style-template.json
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py compose ./work/style-template.json --content examples/content.json --out ./work/project
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py render ./work/project/project.json --out ./work/video-b.mp4
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py verify ./work/project/project.json --mode style-transfer --render ./work/video-b.mp4 --ocr-lang eng
```

命令以 Git checkout 目录结构为准。解压后的 skill 入口是 `scripts/rea-video-pro-max.py`，请保留 `lib`、`assets`、`references` 目录。使用已安装依赖的 Python，不要只复制入口脚本。

## 放入你的新内容

`examples/content.json` 是合成 content binding 示例：每个新场景包含 `id`、`text`、`duration`、`background`、`accent` 和可选 `asset` 路径；`width`、`height`、`fps` 指定输出，`audio`、`font` 可选。素材路径相对于 binding 文件解析。项目复制素材并记录哈希，不会悄悄拿 A 的画面或音乐充当 B 的新内容。新话语需要新时间信息；没有精确对齐时，会说明估计方法。

场景视频的音轨默认静音；如需声音，请单独提供新的 `audio` 绑定。短素材会保持最后一帧，原生渲染要求素材方向正确且采用方形像素。CSV 仅导出镜头行。使用复杂或双向文字前，请先检查字形排版与分组限制。

## 用于 Claude Code / Codex

将整个 `skills/rea-video-pro-max` 文件夹复制到 host 的 skill 目录，或让 agent 从本 checkout 安装。常见项目内位置为 `.claude/skills/rea-video-pro-max` 和 `.agents/skills/rea-video-pro-max`。安装 skill 不会安装 FFmpeg、OCR 语言包或模型权重。host 的账户、执行权限与数据政策独立适用。[Skill](skills/rea-video-pro-max/SKILL.md) 与技术参考目前为 English。

## 数据和导出行为

- Native JSON 保留分析、时间线、字幕／样式／运动／音频数据、模板和项目。CSV 用于检查编辑数据。
- SRT/WebVTT/ASS 按各自格式能力导出文字和时间；SRT 无法保留完整字体样式或运动。
- 仅使用安装版本报告为 available 的时间线适配器。导出 receipt 说明支持子集、近似和损失，不保证任意编辑器都能还原任意效果。
- 软件渲染器使用新内容合成并通过 FFmpeg 编码，不依赖 FFmpeg 可选的 `drawtext`、`ass`、`subtitles` 滤镜。

## 重要限制

测得的元数据、OCR 结果、样式拟合和制作机制假设属于不同证据。扁平视频不能唯一确定原始片段、被遮挡图层、原字体／插件／剪辑项目或 AI 提示词。初始范围聚焦时间、字幕和支持的 2D 基元；不是万能视频反编译器，也没有被证明是市场最强。复杂遮挡、3D 重建、HDR 母版及任意 NLE 往返均在已验证范围之外。复杂文字 shaping 需要单独支持与测试；九种 README 翻译不代表九种 OCR 或渲染语言获得认证。

视频 B 按新内容、风格合同与播放结果检查，不要求与 A 全帧像素一致。技术验证与人的创作质量判断不同。[验证与限制 (English)](docs/VALIDATION.md)。

## 本地处理与致谢

核心分析和渲染在本地运行，不要求付费 API、不向托管推理服务上传视频，也不自动发布媒体。安装依赖或启用可选 provider 可能产生网络请求。Claude/Codex host 的政策另行适用。[Privacy (English)](docs/PRIVACY.md)。项目受 JuneYaooo/rea-video 启发，是独立产品而非官方升级；代码、字体、媒体、编码器和模型的许可分别适用。

本地报告默认复制参考媒体和证据。`report --no-media` 只省略完整媒体副本，仍保留 OCR 文字、本地路径和裁切图。分享前请检查。

[支持 (English)](SUPPORT.md) · [维护 (English)](docs/MAINTENANCE.md) · 未声称翻译经过专业母语审校。

[本地语音与高级运动分析（英文技术文档）](skills/rea-video-pro-max/references/speech-and-motion.md).
