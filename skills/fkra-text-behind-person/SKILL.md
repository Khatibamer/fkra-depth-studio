---
name: fkra-text-behind-person
description: Typography and shapes placed BEHIND the person in a video — giant words the head covers, a colour circle behind the head, hollow outline words, gradient titles, ghost trails (تيبوغرافي خلف الشخص، كلمة كبيرة ورا الراس، دائرة ورا الشخص، نص مخفي جزئياً). Use when the user wants the "text behind me" depth look for a hook, title or keyword; renders with fkra-depth-montage.
---

# Typography behind the person (تيبوغرافي خلف الشخص)

The person cuts through the letters, so the text reads as part of the scene. It works best
for the **hook (0–3 s)**, a **chapter title** or **one keyword** the whole video is about.

Engine and workflow: `fkra-depth-montage` (analyze → plan → preview → render).
All layers here use `"z": "behind"`.

## Looks

**1. Giant title over the shoulders** (the classic hook)
```json
{"type": "text", "text": "فكرة\n*AI*", "fit": 0.95, "weight": 900, "line_spacing": 0.9,
 "z": "behind", "pos": [0.5, 0.2], "start": 0, "end": 2.8, "in": "zoom", "out": "fade"}
```
Pair it with `{"type": "background", "start": 0, "end": 2.8, "dim": 0.35, "desat": 0.3}` so the
letters pop and the background calms down.

**2. Colour circle behind the head** (portrait / thumbnail look)
```json
{"type": "shape", "shape": "circle", "anchor_to": "face", "radius": 0.36, "color": "accent",
 "z": "behind", "in": "pop", "start": 0, "end": 3}
```
Follows the face. Add `"react": 0.08` for a subtle pulse on the voice.

**3. Hollow outline word** (premium / fashion)
```json
{"type": "text", "text": "SECRET", "fit": 0.9, "hollow": true, "stroke": 0.006,
 "stroke_color": "accent", "z": "behind", "pos": [0.5, 0.22], "in": "fade", "start": 3, "end": 6}
```

**4. Gradient stack + rise reveal** (stat or promise)
```json
{"type": "text", "text": "سرعة\n*×10*", "fit": 0.8, "gradient": ["#FFFFFF", "#FFC400"],
 "z": "behind", "pos": [0.5, 0.15], "in": "rise", "stagger": 0.12, "start": 6, "end": 9}
```

**5. Background replaced + title** (studio look from any room)
```json
{"type": "background", "gradient": ["#120A2A", "#000000"], "replace": 0.9, "start": 0, "end": 4},
{"type": "text", "text": "*٣* أسرار", "fit": 0.85, "z": "behind", "pos": [0.5, 0.15], "start": 0, "end": 4, "in": "zoom"}
```

**6. Ghost trail** (energy on a turn or gesture)
```json
{"type": "echo", "delays": [3, 6, 9], "start": 4.0, "end": 5.5}
```

**7. Parallax depth** — add `"parallax": 0.25` to any behind layer: it drifts opposite to the head,
which sells the 3D feel when the speaker moves.

## Rules

1. **≤ 50% hidden.** Run `preview` on the layer's middle second: it prints how much of the text
   the person covers. Over 50% → move it up (`pos y` 0.12–0.25), make it wider (`fit`), or shorten it.
2. **1–2 words, max 2 lines.** It's a poster, not a sentence. The full sentence belongs in captions.
3. **Weight 800–900**, `line_spacing` 0.85–0.95, and the accent colour on one word only.
4. **Contrast**: dim/desaturate the background (`background dim 0.3–0.5`) or use the circle — never put
   white text behind on a bright wall without one of them.
5. Enter with `zoom` or `rise`, exit with `fade` on the next beat. Hold ≥ 1.5 s.
6. Don't combine with above-head text at the same moment (same space). A front caption is fine.
7. If the speaker walks out of frame, end the layer before they leave.
