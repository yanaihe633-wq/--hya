#!/usr/bin/env bash
# Replace a video's audio with the English dub track (video untouched, re-muxed).
# Usage: build_voiceover.sh INPUT.mp4 DUB.wav OUT.mp4
set -euo pipefail

IN="${1:?usage: build_voiceover.sh INPUT.mp4 DUB.wav OUT.mp4}"
DUB="${2:?usage: build_voiceover.sh INPUT.mp4 DUB.wav OUT.mp4}"
OUT="${3:?usage: build_voiceover.sh INPUT.mp4 DUB.wav OUT.mp4}"

mkdir -p "$(dirname "$OUT")"
# Keep original video stream as-is; take audio only from the dub.
ffmpeg -y -i "$IN" -i "$DUB" \
  -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -b:a 192k \
  -shortest "$OUT"
echo "Wrote $OUT"
