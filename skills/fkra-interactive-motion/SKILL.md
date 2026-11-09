---
name: fkra-interactive-motion
description: Motion that REACTS to the person — a glowing orb or label glued to the fingertip, bursts and words that pop when they pinch, elements that appear only when a hand is raised, outlines and text that pulse with the voice, parallax that moves with the head (تفاعل، عناصر بتلحق الإيد، فرقعة بالأصابع، تفاعل مع الصوت، حركة مع الراس). Use when the user wants the edit to feel alive and interactive with the speaker's gestures; renders with fkra-depth-montage hand/voice tracking.
---

# Interactive motion (تفاعل مع الشخص)

`analyze` tracks both hands (index tip, thumb, palm, pinch distance), the head and the voice
loudness for every frame, so layers can **respond** instead of just playing on a timer.
Engine: `fkra-depth-montage`.

## Interactions

**1. Magic fingertip** — a glowing orb with a light trail follows the index finger
```json
{"type": "hand_follow", "trail": 12, "color": "accent", "start": 0, "end": 12}
```
With a label (they "hold" the word): add `"text": "AI", "offset": [0, -0.06]`.

**2. Pinch to pop** — each pinch fires a burst and pops the next word at the fingers
```json
{"type": "pinch_burst", "words": ["فكرة", "مونتاج", "نشر"], "color": "accent", "start": 2, "end": 10}
```
Great for "1, 2, 3" lists said with finger gestures. Tune `threshold` (0.15 strict – 0.3 loose).

**3. Show on raised hand** — any layer with `"when": "hand"` fades in while a hand is in frame
```json
{"type": "text", "text": "*٣* خطوات", "size": 0.07, "pos": [0.5, 0.12], "when": "hand", "in": "none", "start": 0, "end": 12}
```
`"when": "no_hand"` does the opposite (hide the caption while they gesture).

**4. Voice-reactive** — `react` scales with loudness (0.1 subtle – 0.4 strong)
```json
{"type": "outline", "glow": 0.03, "react": 0.6, "start": 4, "end": 8},
{"type": "shape", "shape": "circle", "anchor_to": "face", "z": "behind", "radius": 0.34, "react": 0.12, "start": 4, "end": 8}
```

**5. Head parallax** — behind layers drift opposite to the head (`parallax` 0.2–0.4), front layers
with the head (negative values). Instantly reads as 3D.
```json
{"type": "text", "text": "DEPTH", "fit": 0.9, "z": "behind", "pos": [0.5, 0.2], "parallax": 0.3, "start": 0, "end": 4}
```

**6. Hand-pointing arrow** — an arrow from a label to wherever the hand is:
```json
{"type": "shape", "shape": "arrow", "from": [0.2, 0.15], "to": "hand", "start": 5, "end": 7}
```

**7. Text that follows the hand** — any text with `"anchor_to": "hand"` (+ `"when": "hand"`).

## Rules

1. **Check the tracking first**: `track.json` → count frames with `hands` in the time range. Under ~60%
   of frames → use a timed layer instead (an interaction that flickers looks like a bug).
2. Gestures must be **in frame and not too fast**; motion blur kills hand landmarks.
3. One interactive element at a time — the viewer's eye follows the hand.
4. Pinch words must match what they're saying at that moment (transcript timing).
5. `react` on at most two layers; voice pulses on everything feels like a music visualiser.
6. Always `preview` a frame in the middle of the gesture to confirm the anchor lands on the fingers.
