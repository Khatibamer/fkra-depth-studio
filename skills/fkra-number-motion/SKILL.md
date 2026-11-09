---
name: fkra-number-motion
description: Moving numbers — counters that roll up to the figure being said, percentages with progress bars, money and follower counts, Arabic-Indic digits, giant numbers behind the person (أرقام بتتحرك، عداد، نسبة مئوية، شريط تقدم، رقم كبير ورا الشخص، أرقام عربية). Use whenever a number, price, stat or result is spoken in a video; renders with fkra-depth-montage.
---

# Number motion (أرقام بتتحرك)

Rule from `fkra-motion-library`: **every number said aloud gets a counter.**
Engine: `fkra-depth-montage` — `counter` (a text layer whose value rolls) + `shape bar`.

## Looks

**1. Big counter in the lower third** (views, followers, sales)
```json
{"type": "counter", "from": 0, "to": 10000, "text": "+{n}", "size": 0.13, "pos": [0.5, 0.76],
 "dur": 1.3, "start": 6.0, "end": 9.0},
{"type": "text", "text": "مشاهدة *بأسبوع*", "size": 0.06, "pos": [0.5, 0.84], "in": "rise", "start": 6.2, "end": 9.0}
```
Start the layer on the word *before* the number so it lands as they say it.

**2. Percentage + progress bar**
```json
{"type": "counter", "from": 0, "to": 87, "text": "{n}%", "size": 0.16, "pos": [0.5, 0.72], "start": 0.5, "end": 3},
{"type": "shape", "shape": "bar", "value": 0.87, "pos": [0.5, 0.81], "dur": 1.2, "start": 0.5, "end": 3},
{"type": "text", "text": "من المشاهدين *بيكملوا*", "size": 0.055, "pos": [0.5, 0.87], "in": "rise", "start": 0.6, "end": 3}
```
Keep counter `dur` = bar `dur` so they land together.

**3. Money with decimals**
```json
{"type": "counter", "from": 0, "to": 2.5, "decimals": 1, "text": "${n}M", "size": 0.14,
 "pos": [0.5, 0.74], "dur": 1.0, "start": 3, "end": 6}
```

**4. Arabic-Indic digits** (Gulf / formal audience): add `"arabic_digits": true` → ١٠٬٠٠٠.

**5. Giant number behind the person** (the number IS the hook)
```json
{"type": "counter", "from": 0, "to": 300, "text": "{n}", "fit": 0.9, "weight": 900, "z": "behind",
 "pos": [0.5, 0.2], "dur": 1.4, "start": 0, "end": 3},
{"type": "background", "dim": 0.4, "start": 0, "end": 3}
```

**6. Impact landing**: add a camera punch + burst at the landing moment (`start + delay + dur`):
```json
{"type": "camera", "zoom": 1.1, "start": 7.4, "end": 8.2, "in_dur": 0.15, "out_dur": 0.4},
{"type": "shape", "shape": "burst", "pos": [0.5, 0.76], "r0": 0.12, "r1": 0.3, "start": 7.4, "end": 8}
```

**7. Countdown** — `from` bigger than `to` (`"from": 10, "to": 0, "ease": "linear", "dur": 10`).

## Rules

1. **The exact number said.** Never round up or invent stats; if they say "around 10K" show `~10K`.
2. Roll 0.8–1.5 s with `ease: out` (fast then settles). `land_pop` gives the little bump at the end.
3. One counter on screen at a time; a second number waits until the first one leaves.
4. Units are part of the template (`"+{n}K"`, `"{n}%"`, `"{n}$"`), so the width is fixed while it rolls.
5. SFX: tick/riser while rolling, an impact on landing.
6. Counters behind the person follow the behind-text rule: ≤ 50% hidden (check `preview`).
