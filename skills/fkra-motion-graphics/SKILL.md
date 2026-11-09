---
name: fkra-motion-graphics
description: Motion-graphics toolkit over live video — arrows that draw themselves, bursts, underlines, pulse rings, tech grids, particles, background restyle (dim, blur, gradient, spotlight), camera punch-in tracking the face, shake and flash (موشن جرافيك، أسهم، خطوط، انفجار، جريد، خلفية، زوم على الوجه، اهتزاز، فلاش). Use to add designed accents and camera energy to a talking-head video; renders with fkra-depth-montage.
---

# Motion graphics over the person (موشن جرافيك)

Accents that **point, frame and punctuate** — never decoration for its own sake.
Engine: `fkra-depth-montage` (`shape`, `background`, `camera` layers).

## Accents

| Need | Layer |
|---|---|
| Point at something they mention | `{"type":"shape","shape":"arrow","from":[0.2,0.3],"to":"face","in_dur":0.5}` |
| Underline the key word | `{"type":"shape","shape":"underline","pos":[0.5,0.79],"length":0.5}` (sweeps right→left) |
| Punchline impact | `{"type":"shape","shape":"burst","anchor_to":"face","r0":0.2,"r1":0.38}` + camera shake |
| "Listen" / signal | `{"type":"shape","shape":"ring_pulse","anchor_to":"face","z":"behind"}` |
| Frame the face | `{"type":"shape","shape":"corners"}` |
| Tech backdrop | `{"type":"shape","shape":"grid","strength":0.4}` (behind) |
| Ambience | `{"type":"shape","shape":"particles","count":60}` (behind) |

## Background restyle (only behind the person)

```jsonc
{"type": "background", "dim": 0.4, "desat": 0.5, "start": 0, "end": 3}          // focus
{"type": "background", "blur": 0.02, "start": 3, "end": 6}                        // fake depth of field
{"type": "background", "spotlight": 0.5, "start": 6, "end": 9}                    // stage light on the face
{"type": "background", "gradient": ["#1A0F3D", "#000000"], "replace": 0.9}        // studio from any room
{"type": "background", "image": "city.jpg", "replace": 1.0}                       // new location
{"type": "background", "tint": "#FFC40033"}                                       // brand wash
```

## Camera (applied to the finished frame)

```jsonc
{"type": "camera", "zoom": 1.12, "start": 6.0, "end": 7.5, "in_dur": 0.25, "out_dur": 0.4}   // punch-in on the face
{"type": "camera", "shake": 0.012, "start": 7.4, "end": 7.7}                                // impact shake
{"type": "camera", "flash": 0.7, "start": 10.0, "end": 10.3}                                // white flash transition
```
Punch-in tracks the face (`anchor_to` defaults to `face`), so it also hides jump cuts.

## Rules

1. **One accent at a time** in the point of focus; something visual changes every 2–3 s.
2. Arrows/underlines draw over 0.3–0.5 s, hold, then fade — they must point at something real.
3. Shake ≤ 0.3 s and never twice in a row; flash only on a cut or section change.
4. Background restyles last a whole beat (≥ 2 s); toggling every second looks broken.
5. Brand colours: `accent` for accents, white for frames, never more than 2 colours per shot.
6. Every accent gets an SFX (whoosh for arrows, impact for burst/shake, shimmer for particles).
