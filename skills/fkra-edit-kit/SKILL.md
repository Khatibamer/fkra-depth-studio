---
name: fkra-edit-kit
description: Rough-cut and short-form editing of a talking-head video from the terminal (مونتاج، قص الصمت، حذف الأخطاء، تحويل فيديو طويل لريلز) — cut silences, remove fluffed takes and repeated sentences, turn a long recording into 9:16 shorts with a hook, story structure and B-roll. Use when the user gives a raw recording and asks to edit, cut, trim, clean up, make a reel/short/TikTok, or "اعملي مونتاج".
---

# Fkra Edit Kit (المونتاج الكامل بدون CapCut)

One skill, six commands. Run them in this order on a raw recording; each step
writes a new file and never overwrites the source.

```
raw.mp4 → /cut-silences → /cut-mistakes → /video-storytelling → /short-form-edit → captions → export
```

Always start with `ffprobe` (duration, resolution, fps, audio) and make a 540p
proxy for previews if the source is over 1080p (see `fkra-ffmpeg-toolkit`).

## /cut-silences — remove dead air

```bash
python3 .claude/skills/fkra-edit-kit/scripts/cut_silences.py raw.mp4 step1.mp4 --dry-run
python3 .claude/skills/fkra-edit-kit/scripts/cut_silences.py raw.mp4 step1.mp4
```

- Defaults: `--noise -35` dB, `--min-silence 0.45` s, `--pad 0.12` s.
- Noisy room → raise noise to `-30`. Fast, punchy TikTok pace → `--min-silence 0.3 --pad 0.08`.
  Calm teaching video → `--min-silence 0.7 --pad 0.2`.
- Report "removed X s of Y s" to the user from the JSON the script prints.

## /cut-mistakes — remove fluffed takes

1. Transcribe `step1.mp4` with word timestamps (see `fkra-embedded-captions` §1).
2. Build a numbered sentence list with start/end times.
3. Mark as mistakes:
   - a sentence that is restarted: keep **the last complete take** ("he said we want to… sorry. He said we want to channel it." → keep the second);
   - sentences containing "sorry / خلص / لا لا / من جديد / عيد" followed by a retake;
   - filler-only fragments (يعني، اممم، اه، um, uh) longer than 0.4 s.
4. **Show the list of cuts to the user before rendering** (time + text + reason).
5. Render the keep-list with the same trim/concat graph as `cut_silences.py`.

## /video-storytelling — structure before cutting

Reorder segments (don't just trim) into:

| Beat | Length (60 s reel) | Content |
|---|---|---|
| Hook | 0–3 s | strongest sentence or result, pulled from anywhere in the video |
| Problem | 3–12 s | pain the viewer recognises |
| Value | 12–45 s | numbered points / steps; one idea per cut |
| Proof | 45–55 s | number, demo, before/after |
| CTA | last 3–5 s | one action only (follow, DM a keyword, comment) |

If the Fkra hook bank skill (`fkra-hook-first-frame`) is available, use it to choose the hook line.

## /short-form-edit — long video → 9:16 shorts

1. From the transcript, pick 3–5 self-contained moments of 20–60 s that each have their own hook.
2. Cut each, then reframe to 9:16 on the speaker's face
   (`crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920`; shift `x` if the face is off-centre —
   check with a frame grab).
3. Add a jump-cut zoom every 3–5 s to keep motion: alternate 100% and 112% framing
   (punch-in recipe in `fkra-ffmpeg-toolkit/reference.md`).
4. Captions with `fkra-embedded-captions` (`stomp` for the hook, `karaoke` after).
5. Loudness to −14 LUFS and export with `+faststart`.

## /motion-showreel — B-roll and cards

- Cover every abstract sentence with a B-roll clip or image (ffmpeg `overlay`, 1–2 s each, with `fade`).
- Title cards and lower-thirds: use `fkra-talking-head-recut`.
- Never cover the face during the hook.

## /style-library — keep the look consistent

Save every accepted edit as a preset in `video-styles.json` next to the project
(caption style, font, colours, cut pace, zoom rhythm, LUT, loudness) and reuse it for
the next video of the same series so the channel looks consistent.

## Done checklist

- [ ] No cut lands mid-word (listen at each cut point or check against word timestamps).
- [ ] Hook is in the first 3 s, no logo/intro before it.
- [ ] Audio −14 LUFS, true peak ≤ −1 dB.
- [ ] 1080×1920, 30 fps, H.264 + AAC, `yuv420p`.
