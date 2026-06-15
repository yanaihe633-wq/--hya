#!/usr/bin/env bash
# Extract a clean mono 16kHz WAV from a video, suitable for speech recognition.
# Usage: extract_audio.sh INPUT.mp4 OUT.wav
set -euo pipefail

IN="${1:?usage: extract_audio.sh INPUT.mp4 OUT.wav}"
OUT="${2:?usage: extract_audio.sh INPUT.mp4 OUT.wav}"

mkdir -p "$(dirname "$OUT")"
ffmpeg -y -i "$IN" -vn -ac 1 -ar 16000 -c:a pcm_s16le "$OUT"
echo "Wrote $OUT"
