---
name: fkra-orbit-around-person
description: Elements that go AROUND the person — words, tools or logos orbiting on a ring that passes behind and in front of the body, neon outline/glow hugging the silhouette, pulse rings, floating particles in depth (حوالين الشخص، كلمات بتلف حوالين الشخص، لوغوهات بتدور، هالة، نيون حوالين الجسم). Use for lists of tools/skills, "everything in one place", energy moments or intros; renders with fkra-depth-montage.
---

# Around the person (حوالين الشخص)

The orbit is the signature depth move: items on the far side of the ring pass **behind** the
person (smaller, dimmer), items on the near side pass **in front**. Engine: `fkra-depth-montage`.

## Looks

**1. Tool / skill orbit at chest level** ("I use these 5 tools")
```json
{"type": "orbit", "items": ["Claude", "Code", "Video", "AI", "Motion"],
 "anchor_to": "chest", "rx": 0.42, "ry": 0.06, "speed": 0.12, "start": 3, "end": 7}
```
Logos instead of words: `"items": ["logos/claude.png", "logos/figma.png", …]` (transparent PNGs).

**2. Neon outline** (person glows when the energy goes up)
```json
{"type": "outline", "color": "accent", "width": 0.008, "glow": 0.03, "react": 0.6, "start": 3, "end": 7}
```
`react` makes the stroke breathe with the voice. Sticker look: `"glow": 0, "width": 0.015, "color": "#FFFFFF"`.

**3. Pulse rings from the face** (signal / broadcast / "listen")
```json
{"type": "shape", "shape": "ring_pulse", "anchor_to": "face", "z": "behind",
 "r0": 0.15, "r1": 0.55, "period": 1.4, "count": 3, "start": 8, "end": 11}
```

**4. Particles in two depths** (premium ambience)
```json
{"type": "shape", "shape": "particles", "z": "behind", "count": 60, "start": 0, "end": 12},
{"type": "shape", "shape": "particles", "z": "front", "count": 12, "size": 0.009, "seed": 9, "opacity": 0.7, "start": 0, "end": 12}
```

**5. Tilted halo around the head** (title moment)
```json
{"type": "orbit", "items": ["01", "02", "03"], "anchor_to": "head", "offset": [0, -0.01],
 "rx": 0.3, "ry": 0.03, "tilt": -14, "size": 0.04, "start": 0, "end": 3}
```

## Rules

1. **3–6 items.** More than 6 and the near side crowds the face.
2. Keep the ring at **chest level** (`anchor_to: chest`, the default) for lists; a head-level ring
   only for short title moments, and lift it above the hair (`anchor_to: head`, small `ry`) — a ring
   through the face puts the front items over the eyes and mouth.
3. `speed` 0.08–0.18 rev/s: slow enough to read each item as it passes in front.
4. Time it to the speech: orbit starts when they start listing, ends on the last item.
5. Outline + orbit together is the maximum (2 depth effects). No behind-text at the same time.
6. `rx` ≤ 0.45 so the pills don't get clipped by the frame edge.
