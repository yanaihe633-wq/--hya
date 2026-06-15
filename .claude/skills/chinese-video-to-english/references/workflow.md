# 中文视频转英文 · 完整流程说明

这份文档是给两类读者看的：
- **给 Claude**：每一步的精确命令和注意事项。
- **给非技术用户（大白话版）**：在最下面，解释这套东西到底在干嘛。

---

## 一、流程总览

```
INPUT.mp4
   │
   ├─ extract_audio.sh ──► out/audio.wav            (1) 抽出声音
   │
   ├─ transcribe.py ─────► out/transcript.zh.json   (2) 中文听写成带时间的文字
   │
   ├─ [Claude 翻译] ─────► out/transcript.en.json   (3) 翻成自然英文（时间轴不变）
   │
   ├─【口播版】tts.py ──► out/dub.wav
   │          build_voiceover.sh ─► out/..._EN_voiceover.mp4
   │
   └─【字幕版】make_srt.py ─► out/transcript.en.srt
              burn_subtitles.sh ─► out/..._EN_subtitled.mp4
```

## 二、逐步命令

```bash
# 0) 自检环境（第一次）
bash scripts/check_deps.sh

# 1) 抽音频（16kHz 单声道，给识别用）
bash scripts/extract_audio.sh INPUT.mp4 out/audio.wav

# 2) 中文转写（默认 small 模型；口音重/有BGM就换 --model large-v3）
python3 scripts/transcribe.py out/audio.wav out/transcript.zh.json --language zh

# 3) 翻译：Claude 读 transcript.zh.json，逐段把 text 翻成口语化英文，
#    index/start/end 原样不动，写到 transcript.en.json

# 4A) 英文配音版
python3 scripts/tts.py out/transcript.en.json out/dub.wav --voice en-US-AriaNeural
bash scripts/build_voiceover.sh INPUT.mp4 out/dub.wav out/INPUT_EN_voiceover.mp4

# 4B) 英文字幕版（遮掉原中文字幕）
python3 scripts/make_srt.py out/transcript.en.json out/transcript.en.srt
bash scripts/burn_subtitles.sh INPUT.mp4 out/transcript.en.srt out/INPUT_EN_subtitled.mp4
```

## 三、常见调整

| 想要的效果 | 怎么调 |
|---|---|
| 换男声/女声 | `tts.py --voice en-US-GuyNeural`（男）/ `en-US-AriaNeural`（女）/ `en-US-JennyNeural` |
| 识别更准 | `transcribe.py --model medium` 或 `large-v3`（更慢更准） |
| 配音太赶/太空 | 翻译时让英文长度更贴近原句；或调 `tts.py --max-tempo 1.5` |
| 原中文字幕没盖住 | `MASK_HEIGHT=180 bash scripts/burn_subtitles.sh ...` |
| 盖黑条太丑 | `MASK_MODE=blur bash scripts/burn_subtitles.sh ...`（改成模糊原字幕） |
| 字幕字太小 | `FONT_SIZE=22 bash scripts/burn_subtitles.sh ...` |

## 四、可选的语音嗓音（edge-tts，免费）

- `en-US-AriaNeural`（女，自然）
- `en-US-JennyNeural`（女，亲和）
- `en-US-GuyNeural`（男，沉稳）
- `en-US-ChristopherNeural`（男，新闻感）
- 列全部：`edge-tts --list-voices | grep en-`

---

## 五、给非技术用户的大白话版 🌱

你给我一个**中国人讲话的视频**，我能给你变出两种英文版本：

1. **英文配音版**：画面不变，但里面讲话的声音换成英文（电脑合成的真人声）。
   - 原理：先把视频里的中文话**听写**成文字 → 我**翻译**成英文 → 电脑用英文**念出来** → 把英文声音**贴回**视频，盖掉原来的中文声音。

2. **英文字幕版**：画面下面出现英文字幕，原来烧死在画面里的中文字幕被**盖掉**（盖黑条或打码模糊）。
   - 适合你想保留原声、只加英文字幕的情况。

你要做的只有一件事：告诉我"**要配音版还是字幕版，还是两个都要**"，剩下的我来跑。

> ⚠️ 注意：这套要在**你自己的电脑**上跑（需要联网下载语音）。云端会话里网络受限，可能合成不了声音。
