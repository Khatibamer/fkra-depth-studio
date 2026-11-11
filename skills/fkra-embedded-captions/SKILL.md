---
name: fkra-embedded-captions
description: Burn animated word-by-word captions into a video (ترجمة/كابشن محروق داخل الفيديو) in Arabic or English, with styles karaoke, cinematic, neon or stomp. Use when the user asks to add captions, subtitles, كابشن، ترجمة على الفيديو، نص متحرك، or wants TikTok/Reels-style captions without CapCut.
---

# Embedded captions (كابشن محروق بأسلوب تيك توك)

Replaces CapCut auto-captions: transcribe with word timestamps, generate a styled
`.ass` file, burn it with ffmpeg. Everything runs locally.

## 1. Transcribe with word timestamps

Pick whatever is available, in this order:

1. **faster-whisper** (local):
   ```python
   from faster_whisper import WhisperModel
   m = WhisperModel("small", compute_type="int8")
   segs, _ = m.transcribe("audio.wav", word_timestamps=True, language="ar")  # or "en"
   words = [{"word": w.word, "start": w.start, "end": w.end} for s in segs for w in s.words]
   ```
2. **whisper.cpp** with `-ojf` (full JSON) and map tokens to the same shape.
3. **ElevenLabs connector** `creative_transcribe_audio` if no local model can be downloaded.

Extract audio first: `ffmpeg -i in.mp4 -ac 1 -ar 16000 audio.wav`.
Save the list as `words.json`. **Show the transcript to the user and fix wrong
words before rendering** — for Lebanese/Gulf dialect, Whisper often writes MSA
spellings; keep the dialect the speaker actually used.

## 2. Generate the subtitle file

```bash
python3 .claude/skills/fkra-embedded-captions/scripts/words_to_ass.py words.json subs.ass \
  --style karaoke --width 1080 --height 1920 --font "Cairo" --words-per-line 3
```

| Style | Look | When |
|---|---|---|
| `karaoke` | white line, spoken word in yellow and slightly larger, lower third | default for talking heads |
| `cinematic` | small, thin, fading full line | B-roll, storytelling, ads with music |
| `neon` | centred, pink glow, cyan active word | night/energetic content |
| `stomp` | one huge word at a time popping in | hooks, first 3 seconds, punchlines |

Get the real width/height from `ffprobe` and pass them, otherwise sizes are off.
Use 2 words per line for Arabic hooks, 3 for normal speech.

## 3. Burn in

```bash
ffmpeg -i in.mp4 -vf "ass=subs.ass:fontsdir=./fonts" -c:v libx264 -crf 18 -preset medium \
  -c:a copy -movflags +faststart out_captioned.mp4
```

- Arabic needs a **TTF/OTF** font with Arabic glyphs in `fontsdir` (Cairo, Tajawal,
  Noto Kufi Arabic). libass handles RTL shaping; never reverse the text manually.
  The script writes the style with `Encoding: -1` so libass lays out the whole line
  as one bidi paragraph; with `1` the highlighted Arabic word jumps out of order.
- Keep captions out of the TikTok UI zones: bottom ~20% and right edge ~12% of a 9:16 frame.
  The `karaoke` style already sits at 22% from the bottom.
- Mix styles: render `stomp` for the first 2–3 s (the hook) and `karaoke` for the
  rest. Split `words.json`, generate each part with a different `--name`
  (e.g. `--name Hook` / `--name Body`), then append the hook file's `Style:` line and
  `Dialogue:` lines into the body file. Same style name in both = the hook loses its look.
- Arabic lines that start with an English word (Google, Genie…) get a leading RLM
  from the script so they still read right-to-left.

## 4. Check

Extract 3 frames (`ffmpeg -ss T -i out.mp4 -frames:v 1 f.jpg`) at the start,
middle and end and look at them before handing the file over: font loaded (no
boxes), Arabic letters joined, nothing hidden by the platform UI.
