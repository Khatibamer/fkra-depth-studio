# depthfx layer reference

Units: a number ≤ 1.5 is a **fraction** (x/size → of width, y → of height); larger = pixels.
Colours: `#RRGGBB`, `#RRGGBBAA`, `[r,g,b,a]` 0–255, or a brand key (`accent`, `text`, `dark`, `pink`, `cyan`
or any key you add under `"brand"`).

## Common keys (every layer)

| key | default | meaning |
|---|---|---|
| `type` | `text` | layer type (sections below) |
| `start` / `end` | 0 / ∞ | seconds in the rendered file |
| `z` | per type | `bg` (restyle background) · `behind` (under the person) · `front` (over the person) · `post` (whole frame, after everything) |
| `in` / `out` | `fade` / `fade` | entrance / exit animation (per type) |
| `in_dur` / `out_dur` | 0.35 / 0.25 | seconds |
| `opacity` | 1 | |
| `pos` | [0.5, 0.5] | position of the layer's centre |
| `anchor_to` | — | follow the person: `head` (top of hair) · `face` (face centre) · `chest` · `body` · `hand` (index tip) |
| `offset` | [0, 0] | added to `pos`/anchor |
| `parallax` | — | e.g. `0.3`: moves opposite to the head → depth |
| `float` | — | `0.01` or `[amp, period_s]`: gentle bob |
| `react` | — | e.g. `0.2`: scale pulses with voice loudness |
| `when` | — | `hand` / `no_hand`: only visible while a hand is (not) in frame |

## text  (default z: front)

| key | default | |
|---|---|---|
| `text` | | `\n` = new line, `*word*` = accent |
| `font` / `weight` | `display` (Cairo) / 800 | also `body` (Tajawal Bold), `mono` (JetBrains Mono) or a .ttf path |
| `size` | 0.08 | or `fit: 0.9` = widest line fills 90% of width (cap `max_size` 0.5) |
| `color` / `accent` | `text` / `accent` | |
| `accent_style` | `color` | `box` = highlighter card behind accent words (`box_text` = its text colour) |
| `stroke` / `stroke_color` | 0 / black | outline width (fraction of width) |
| `hollow` | false | outline-only letters (needs `stroke`) |
| `gradient` | — | `[top, bottom]` fill |
| `shadow` | true | `false` or `{dx, dy, blur, color}` |
| `box` | — | card behind the whole block `{color, pad, radius}`, sweeps open in reading direction |
| `line_spacing` | 1.08 | 0.85–0.95 for stacked display type |
| `stagger` | 0.06 | seconds between words for `pop`/`rise`/`slide`/`type` |
| `anchor` | `center` | `bottom` (default when anchored to head) / `top` |
| `align` | `center` | `left` / `right` |
| `safe` | true | clamp inside a 4% margin |

`in`: `pop` (scale-bounce per word) · `fade` · `rise` (mask reveal from the baseline) · `slide` ·
`type` (word by word) · `zoom` (whole block 1.35→1, cinematic) · `none`
`out`: `fade` · `pop` · `rise_out` · `zoom` · `none`

## counter  (text + these)

`from` 0 · `to` 100 · `text` `"{n}"` (template: `"+{n}K"`, `"${n}"`, `"{n}%"`) · `decimals` 0 · `commas` true ·
`arabic_digits` false (٠١٢٣) · `dur` 1.2 · `delay` 0.1 · `ease` `out` · `land_pop` true (bump when it lands). Default `in: pop`.

## code  (default z: front)

`code` (string, `\n` lines) · `theme` `editor` | `terminal` | `fkra` · `colors` {kw,str,num,com,fn,op,text,bg,border} ·
`cps` 28 (chars/s) · `type_delay` = in_dur · `size` 0.032 · `width` 0.84 · `max_lines` (auto-scrolls) · `title` · `chrome` true (window dots).
Default `in: pop`. Mono font has no Arabic: keep Arabic in a `text` layer next to the panel.

## code_rain  (default z: behind)

