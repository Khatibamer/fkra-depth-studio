---
name: fkra-motion-library
description: Amer's motion-graphics library and the rules for choosing from it (حركات موشن جرافيك، زوم، انتقالات، نص متحرك، عدّاد أرقام). Use whenever the user hands over a video to edit, montage, caption or turn into a reel (أعطيتك فيديو، اعملي مونتاج، ريلز) — read the video's idea first, then pick only the moves that fit it and apply them with the other fkra-* skills.
---

# FKRA motion library (مكتبة حركات الموشن)

The user asked for this: **when they give you a video, you choose the moves that
fit its idea.** Don't apply everything, and don't ask them to pick from the
list. Choose, explain briefly, then apply.

## 0. Workflow

1. **Understand the video**: transcribe it (see `fkra-embedded-captions` §1),
   then work out its type (table in §2), its tone and its key beats (hook,
   numbers, punchline, CTA).
2. **Pick 5–8 moves** from the library (§1) using the type table and the rules (§3).
3. **Show the user a short motion plan** (time → move → reason) before rendering:
   ```
   00:00–00:02  Word Pop + Punch-in  → Hook
   00:07        Number Counter 0→10K → he says "10 thousand"
   00:15        Whip Pan             → move to the second point
   ```
4. **Apply** with the skills: `fkra-depth-montage` (every layered move in §1.6 — behind /
   in front of / around / above the person, numbers, code, interaction), `fkra-embedded-captions`
   (captions, last), `fkra-talking-head-recut` (simple headlines and cards), `fkra-ffmpeg-toolkit`
   (cuts, transitions, export), `fkra-remotion-motion` (full-screen animated scenes or a reusable template).
5. **Audio**: add an SFX to every main move (§1.5).

## 1. The library

### 1.1 Text moves
| Move | What it does | Best for |
|---|---|---|
| **Kinetic Typography** | each word appears with the audio, the key word bigger or a different colour | captions for any talking-head video |
| **Word Pop / Scale Bounce** | 0→110%→100% with overshoot | Hook, energetic words |
| **Mask Reveal** | text slides out from behind a line or mask | elegant headlines, business content |
| **Typewriter** | letter by letter | numbers, code, tech/AI info, secrets |
| **Highlight Sweep** | a coloured bar sweeps behind the word | the most important word in a sentence |

### 1.2 Camera and framing
| Move | What it does | Best for |
|---|---|---|
| **Punch-in Zoom** | fast 10–15% zoom on the face | strong sentences, hiding jump cuts |
| **Ken Burns** | slow zoom + pan on a still image | still images, story |
| **Camera Shake** | 3–5 frames with an impact | shocking numbers, punchlines |
| **Parallax 2.5D** | speaker separated from the background, each moving at its own speed | intros, cinematic shots |

### 1.3 Transitions
| Move | Best for |
|---|---|
| **Whip Pan** + motion blur | moving between points, energetic content |
| **Match Cut** | when there's a matching shape or motion between two shots |
| **Zoom Through** | entering a screen/app/idea, before→after |
| **Glitch / RGB Split** | AI and tech content only, at most twice per video |
| **Shape Wipe** (brand colour) | a new section, chapter change |

### 1.4 Information elements
| Move | Best for |
|---|---|
| **Number Counter** 0→N | any number or stat that's said aloud |
| **Lower Third** | first time the speaker appears (name + title) |
| **Callout Lines** | explaining part of a product, screen or image |
| **Progress Bar / Checklist ✓** | steps, lists, "3 things" |
| **Floating Screenshots** with shadow and depth | proof: results, comments, apps, sites |

### 1.5 Finishing touches (always on)
- **Easing**: never linear — Ease Out on the way in, Ease In on the way out.
- **Motion Blur** on any fast move.
- **SFX**: Whoosh (transitions), Pop (words/cards), Click (checklist),
  Riser (before a reveal), Impact (shake/number).
- **Stagger**: elements enter one after another, 2–4 frames apart.

### 1.6 Depth layers (person cut out every frame → `fkra-depth-montage`)
| Move | Skill | Best for |
|---|---|---|
| **Text Behind Person** (giant word the head covers) | `fkra-text-behind-person` | hook, title, the one keyword of the video |
| **Circle Behind Head** | `fkra-text-behind-person` | portraits, intros, personal brand |
| **Front Word Pop / Highlight Card** | `fkra-text-front-person` | punchlines, key words, proof screenshots |
| **Above-Head Label** (follows the head) | `fkra-text-above-head` | name/role, "me before", reactions |
| **Face Brackets / Arrow to Face** | `fkra-text-above-head`, `fkra-motion-graphics` | "look at this", attention |
| **Orbit Around Person** (passes behind and in front) | `fkra-orbit-around-person` | lists of tools/skills, "all in one place" |
| **Neon Outline / Glow** | `fkra-orbit-around-person` | energy peaks, intros |
| **Code Panel / Terminal / Code Rain** | `fkra-code-motion` | AI, programming, prompts, automation |
| **Counter + Progress Bar** | `fkra-number-motion` | every number or % said aloud |
| **Background Restyle / Spotlight / Grid / Particles** | `fkra-motion-graphics` | focus, studio look from any room |
| **Fingertip Orb / Pinch Pop / Voice Pulse / Parallax** | `fkra-interactive-motion` | gestures, counting on fingers, "alive" feel |

