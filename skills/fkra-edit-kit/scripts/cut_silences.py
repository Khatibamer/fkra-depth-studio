#!/usr/bin/env python3
"""Remove dead air from a talking-head video with ffmpeg silencedetect.

Usage:
  cut_silences.py in.mp4 out.mp4 [--noise -35] [--min-silence 0.45] [--pad 0.12] [--dry-run]

--pad keeps a little breathing room around speech so cuts don't clip consonants.
--dry-run prints the keep-segments as JSON without rendering.
"""
import argparse
import json
import re
import subprocess


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    ).stdout
    return float(out.strip())


def silences(path, noise, min_silence):
    log = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", path, "-af",
         f"silencedetect=noise={noise}dB:d={min_silence}", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    return list(zip(starts, ends + [None] * (len(starts) - len(ends))))


def keep_segments(total, sil, pad):
    keep, cur = [], 0.0
    for s, e in sil:
        e = total if e is None else e
        seg_end = min(s + pad, total)
        if seg_end - cur > 0.05:
            keep.append((round(cur, 3), round(seg_end, 3)))
        cur = max(e - pad, seg_end)
    if total - cur > 0.05:
        keep.append((round(cur, 3), round(total, 3)))
    return keep


def render(src, dst, keep):
    parts = []
    for i, (s, e) in enumerate(keep):
        parts.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[v{i}];"
                     f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS[a{i}];")
    streams = "".join(f"[v{i}][a{i}]" for i in range(len(keep)))
    graph = "".join(parts) + f"{streams}concat=n={len(keep)}:v=1:a=1[v][a]"
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", src,
         "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", dst],
        check=True,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("src")
    p.add_argument("dst")
    p.add_argument("--noise", type=float, default=-35)
    p.add_argument("--min-silence", type=float, default=0.45)
    p.add_argument("--pad", type=float, default=0.12)
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    total = duration(a.src)
    keep = keep_segments(total, silences(a.src, a.noise, a.min_silence), a.pad)
    kept = sum(e - s for s, e in keep)
    print(json.dumps({"duration": round(total, 2), "kept": round(kept, 2),
                      "removed": round(total - kept, 2), "segments": keep}))
    if not a.dry_run and keep:
        render(a.src, a.dst, keep)


if __name__ == "__main__":
    main()