`cell` 0.03 · `chars` `"01{}[]<>/=+*#$;:ABCDEFXYZ"` · `color` accent · `head_color` white · `trail` 14 · `speed` 1 · `density` 0.75 · `seed`.

## orbit  (draws in both behind and front passes)

`items` [words or .png paths] · `anchor_to` `chest` (default; `head` + small `ry` for a halo above the hair) · `rx` 0.42 · `ry` 0.07 ·
`speed` 0.12 rev/s (negative = other way) · `tilt` −8° · `size` 0.055 · `pill` true · `pill_color` · `color` / `accent` (alternating) ·
`ring` true · `ring_color` accent · `ring_width` 0.004. Items on the far side shrink/dim and pass behind the person.

## shape  (default z: front; particles/grid: behind)

`shape` + `color` (accent) + `width` (line thickness 0.006):

| shape | keys |
|---|---|
| `circle` | `radius` 0.33 · `fill` true (false = ring). Behind the head: `anchor_to: face`, `z: behind`, `in: pop` |
| `ring_pulse` | `r0` 0.05 · `r1` 0.4 · `period` 1.2 · `count` 3 |
| `burst` | `r0` 0.06 · `r1` 0.2 · `rays` 10 · `dur` 0.5 (fires at `start`) |
| `corners` | focus brackets on the tracked face · `margin` 0.35 |
| `underline` | `length` 0.5 · `width` 0.012 · `dir` `rtl`/`ltr` |
| `arrow` | `from` / `to` = [x,y] or an anchor name (`"face"`, `"hand"`) · `bend` 0.25 · draws itself over `in_dur` |
| `bar` | progress bar · `value` 0–1 · `length` 0.7 · `height` 0.03 · `dur` 1.2 · `delay` · `dir` rtl · `track_color` |
| `particles` | `count` 70 · `size` 0.006 · `rise` 0.03 · `seed` |
| `grid` | `cell` 0.09 · `drift` 0.02 · `strength` 0.35 |

## outline  (default z: behind)
Sticker stroke / neon glow hugging the person: `color` accent · `width` 0.012 · `glow` 0.02 (0 = none) · `stroke` true · `react`.

## echo  (default z: behind)
Ghost copies of the person trailing behind them: `delays` [4,8,12] frames · `color` accent · `tint` 0.35 · `strength` 0.5.
Best on movement (turns, gestures). Needs sequential frames (fine in render and preview).

## background  (z: bg — only what is behind the person)
`dim` 0–1 · `blur` (fraction) · `desat` 0–1 · `tint` `#RRGGBBAA` · `color` / `gradient` [top,bottom] / `image` path ·
`replace` 1.0 (how much of colour/gradient/image) · `spotlight` radius (darkens away from `spot_on` = `face`).
Put background layers first in the list.

## image  (default z: front)
`path` · `width` 0.5 · `radius` (rounded corners) · `shadow` true · `in` `pop` | `fade` | `rise`. Screenshots, logos, stickers.

## hand_follow
Glowing orb glued to the hand: `point` `tip` | `thumb` | `palm` · `trail` 10 · `radius` 0.018 · `color` ·
optional `text` label (+ `text_color`, `size`, `offset` [0,-0.06]). Fades with hand presence.

## pinch_burst
Every pinch (thumb meets index) inside `start..end` fires a `burst` + pops the next word from `words` / `text`:
`threshold` 0.22 (× face width) · `words` [] · `size` 0.06 · `text_color` · plus burst keys (`rays`, `r0`, `r1`, `dur`).

## camera  (z: post)
`zoom` 1.12 (punch-in toward `anchor_to` = `face`; eases in over `in_dur`, back out over `out_dur` unless `return: false`) ·
`shake` (amplitude fraction, decays to `end`) · `flash` 0–1 (white flash at `start`).

## track.json (from analyze)
`w, h, fps, frames[]` → `face [cx,cy,w,h]`, `face_seen`, `head [x,y]`, `body [x0,y0,x1,y1]`,
`hands [{tip, thumb, palm, pinch}]`, `rms` 0–1. Pixel coordinates of the analysed file.