## 2. Choosing by video type

| Video type | Core moves | Avoid |
|---|---|---|
| **Educational / explainer** | Kinetic captions, Progress/Checklist, Callout Lines, Number Counter, Shape Wipe between sections · depth: Text Behind (chapter titles), Counter + Bar, Orbit for lists | Glitch, heavy shake, Code Rain |
| **Business / authority** | Mask Reveal, Highlight Sweep, Floating Screenshots, Number Counter, Lower Third · depth: Circle Behind Head, Above-Head Label, Spotlight | Glitch, Typewriter, Pinch Pop |
| **AI / tech** | Typewriter, Glitch (light), Zoom Through into screens, Floating Screenshots, Callout Lines · depth: Code Panel/Terminal, Code Rain (≤3 s), Neon Outline, Orbit of tools | Ken Burns |
| **Story / personal** | Ken Burns, Parallax, Match Cut, calm Kinetic captions, soft Punch-in · depth: Text Behind (soft fade), Above-Head "me before", Background Restyle | Shake, Glitch, Counter, Code Rain |
| **Ad / product** | Word Pop hook, Zoom Through, Callout Lines on the product, Number Counter for price/discount, Shape Wipe before CTA · depth: Text Behind hook, Fingertip Orb on the product | anything that hides the product |
| **Energetic / trend / comedy** | Word Pop, Punch-in, Whip Pan, Camera Shake, loud SFX · depth: Pinch Pop, Echo trail, Voice Pulse | Mask Reveal, slow pacing |
| **Ranking / list** | Checklist, Number Counter, Shape Wipe, Word Pop · depth: Orbit (the items), Pinch Pop per item | Ken Burns |
| **Podcast / interview** | Lower Third, Highlight Sweep, Kinetic captions, Punch-in on punchlines · depth: Above-Head Label for names, Spotlight | fast transitions, Orbit |

## 3. Golden rules
1. **The first second is the most important**: Word Pop + Punch-in + Hook text from the first frame
   (see `fkra-hook-first-frame`).
2. **One move in the point of focus** — never 5 things moving at once.
3. **Change something visual every 2–3 seconds** (zoom / text / B-roll / card).
4. **Fix one style**: FKRA brand colours and fonts, the same moves in every video.
5. **Arabic**: respect RTL — Mask Reveal and Highlight Sweep go from **right to left**,
   use `Encoding: -1` in `.ass` (libass shapes Arabic correctly).
6. **Every move must have a reason** in the content (a number → Counter, a list → Checklist).
   No move just for the sake of it.
7. **Don't use a heavy move twice in a row** (Shake, Glitch, Zoom Through).
8. **Depth layers: max 2 at once** (e.g. text behind + one front element), and never text behind
   and above-head text at the same moment. Behind-text must stay ≥ 50% visible (`depthfx preview` checks it).

## 4. Quick ffmpeg recipes

```bash
# Punch-in zoom 12% between 3.0s and 3.6s (smooth ease)
ffmpeg -i in.mp4 -vf "scale=iw*1.12:-2,zoompan=z='if(between(it,3,3.6),1+0.12*sin((it-3)/0.6*PI/2),1)':d=1:s=1080x1920:fps=30" -c:a copy out.mp4

# Camera shake for 5 frames at 7s
ffmpeg -i in.mp4 -vf "crop=iw-20:ih-20:10+if(between(t,7,7.17),8*sin(t*90),0):10+if(between(t,7,7.17),8*cos(t*90),0),scale=1080:1920" -c:a copy out.mp4

# Ken Burns on an image (5s)
ffmpeg -loop 1 -i img.jpg -vf "scale=2160:-2,zoompan=z='1+0.0008*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=150:s=1080x1920:fps=30" -t 5 kb.mp4
```

For moving text (Word Pop, Mask Reveal, Highlight, Typewriter) use `.ass` with `\t()`
and `\clip` — templates are in `fkra-embedded-captions` and `fkra-talking-head-recut`.
For Number Counter, Parallax, Floating Screenshots and complex transitions use
`fkra-remotion-motion`.
