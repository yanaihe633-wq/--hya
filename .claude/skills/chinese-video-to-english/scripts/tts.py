#!/usr/bin/env python3
"""Build a full English dub track from translated, time-stamped segments.

For each segment it synthesizes speech with edge-tts, then fits that audio to
the segment's [start, end] slot (gentle time-stretch, clamped for quality) and
lays it on a silent timeline so lip-sync does not drift.

Usage:
    tts.py SEGMENTS.en.json OUT.wav [--voice en-US-AriaNeural]
                                    [--min-tempo 0.6] [--max-tempo 1.7]
"""
import argparse
import asyncio
import json
import os
import subprocess
import sys
import tempfile

SR = 44100


def run(cmd):
    subprocess.run(cmd, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", path])
    return float(out.strip())


def silence(seconds, path):
    seconds = max(seconds, 0.0)
    run(["ffmpeg", "-y", "-f", "lavfi",
         "-i", f"anullsrc=r={SR}:cl=mono", "-t", f"{seconds:.3f}",
         "-c:a", "pcm_s16le", path])


async def synth(text, voice, out_mp3):
    import edge_tts
    await edge_tts.Communicate(text, voice).save(out_mp3)


def fit_segment(raw_mp3, target, out_wav, min_tempo, max_tempo):
    """Stretch raw audio toward `target` seconds, then pad/trim to exactly target."""
    raw = max(duration(raw_mp3), 0.05)
    tempo = raw / max(target, 0.1)            # >1 => speed up to fit a shorter slot
    tempo = min(max(tempo, min_tempo), max_tempo)
    af = f"atempo={tempo:.4f},apad"
    run(["ffmpeg", "-y", "-i", raw_mp3, "-af", af,
         "-t", f"{target:.3f}", "-ar", str(SR), "-ac", "1",
         "-c:a", "pcm_s16le", out_wav])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("segments")
    ap.add_argument("out")
    ap.add_argument("--voice", default="en-US-AriaNeural")
    ap.add_argument("--min-tempo", type=float, default=0.6)
    ap.add_argument("--max-tempo", type=float, default=1.7)
    args = ap.parse_args()

    voice = os.environ.get("VOICE", args.voice)

    with open(args.segments, encoding="utf-8") as f:
        segs = [s for s in json.load(f) if (s.get("text") or "").strip()]
    segs.sort(key=lambda s: float(s["start"]))
    if not segs:
        sys.exit("No segments with text.")

    tmp = tempfile.mkdtemp(prefix="cv2e_tts_")
    pieces = []          # ordered list of wav paths to concat
    cursor = 0.0         # current end position on the timeline

    for i, s in enumerate(segs):
        start = float(s["start"])
        end = float(s["end"])
        target = max(end - start, 0.4)
        text = s["text"].strip()

        gap = start - cursor
        if gap > 0.02:
            sil = os.path.join(tmp, f"gap_{i}.wav")
            silence(gap, sil)
            pieces.append(sil)

        raw = os.path.join(tmp, f"seg_{i}.mp3")
        try:
            asyncio.run(synth(text, voice, raw))
        except ImportError:
            sys.exit("ERROR: install edge-tts  ->  pip install edge-tts")

        fitted = os.path.join(tmp, f"fit_{i}.wav")
        fit_segment(raw, target, fitted, args.min_tempo, args.max_tempo)
        pieces.append(fitted)
        cursor = max(start, cursor) + target

    listfile = os.path.join(tmp, "concat.txt")
    with open(listfile, "w") as f:
        for p in pieces:
            f.write(f"file '{p}'\n")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
         "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", args.out])

    print(f"[{voice}] {len(segs)} segments, ~{cursor:.1f}s dub -> {args.out}")


if __name__ == "__main__":
    main()
