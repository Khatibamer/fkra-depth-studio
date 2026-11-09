---
name: fkra-text-above-head
description: Text, labels and frames that sit ON TOP of the person's head and follow it as they move — name tags, titles, thought labels, crowns of words, focus brackets on the face (نص فوق الراس، عنوان بيلحق الراس، اسم فوق الشخص، تتبع الوجه). Use when a label should stay glued to the speaker's head or face; renders with fkra-depth-montage head tracking.
---

# Text above the head (نص فوق الراس بيلحق الحركة)

`analyze` finds the **top of the hair** every frame (`head`) and the face box (`face`), smoothed
and gap-filled. Anchor any layer to them and it moves with the speaker.
Engine: `fkra-depth-montage`.

## Looks

**1. Title riding on the head**
```json
{"type": "text", "text": "*المدير* التنفيذي", "size": 0.06, "anchor_to": "head",
 "offset": [0, -0.015], "in": "pop", "start": 0.5, "end": 3.5}
```
With `anchor_to: head` the block's **bottom** sits on the hair (`anchor: bottom` is automatic).
`offset y` negative = higher.

**2. Highlight tag above the head** (name / role / "me in 2020")
```json
{"type": "text", "text": "*أنا قبل سنة*", "size": 0.055, "accent_style": "box",
 "anchor_to": "head", "offset": [0, -0.02], "in": "pop", "start": 4, "end": 6.5}
```

**3. Thought / reaction word, floating**
```json
{"type": "text", "text": "ليش؟", "size": 0.07, "anchor_to": "head", "offset": [0.12, -0.03],
 "float": [0.006, 2], "in": "pop", "start": 7, "end": 9}
```
(Cairo has no emoji glyphs — for an emoji use an `image` layer with a PNG sticker.)

**4. Focus brackets on the face** (attention / "look at this face")
```json
{"type": "shape", "shape": "corners", "color": "#FFFFFF", "width": 0.007, "margin": 0.35,
 "start": 3, "end": 5}
```

**5. Word crown** — 3 small words orbiting just above the hair:
```json
{"type": "orbit", "items": ["AI", "Video", "Code"], "anchor_to": "head", "offset": [0, -0.02],
 "rx": 0.22, "ry": 0.025, "size": 0.04, "speed": 0.18, "ring": false, "start": 9, "end": 12}
```

**6. Arrow from a label to the face**
```json
{"type": "text", "text": "*هون* المشكلة", "size": 0.06, "pos": [0.25, 0.1], "start": 12, "end": 14, "in": "slide"},
{"type": "shape", "shape": "arrow", "from": [0.25, 0.15], "to": "face", "start": 12.2, "end": 14, "in_dur": 0.5}
```

## Rules

1. **Leave headroom**: if the head is already near the top (hair within 8% of the frame top), the safe
   margin clamps the text and it will overlap the hair — use a side label or the top band instead.
2. Short labels only (1–3 words); they move, so long text becomes unreadable.
3. Tracking is smoothed (no jitter) but lags fast head-whips slightly — avoid on very fast movement,
   or end the layer before the whip.
4. Check `face_seen` in `track.json` across the layer's time range; where the face isn't detected, the
   anchor holds/interpolates the last position.
5. Don't show above-head text together with big behind-text (same space).
