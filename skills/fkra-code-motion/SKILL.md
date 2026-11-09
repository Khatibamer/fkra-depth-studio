---
name: fkra-code-motion
description: Code on screen as motion design — a code-editor window that types itself with syntax colours, a terminal running commands, falling code rain behind the person (كودات، كود بينكتب، تيرمينال، برمجة على الفيديو، ماتريكس ورا الشخص). Use for AI/tech/programming content, "I built this with Claude Code", prompts and automation videos; renders with fkra-depth-montage.
---

# Code motion (كود بيتحرك)

Engine: `fkra-depth-montage`. Three layers: `code` (editor or terminal panel), `code_rain`
(behind the person), and normal `text` for the Arabic explanation (the mono font has no Arabic).

## Looks

**1. Editor window typing in front** (show the actual code / prompt)
```json
{"type": "code", "theme": "fkra", "title": "montage.py", "size": 0.03, "pos": [0.5, 0.74],
 "code": "from fkra import montage\n\nvideo = montage(\"reel.mp4\")\nvideo.text_behind(\"AI\")\nvideo.render()  # done",
 "cps": 30, "start": 9, "end": 13}
```
Themes: `editor` (GitHub dark), `terminal` (green), `fkra` (black + yellow brand border).

**2. Terminal running a command** (Claude Code / CLI demos)
```json
{"type": "code", "theme": "terminal", "size": 0.028, "pos": [0.5, 0.18], "cps": 35,
 "code": "claude \"edit my reel\"\n> analysing faces... done\n> text behind person: ok", "start": 2, "end": 6}
```

**3. Code rain behind the person** (AI / hacker energy)
```json
{"type": "background", "dim": 0.55, "start": 0, "end": 3},
{"type": "code_rain", "color": "#39FF88", "opacity": 0.75, "start": 0, "end": 3}
```
Brand version: `"color": "accent"`. Calmer: `"density": 0.4, "speed": 0.6`.

**4. Code panel behind the person** (they "stand in front of" their code)
```json
{"type": "code", "theme": "editor", "z": "behind", "width": 0.95, "pos": [0.5, 0.35],
 "max_lines": 14, "size": 0.026, "code": "…long file…", "cps": 60, "start": 0, "end": 5}
```
Dim the background (`dim 0.4`) so the panel reads around the head.

**5. Prompt card** — the exact prompt typed, then an Arabic caption explaining it:
```json
{"type": "code", "theme": "fkra", "title": "prompt", "code": "Make a 30s reel:\n- hook in 1s\n- text behind me", "pos": [0.5, 0.2], "start": 4, "end": 8},
{"type": "text", "text": "هيدا *البرومبت* كامل", "size": 0.06, "pos": [0.5, 0.76], "start": 5, "end": 8, "in": "rise"}
```

## Rules

1. **Typing speed matches speech**: `cps` 25–40 while they talk over it; whole thing typed before
   they move on. Total chars ÷ cps = typing seconds.
2. ≤ 8 visible lines in front (`max_lines`); keep lines ≤ 34 characters at `size 0.03` on 9:16.
3. Real, correct code only — viewers screenshot it. Never invent an API in a "real" demo.
4. Panel in the top band or lower third, never over the face. Behind-panels need `dim`.
5. Code rain is a mood, not information: max 3 s, once or twice per video.
6. Add a keyboard-typing SFX under the typing and a soft pop when the panel appears.
