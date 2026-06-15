---
name: chinese-video-to-english
version: "1.0.0"
description: "Turn a Chinese talking-head / 口播 video into English — either a re-dubbed English voiceover, or an English-subtitled version that masks the original burned-in Chinese captions. Handles transcription, translation, TTS dubbing, and subtitle burning end to end."
argument-hint: '把 balcony.mp4 转成英文口播 | 把 balcony.mp4 转成英文字幕版（遮掉中文字幕）'
allowed-tools: Bash, Read, Write, AskUserQuestion
user-invocable: true
metadata:
  openclaw:
    emoji: "🎬"
    requires:
      bins:
        - ffmpeg
        - ffprobe
        - python3
      env: []
      optionalEnv:
        - VOICE
    files:
      - "scripts/*"
      - "references/*"
    tags:
      - video
      - translation
      - dubbing
      - subtitles
      - chinese
      - voiceover
---

# chinese-video-to-english

把一段**中文口播视频**转成英文。两种产出，可任选其一或两者都要：

1. **英文口播（配音版 / voiceover）** — 把原视频里的中文人声替换成自然的英文配音，画面不变。
2. **英文字幕版（subtitled）** — 在画面下方烧录英文字幕，并**遮掉原来烧死在画面里的中文字幕**。

> 这条流程的"聪明部分"（把中文翻成自然地道的英文）由 Claude 亲自完成；脚本只负责机械的提取音频、语音识别、合成配音、合成字幕等步骤。

---

## When to use

用户说类似这些话时启用本 Skill：

- "把这个视频转成英文" / "做个英文配音版"
- "把口播翻译成英文，重新配音"
- "加英文字幕，把原来的中文字幕盖掉"
- "localize / dub / re-voice this Chinese video into English"

---

## Prerequisites（第一次用先装好）

本 Skill 需要本机有这些命令行工具：

- `ffmpeg` / `ffprobe` — 视频音频处理（必装）
- `python3`
- Python 包：`edge-tts`（免费高质量英文配音，需联网）、以及 `faster-whisper` **或** `openai-whisper`（中文语音识别）

先跑一次自检，缺什么它会告诉你怎么装：

```bash
bash scripts/check_deps.sh
```

一键安装（macOS 示例）：

```bash
brew install ffmpeg
pip install edge-tts faster-whisper      # faster-whisper 在 CPU 上更快更轻
# 或者：pip install edge-tts openai-whisper
```

> 在受限网络（如云端会话）里 `edge-tts` / 模型下载可能用不了；**建议在本地电脑上运行本 Skill**。

---

## Workflow（Claude 执行步骤）

设工作目录里有输入视频 `INPUT.mp4`。所有中间产物都放在 `./out/` 下。

### 步骤 0 — 确认意图

先用 `AskUserQuestion` 问清楚（除非用户已说明）：
- 要 **英文口播配音**，还是 **英文字幕版**，还是 **两个都要**？
- 字幕版是否需要遮掉原中文字幕？（默认遮）

### 步骤 1 — 提取音频

```bash
bash scripts/extract_audio.sh INPUT.mp4 out/audio.wav
```

### 步骤 2 — 中文转写（带时间轴）

```bash
python3 scripts/transcribe.py out/audio.wav out/transcript.zh.json --language zh
```

产出 `out/transcript.zh.json`，格式为分段数组：

```json
[{"index": 1, "start": 0.0, "end": 3.2, "text": "大家好，今天教大家做阳台植物墙"}, ...]
```

### 步骤 3 — 翻译成英文（**Claude 亲自做**）

读取 `out/transcript.zh.json`，把每一段 `text` 翻成**自然、口语化、地道**的英文：

- **保留 `index`/`start`/`end` 完全不变**，只改 `text`。
- 译文长度尽量贴近原段时长（配音才不会太挤或太空）；该段是口播，就用说话的语气，不要书面腔。
- 写到 `out/transcript.en.json`（用 Write 工具）。

### 步骤 4A — 生成英文配音（口播版）

```bash
python3 scripts/tts.py out/transcript.en.json out/dub.wav     # 可加 --voice en-US-GuyNeural
bash scripts/build_voiceover.sh INPUT.mp4 out/dub.wav out/INPUT_EN_voiceover.mp4
```

`tts.py` 会逐段合成英文语音，并按每段的 `start/end` 时间轴对齐（必要时轻微变速塞进时长里），保证口型不漂。

### 步骤 4B — 生成英文字幕版

先把 en JSON 转成 SRT，再烧录 + 遮原字幕：

```bash
python3 scripts/make_srt.py out/transcript.en.json out/transcript.en.srt
bash scripts/burn_subtitles.sh INPUT.mp4 out/transcript.en.srt out/INPUT_EN_subtitled.mp4
```

遮原中文字幕：`burn_subtitles.sh` 默认在画面底部盖一条黑边再写英文字幕。可调：
- `MASK_HEIGHT=140`（盖住的高度像素，默认按视频高度的 ~18%）
- `MASK_MODE=box|blur`（box=盖黑条；blur=高斯模糊原字幕区，默认 box）
- `MASK_COLOR=black`

例：`MASK_HEIGHT=160 MASK_MODE=blur bash scripts/burn_subtitles.sh ...`

### 步骤 5 — 交付

把最终 mp4 用 `SendUserFile` 发给用户，并说明用了哪种产出。

---

## Notes / 经验

- **变速别太狠**：英文常比中文长，`tts.py` 默认把每段变速限制在 0.6×–1.7×，超出就接受轻微留白/重叠，优先保音质。想换配音嗓音用 `--voice`（如 `en-US-AriaNeural` 女声 / `en-US-GuyNeural` 男声）。
- **识别不准**：口音重或背景音乐大时，换更大的 whisper 模型：`transcribe.py ... --model large-v3`（默认 `small`）。
- **原字幕没盖干净**：调大 `MASK_HEIGHT`，或用 `MASK_MODE=blur`。
- 详细的逐步说明（含给非技术用户的大白话版）见 `references/workflow.md`。
