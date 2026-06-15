#!/usr/bin/env python3
"""Convert a segments JSON ([{index,start,end,text}, ...]) into an SRT file.

Usage: make_srt.py SEGMENTS.json OUT.srt
"""
import argparse
import json


def ts(seconds):
    if seconds < 0:
        seconds = 0
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("segments")
    ap.add_argument("out")
    args = ap.parse_args()

    with open(args.segments, encoding="utf-8") as f:
        segs = json.load(f)

    lines = []
    for i, s in enumerate(segs, 1):
        text = (s.get("text") or "").strip()
        if not text:
            continue
        lines.append(str(i))
        lines.append(f"{ts(float(s['start']))} --> {ts(float(s['end']))}")
        lines.append(text)
        lines.append("")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"{len(segs)} cues -> {args.out}")


if __name__ == "__main__":
    main()
