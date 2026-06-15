#!/usr/bin/env bash
# Mask the original burned-in Chinese subtitles, then burn English subtitles.
# Usage: burn_subtitles.sh INPUT.mp4 ENGLISH.srt OUT.mp4
#
# Env knobs:
#   MASK_HEIGHT  pixels covered at the bottom (default: ~18% of video height)
#   MASK_MODE    box | blur  (default: box)
#   MASK_COLOR   fill color for box mode (default: black)
#   FONT_SIZE    subtitle font size (default: 18)
set -euo pipefail

IN="${1:?usage: burn_subtitles.sh INPUT.mp4 ENGLISH.srt OUT.mp4}"
SRT="${2:?usage: burn_subtitles.sh INPUT.mp4 ENGLISH.srt OUT.mp4}"
OUT="${3:?usage: burn_subtitles.sh INPUT.mp4 ENGLISH.srt OUT.mp4}"

MASK_MODE="${MASK_MODE:-box}"
MASK_COLOR="${MASK_COLOR:-black}"
FONT_SIZE="${FONT_SIZE:-18}"

mkdir -p "$(dirname "$OUT")"

# Default mask height = 18% of the source height if not given.
if [ -z "${MASK_HEIGHT:-}" ]; then
  H="$(ffprobe -v quiet -select_streams v:0 -show_entries stream=height -of csv=p=0 "$IN")"
  MASK_HEIGHT="$(python3 -c "print(int(round($H*0.18)))")"
fi

# escape the srt path for ffmpeg's subtitles filter (colon/backslash safe enough for typical paths)
SRT_ESC="$(printf '%s' "$SRT" | sed -e 's/\\/\\\\/g' -e "s/'/\\\\'/g" -e 's/:/\\:/g')"

STYLE="FontName=Arial,FontSize=${FONT_SIZE},PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,MarginV=20"

if [ "$MASK_MODE" = "blur" ]; then
  # Blur the bottom strip, overlay it back, then burn subtitles.
  VF="split[full][crop];[crop]crop=iw:${MASK_HEIGHT}:0:ih-${MASK_HEIGHT},boxblur=20:2[bl];[full][bl]overlay=0:H-${MASK_HEIGHT}[masked];[masked]subtitles='${SRT_ESC}':force_style='${STYLE}'"
else
  # Cover the bottom strip with a solid box, then burn subtitles.
  VF="drawbox=x=0:y=ih-${MASK_HEIGHT}:w=iw:h=${MASK_HEIGHT}:color=${MASK_COLOR}:t=fill,subtitles='${SRT_ESC}':force_style='${STYLE}'"
fi

ffmpeg -y -i "$IN" -vf "$VF" -c:a copy "$OUT"
echo "Wrote $OUT  (mask=${MASK_MODE} height=${MASK_HEIGHT}px)"
