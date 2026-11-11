#!/usr/bin/env python3
"""Turn word-level timestamps into a styled .ass subtitle file for burning into video.

Input: JSON list of {"word": str, "start": float, "end": float} (faster-whisper,
whisper.cpp --output-json-full, or ElevenLabs transcription words all map to this).

Usage:
  words_to_ass.py words.json out.ass --style karaoke --width 1080 --height 1920 \
      --font "Cairo" --words-per-line 3
Then:
  ffmpeg -i in.mp4 -vf "ass=out.ass:fontsdir=./fonts" -c:a copy out.mp4
"""
import argparse
import json

# ASS colours are &HAABBGGRR
WHITE = "&H00FFFFFF"
BLACK = "&H00000000"
YELLOW = "&H0000D7FF"
PINK = "&H00B469FF"
CYAN = "&H00FFFF00"
RLM = "\u200f"

STYLES = {
    # name: (fontsize ratio of height, primary, outline colour, outline, shadow, bold, alignment, margin_v ratio, highlight)
    "karaoke": (0.045, WHITE, BLACK, 4, 0, 1, 2, 0.22, YELLOW),
    "cinematic": (0.032, WHITE, BLACK, 1, 2, 0, 2, 0.12, None),
    "neon": (0.048, WHITE, PINK, 3, 0, 1, 5, 0.0, CYAN),
    "stomp": (0.075, WHITE, BLACK, 6, 0, 1, 5, 0.0, YELLOW),
}


def ts(t):
    t = max(t, 0)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def clean(w):
    return w.strip().replace("{", "(").replace("}", ")")


def has_arabic(text):
    return any("\u0600" <= ch <= "\u06ff" for ch in text)


def group(words, n, max_gap=0.6):
    """Split into lines of up to n words, breaking early on pauses."""
    lines, cur = [], []
    for w in words:
        if cur and (len(cur) >= n or w["start"] - cur[-1]["end"] > max_gap):
            lines.append(cur)
            cur = []
        cur.append(w)
    if cur:
        lines.append(cur)
    return lines


def build(words, style, width, height, font, n, upper, name="Default"):
    size_r, primary, outline_c, outline, shadow, bold, align, mv_r, hl = STYLES[style]
    size = int(height * size_r)
    mv = int(height * mv_r)
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: {name},{font},{size},{primary},{primary},{outline_c},&H80000000,{-1 if bold else 0},0,0,0,100,100,0,0,1,{outline},{shadow},{align},60,60,{mv},-1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    fmt = (lambda s: s.upper()) if upper else (lambda s: s)

    if style == "stomp":
        # One big word at a time that pops in.
        for w in words:
            pop = r"{\fscx130\fscy130\t(0,90,\fscx100\fscy100)}"
            events.append((w["start"], w["end"], pop + fmt(clean(w["word"]))))
    elif hl is None:
        # Cinematic: whole line, soft fade.
        for line in group(words, n):
            text = " ".join(fmt(clean(w["word"])) for w in line)
            events.append((line[0]["start"], line[-1]["end"], r"{\fad(120,120)}" + text))
    else:
        # Karaoke / neon: whole line visible, the spoken word highlighted.
        glow = r"{\blur4}" if style == "neon" else ""
        for line in group(words, n):
            for i, w in enumerate(line):
                end = line[i + 1]["start"] if i + 1 < len(line) else w["end"]
                parts = []
                for j, x in enumerate(line):
                    t = fmt(clean(x["word"]))
                    if j == i:
                        t = rf"{{\c{hl}\fscx110\fscy110}}{t}{{\c{primary}\fscx100\fscy100}}"
                    parts.append(t)
                events.append((w["start"], end, glow + " ".join(parts)))

    # A line that starts with a Latin word ("Google أعلنت") would get an LTR base
    # direction; a leading RLM keeps Arabic lines right-to-left.
    body = "".join(
        f"Dialogue: 0,{ts(s)},{ts(e)},{name},,0,0,0,,{RLM if has_arabic(t) else ''}{t}\n"
        for s, e, t in events if e > s
    )
    return header + body


def main():
    p = argparse.ArgumentParser()
    p.add_argument("words")
    p.add_argument("out")
    p.add_argument("--style", choices=sorted(STYLES), default="karaoke")
    p.add_argument("--width", type=int, default=1080)
    p.add_argument("--height", type=int, default=1920)
    p.add_argument("--font", default="Cairo")
    p.add_argument("--words-per-line", type=int, default=3)
    p.add_argument("--upper", action="store_true", help="uppercase Latin text")
    p.add_argument("--name", default="Default", help="style name; use different names to merge files")
    a = p.parse_args()
    with open(a.words, encoding="utf-8") as f:
        words = [w for w in json.load(f) if w.get("word", "").strip()]
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(build(words, a.style, a.width, a.height, a.font, a.words_per_line, a.upper, a.name))


if __name__ == "__main__":
    main()
