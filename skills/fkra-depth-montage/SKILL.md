---
name: fkra-depth-montage
description: Layered "depth" montage engine — cuts the person out of every frame so text, numbers, code, shapes and logos can sit BEHIND them, IN FRONT of them, AROUND them (orbit) or ABOVE their head and follow them, plus hand/voice-reactive motion. Local Python + ffmpeg, no CapCut/Descript/After Effects (مونتاج طبقات، نص خلف الشخص، أمام الشخص، فوق الراس، حوالين الشخص، موشن جرافيك، أرقام، كود، تفاعل). Use whenever a talking-head or person video needs designed motion layers; the fkra-text-*, fkra-orbit-*, fkra-code-motion, fkra-number-motion, fkra-motion-graphics and fkra-interactive-motion skills all render through it.
---

# FKRA depth montage (مونتاج الطبقات حوالين الشخص)

One analysis pass gives the engine a **person matte** + **face / head-top / hands / voice
tracking**. Every design is then a layer in a `plan.json` with a z-position:

```
background ─► bg layers ─► BEHIND layers ─► 👤 person (matte) ─► FRONT layers ─► post (camera)
```

So "typography behind the person" is just `"z": "behind"`, "above the head" is
`"anchor_to": "head"`, "around the person" is an `orbit` (back half behind, front half in front).

Engine: `scripts/depthfx.py` (+ `fx_core.py`, `fx_analyze.py`, `fx_layers.py`).
Full parameter list: [reference.md](reference.md).

## 0. Setup (once per machine)

```bash
pip install --break-system-packages numpy pillow opencv-python-headless mediapipe
# Linux containers also need: apt-get install -y libegl1 libgles2
```
Models (MediaPipe selfie-multiclass, face, hands) and fonts (Cairo, Tajawal, JetBrains Mono)
download automatically to `~/.cache/fkra-depth/` on first use.

## 1. Workflow

```bash
E=.claude/skills/fkra-depth-montage/scripts/depthfx.py
python3 $E analyze cut.mp4 work/          # → work/mask.mkv + work/track.json  (≈30 fps at 540p)
# write plan.json (see §3) next to work/
python3 $E preview plan.json 1.2 4.0 7.5  # contact sheet PNG at those seconds + occlusion check
python3 $E render plan.json               # → out.mp4 with original audio
python3 $E render plan.json --from 3 --to 6 --out test.mp4   # render a slice
```

1. **Cut first** (`fkra-edit-kit`), then analyse the *cut* file — the matte and tracking are frame-exact
   to the file they were made from. Re-run `analyze` after any re-cut.
2. Transcribe (word timings from `fkra-embedded-captions` §1) and pick the beats.
3. Follow `fkra-motion-library`: choose the designs that fit the video's idea → show the motion
   plan (time → layer → reason) → write `plan.json`.
4. `preview` the key moments and **look at the PNG**. Fix anything the occlusion check warns about.
5. `render`, then grab 2–3 frames from the final file and check them.
6. Captions go last, burned over the render (`fkra-embedded-captions`) — keep them out of the
   zones used by front layers.

## 2. Which design skill for what

| The user wants… | Skill | Engine layer |
|---|---|---|
| Huge typography behind the person, circle behind the head, hollow/gradient words, ghost trail | `fkra-text-behind-person` | `text z:behind`, `shape circle`, `echo` |
| Titles, highlight cards, keyword pops in front | `fkra-text-front-person` | `text z:front`, `image` |
| A label/title that sits on the head and follows it | `fkra-text-above-head` | `text anchor_to:head`, `shape corners` |
| Words/logos orbiting around the person, neon outline | `fkra-orbit-around-person` | `orbit`, `outline`, `ring_pulse` |
| Typing code, terminal, falling code | `fkra-code-motion` | `code`, `code_rain` |
| Counting numbers, %, money, progress bars | `fkra-number-motion` | `counter`, `shape bar` |
| Arrows, bursts, grids, particles, background restyle, punch-in/shake/flash | `fkra-motion-graphics` | `shape`, `background`, `camera` |
| Things that react to the hand, a pinch, the voice, head movement | `fkra-interactive-motion` | `hand_follow`, `pinch_burst`, `when`, `react`, `parallax` |

## 3. plan.json skeleton

```json
{
  "video": "cut.mp4",
  "work": "work",
  "out": "final.mp4",
  "brand": {"accent": "#FFC400", "text": "#FFFFFF", "dark": "#0B0B12"},
  "layers": [
    {"type": "background", "start": 0, "end": 3, "dim": 0.35},
    {"type": "text", "text": "فكرة\n*AI*", "fit": 0.95, "z": "behind", "pos": [0.5, 0.2],
     "start": 0, "end": 3, "in": "zoom", "weight": 900, "line_spacing": 0.9},
    {"type": "counter", "from": 0, "to": 10000, "text": "+{n}", "size": 0.13,
     "pos": [0.5, 0.78], "start": 6, "end": 9}
  ]
}
```
Paths are relative to the plan file. Positions/sizes ≤ 1.5 are **fractions of the frame**
(`pos [0.5, 0.2]` = centre, 20% from the top; `size 0.08` = 8% of width), so a plan works at
540p preview and 1080p final. Colours accept `#RRGGBB(AA)` or brand keys (`"accent"`, `"text"`…).
`*word*` in any text = accent colour (or a highlight box with `"accent_style": "box"`).

## 4. Rules that keep it looking designed

1. **Max 2 depth tricks on screen at once** (e.g. text behind + one front element). Never
   behind-text and above-head text at the same moment — they fight for the same space.
2. **Behind-text must stay readable**: put it where the head/shoulders cover ≤ 50% of it
   (usually `pos y 0.15–0.3`, above the shoulders). `preview` prints the hidden % — fix any WARNING.
3. **Front layers live in the lower third or the top band**, never over the eyes/mouth.
4. **Arabic is RTL**: word order, sweeps, underline and bars already run right→left; keep
   `"dir": "rtl"` defaults. Latin-only lines run left→right automatically.
5. Every layer has a **reason in the speech** (a number → counter, "code" → code panel, a
   list → orbit/cards). Timings come from the transcript, not guesses.
6. Hold readable text ≥ 1.2 s; enter on the word, leave on the next beat.
7. Add an SFX for every entrance (whoosh / pop / riser) — see `fkra-motion-library` §1.5.

## 5. Quality, speed, limits

- Speed: ~25 fps at 540×960, ~6–8 fps at 1080×1920 on CPU. Iterate with `preview` and
  `--from/--to`; render the full piece once.
- Matte: MediaPipe selfie-multiclass + guided-filter edge refine + temporal smoothing. Good for
  talking heads and hair; fast-moving hands may smear. For a cleaner matte from a heavier model
  (Robust Video Matting, BiRefNet…), export a **grayscale matte video at the same size/fps** and
  point `"mask": "my_matte.mp4"` at it — everything else stays the same.
- If the person leaves the frame, `head` falls back to the matte top; `face` holds the last
  position (interpolated). Check `face_seen` in `track.json` if an anchor drifts.
- `echo` and `hand_follow` trails need sequential frames: `preview` warms up 0.5 s before each
  timestamp, so what you see matches the render.
