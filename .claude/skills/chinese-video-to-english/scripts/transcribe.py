#!/usr/bin/env python3
"""Transcribe speech to timestamped segments.

Prefers faster-whisper (fast, light on CPU); falls back to openai-whisper.
Output is a JSON array: [{"index", "start", "end", "text"}, ...]

Usage:
    transcribe.py AUDIO.wav OUT.json [--language zh] [--model small]
"""
import argparse
import json
import sys


def with_faster_whisper(audio, language, model_size):
    from faster_whisper import WhisperModel
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _info = model.transcribe(
        audio, language=language, vad_filter=True,
        beam_size=5,
    )
    out = []
    for i, s in enumerate(segments, 1):
        text = (s.text or "").strip()
        if not text:
            continue
        out.append({"index": i, "start": round(s.start, 3),
                    "end": round(s.end, 3), "text": text})
    return out


def with_openai_whisper(audio, language, model_size):
    import whisper
    model = whisper.load_model(model_size)
    res = model.transcribe(audio, language=language, verbose=False)
    out = []
    for i, s in enumerate(res.get("segments", []), 1):
        text = (s.get("text") or "").strip()
        if not text:
            continue
        out.append({"index": i, "start": round(float(s["start"]), 3),
                    "end": round(float(s["end"]), 3), "text": text})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("out")
    ap.add_argument("--language", default="zh")
    ap.add_argument("--model", default="small",
                    help="tiny|base|small|medium|large-v3 (bigger = better & slower)")
    args = ap.parse_args()

    segs = None
    try:
        segs = with_faster_whisper(args.audio, args.language, args.model)
        engine = "faster-whisper"
    except ImportError:
        try:
            segs = with_openai_whisper(args.audio, args.language, args.model)
            engine = "openai-whisper"
        except ImportError:
            sys.exit("ERROR: install faster-whisper (pip install faster-whisper) "
                     "or openai-whisper (pip install openai-whisper).")

    # re-index after dropping empties
    for i, s in enumerate(segs, 1):
        s["index"] = i

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(segs, f, ensure_ascii=False, indent=2)

    print(f"[{engine}] {len(segs)} segments -> {args.out}")


if __name__ == "__main__":
    main()
