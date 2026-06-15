#!/usr/bin/env bash
# Check that all tools needed by chinese-video-to-english are installed.
set -uo pipefail

ok=1
need() {
  if command -v "$1" >/dev/null 2>&1; then
    echo "  ✅ $1"
  else
    echo "  ❌ $1  — $2"
    ok=0
  fi
}
pymod() {
  if python3 -c "import $1" >/dev/null 2>&1; then
    echo "  ✅ python: $1"
    return 0
  fi
  return 1
}

echo "Checking command-line tools:"
need ffmpeg  "install ffmpeg (macOS: brew install ffmpeg / Ubuntu: apt install ffmpeg)"
need ffprobe "comes with ffmpeg"
need python3 "install Python 3"

echo "Checking Python packages:"
if ! pymod edge_tts; then
  echo "  ❌ python: edge_tts  — pip install edge-tts"
  ok=0
fi
if pymod faster_whisper || pymod whisper; then
  :
else
  echo "  ❌ python: faster_whisper OR whisper  — pip install faster-whisper   (or: pip install openai-whisper)"
  ok=0
fi

echo
if [ "$ok" -eq 1 ]; then
  echo "All set. 全部就绪 ✅"
else
  echo "Some dependencies are missing — install them and re-run. 还缺东西，按上面提示装好再跑。"
  exit 1
fi
