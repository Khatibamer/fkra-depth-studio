---
name: fkra-text-front-person
description: Motion text and cards IN FRONT of the person — kinetic word pops, highlight-box keywords, title cards, side labels, floating proof screenshots (نص أمام الشخص، كلمات بتطلع مع الكلام، هايلايت، بطاقة عنوان، سكرينشوت عائم). Use when a talking-head video needs headline text, punchline words or proof images over the speaker; renders with fkra-depth-montage.
---

# Typography in front of the person (نص وبطاقات أمام الشخص)

Front layers carry the **information**: headline, punchline word, proof. They sit over the
person, so placement matters more than style. Engine: `fkra-depth-montage`, `"z": "front"` (default).

## Zones (9:16)

```
┌───────────────┐  0.06–0.18  TOP BAND: headline / chapter
│               │
│     face      │  0.20–0.50  keep clear (eyes + mouth)
│               │
│ side    side  │  0.45–0.65  side labels, x 0.2 or 0.8 (away from the face)
│               │  0.68–0.80  BIG word / number
│   captions    │  0.80–0.90  captions (fkra-embedded-captions)
└───────────────┘
```

## Looks

**1. Word pop on the beat** (hook / punchline)
```json
{"type": "text", "text": "ما *حدا* بيقلك هيك", "size": 0.075, "pos": [0.5, 0.12],
 "in": "pop", "stagger": 0.07, "start": 0.2, "end": 2.6, "out": "pop"}
```

**2. Highlighter card on the key word**
```json
{"type": "text", "text": "مونتاج *بدون* تطبيقات", "size": 0.065, "accent_style": "box",
 "pos": [0.5, 0.72], "in": "pop", "start": 1.0, "end": 3.5}
```

**3. Title card with a backing box** (chapter / step)
```json
{"type": "text", "text": "الخطوة *١*", "size": 0.07, "box": {"color": "#0B0B12D0", "radius": 0.02},
 "pos": [0.5, 0.12], "in": "rise", "start": 5, "end": 8}
```

**4. Side label + underline** (naming a thing they point at)
```json
{"type": "text", "text": "*الأداة*", "size": 0.06, "pos": [0.78, 0.52], "in": "slide", "start": 9, "end": 11},
{"type": "shape", "shape": "underline", "pos": [0.78, 0.565], "length": 0.25, "start": 9.15, "end": 11}
```

**5. Floating proof screenshot**
```json
{"type": "image", "path": "proof.png", "width": 0.55, "radius": 0.02, "pos": [0.7, 0.7],
 "in": "rise", "float": [0.008, 2.5], "start": 12, "end": 15}
```

**6. Cinematic lower title** (`in: zoom`, thin weight, wide)
```json
{"type": "text", "text": "THE PLAN", "size": 0.09, "weight": 300, "pos": [0.5, 0.75], "in": "zoom", "start": 0, "end": 2}
```

## Rules

1. **Never over the eyes or mouth.** Use the zones above; side labels go on the side away from the face.
2. **One idea per card, ≤ 5 words.** Two lines max. The accent (`*…*`) goes on the single key word.
3. **Enter on the spoken word** (transcript timing), leave on the next beat; hold ≥ 1.2 s.
4. A front word and the captions must not overlap in time *and* zone: move the word to the top band.
5. Mix at most two entrance styles per video (e.g. `pop` for hooks, `rise` for titles).
6. Shadows are on by default — keep them; they keep white text readable on any shirt.
