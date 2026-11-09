# Copyright (c) 2026 Amer Khatib (FKRA AI). All rights reserved.
# FKRA Depth Studio — licensed under the FKRA Source-Available License 1.0 (see LICENSE).
# Commercial use, redistribution or re-publishing requires written permission.
"""Layer types for the FKRA depth-montage engine.

Every layer has: start, end (seconds), z ("bg" | "behind" | "front" | "post"),
in / out animation, and optional modifiers:
  parallax  k     moves opposite to the head (depth feel)
  float     [amp, period]   gentle bob
  react     k     scales with voice loudness
  when      "hand" | "no_hand"   only visible while a hand is (not) in frame
Sizes/positions under 1.0 are fractions of the frame (size 0.08 = 8% of width).
"""
from __future__ import annotations

import math
import random
import re
from collections import deque

import cv2
import numpy as np

from fx_core import (blend_full, blit, clamp01, color, ease, font, image_sprite, is_rtl,
                     rect_sprite, scaled, word_sprite)


# ============================================================================ context
class Ctx:
    """Per-frame state handed to every layer."""

    def __init__(self, env, idx, t, frame, mask):
        self.env, self.idx, self.t = env, idx, t
        self.frame, self.mask = frame, mask  # float32 HxWx3 / HxW (0..1)
        tr = env.frames[min(idx, len(env.frames) - 1)]
        self.tr = tr
        self.W, self.H = env.W, env.H
        self.rms = tr.get("rms", 0.0)
        self.hand_presence = env.hand_presence[min(idx, len(env.hand_presence) - 1)]

    def anchor(self, name):
        W, H, tr = self.W, self.H, self.tr
        face = tr.get("face")
        if name == "head":
            return tuple(tr["head"])
        if name == "face" and face:
            return face[0], face[1]
        if name == "chest" and face:  # kept on screen in close-ups
            return face[0], min(face[1] + face[3] * 1.9, H * 0.8)
        if name == "body" and tr.get("body"):
            b = tr["body"]
            return (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        if name == "hand":
            h = self.env.hand_point(self.idx)
            if h:
                return tuple(h)
        return W / 2, H / 2

    def face_w(self):
        f = self.tr.get("face")
        return f[2] if f and f[2] > 0 else self.W * 0.25


class Env:
    def __init__(self, track, brand):
        self.frames = track["frames"]
        self.W, self.H, self.fps = track["w"], track["h"], track["fps"]
        self.brand = brand
        hx = [f["head"][0] for f in self.frames] or [self.W / 2]
        hy = [f["head"][1] for f in self.frames] or [self.H / 4]
        self.head_mean = (float(np.mean(hx)), float(np.mean(hy)))
        pres, p = [], 0.0
        for f in self.frames:
            p = p * 0.7 + (1.0 if f["hands"] else 0.0) * 0.3
            pres.append(p)
        q = 0.0  # backward pass so it fades in slightly before the hand appears
        for k in range(len(pres) - 1, -1, -1):
            q = q * 0.7 + (1.0 if self.frames[k]["hands"] else 0.0) * 0.3
            pres[k] = min(1.0, max(pres[k], q) * 1.6)
        self.hand_presence = pres or [0.0]
        self._last_hand = None

    def hand_point(self, idx, key="tip"):
        """Highest hand's point at frame idx (holds last position briefly)."""
        idx = min(idx, len(self.frames) - 1)
        for k in range(idx, max(-1, idx - 8), -1):
            hs = self.frames[k]["hands"]
            if hs:
                return min(hs, key=lambda h: h["tip"][1])[key]
        return None

    def col(self, c, default="#FFFFFF"):
        if isinstance(c, str) and c in self.brand:
            c = self.brand[c]
        return color(c if c is not None else default)


def px(v, ref):
    """<=1.5 -> fraction of ref; otherwise pixels."""
    return v * ref if abs(v) <= 1.5 else v


# ============================================================================ base
class Layer:
    z_default = "front"

    def __init__(self, s, env):
        self.s, self.env = s, env
        self.start = float(s.get("start", 0))
        self.end = float(s.get("end", 1e9))
        self.z = s.get("z", self.z_default)
        self.in_anim = s.get("in", "fade")
        self.out_anim = s.get("out", "fade")
        self.in_dur = float(s.get("in_dur", 0.35))
        self.out_dur = float(s.get("out_dur", 0.25))
        self.opacity = float(s.get("opacity", 1.0))
        self.W, self.H = env.W, env.H

    def active(self, t):
        return self.start <= t < self.end

    def p_in(self, t, delay=0.0):
        return clamp01((t - self.start - delay) / max(self.in_dur, 1e-3))

    def p_out(self, t):
        return clamp01((self.end - t) / max(self.out_dur, 1e-3))

    def pos(self, ctx, key="pos", default=(0.5, 0.5)):
        s = self.s
        a = s.get("anchor_to")
        if a:
            x, y = ctx.anchor(a)
        else:
            p = s.get(key, default)
            x, y = px(p[0], self.W), px(p[1], self.H)
        off = s.get("offset", [0, 0])
        x, y = x + px(off[0], self.W), y + px(off[1], self.H)
        # modifiers
        k = s.get("parallax")
        if k:
            hx, hy = ctx.tr["head"]
            x -= (hx - self.env.head_mean[0]) * k
            y -= (hy - self.env.head_mean[1]) * k
        fl = s.get("float")
        if fl:
            amp, per = (fl, 3.0) if isinstance(fl, (int, float)) else fl
            y += px(amp, self.H) * math.sin(2 * math.pi * ctx.t / per)
        return x, y

    def mod_scale(self, ctx):
        k = self.s.get("react")
        return 1 + k * ctx.rms if k else 1.0

    def mod_opacity(self, ctx):
        w = self.s.get("when")
        o = self.opacity
        if w == "hand":
            o *= ctx.hand_presence
        elif w == "no_hand":
            o *= 1 - ctx.hand_presence
        return o

    def block_env(self, t):
        """Whole-layer (opacity, scale) envelope from in/out anims."""
        pi, po = self.p_in(t), self.p_out(t)
        op, sc = 1.0, 1.0
        if self.in_anim in ("fade", "rise", "slide", "type", "pop"):
            op *= ease("out", pi)
        if self.in_anim == "pop":
            sc *= ease("back", pi)
        if self.in_anim == "zoom":
            op *= ease("out", pi)
            sc *= 1 + 0.35 * (1 - ease("out", pi))
        if self.out_anim in ("fade", "rise_out"):
            op *= ease("out", po)
        if self.out_anim == "pop":
            sc *= ease("out", po)
        if self.out_anim == "zoom":
            op *= ease("out", po)
            sc *= 1 + 0.2 * (1 - po)
        return op, sc

    def draw(self, canvas, ctx, pass_):
        if pass_ == self.z:
            self.render(canvas, ctx)

    def render(self, canvas, ctx):
        raise NotImplementedError


def patch_draw(canvas, x0, y0, x1, y1, fn, opacity=1.0):
    """Draw with OpenCV into a small RGBA patch, then alpha-blit it."""
    H, W = canvas.shape[:2]
    x0, y0 = int(max(0, x0)), int(max(0, y0))
    x1, y1 = int(min(W, x1)), int(min(H, y1))
    if x1 <= x0 or y1 <= y0:
        return
    rgb = np.zeros((y1 - y0, x1 - x0, 3), np.float32)
    a = np.zeros((y1 - y0, x1 - x0), np.float32)
    fn(rgb, a, x0, y0)
    blit(canvas, np.dstack([rgb, a]), x0, y0, opacity)


SH = 4  # sub-pixel shift bits for cv2 drawing


def _p(x, y):
    return int(round(x * (1 << SH))), int(round(y * (1 << SH)))


# ============================================================================ text
_MARK = re.compile(r"\*([^*]+)\*")


class Text(Layer):
    """Kinetic typography block. `*word*` marks accent words.

    in: pop | fade | rise (mask reveal) | slide | type | zoom | none     out: fade | pop | rise_out | zoom | none
    """

    def __init__(self, s, env):
        super().__init__(s, env)
        self.font_name = s.get("font", "display")
        self.weight = int(s.get("weight", 800))
        self.fill = env.col(s.get("color", "text"))
        self.accent = env.col(s.get("accent", "accent"))
        self.accent_style = s.get("accent_style", "color")  # color | box
        self.stroke = int(px(s.get("stroke", 0), self.W)) if s.get("stroke") else 0
        self.stroke_color = env.col(s.get("stroke_color", "#000000"))
        self.hollow = bool(s.get("hollow", False))
        g = s.get("gradient")
        self.gradient = [env.col(g[0]), env.col(g[1])] if g else None
        sh = s.get("shadow", True)
        self.shadow = None
        if sh:
            sh = sh if isinstance(sh, dict) else {}
            k = self.W / 1080
            self.shadow = (sh.get("dx", 0) * k, sh.get("dy", 6) * k, sh.get("blur", 10) * k,
                           env.col(sh.get("color", "#000000A0")))
        self.box = s.get("box")
        self.spacing = float(s.get("line_spacing", 1.08))
        self.stagger = float(s.get("stagger", 0.06))
        self.anchor = s.get("anchor", "bottom" if s.get("anchor_to") == "head" else "center")
        self.align = s.get("align", "center")
        self.size = self._fit_size(self.sizing_text())
        self._cache = {}

    def sizing_text(self):
        return self.s.get("text", "")

    def _fit_size(self, text):
        s = self.s
        if s.get("fit"):
            f = font(self.font_name, 200, self.weight)
            widest = max(f.getlength(_MARK.sub(r"\1", ln)) for ln in text.split("\n"))
            size = 200 * s["fit"] * self.W / max(widest, 1)
            return int(min(size, px(s.get("max_size", 0.5), self.W)))
        return int(px(s.get("size", 0.08), self.W))

    def layout(self, text):
        if text in self._cache:
            return self._cache[text]
        f = font(self.font_name, self.size, self.weight)
        # tight ink metrics (display fonts report huge ascents that push text off-centre)
        asc = -f.getbbox("Hأل" if is_rtl(text) else "HÀl", anchor="ls")[1]
        desc = max(f.getbbox("gجي", anchor="ls")[3], 1)
        space = f.getlength(" ")
        line_h = self.size * self.spacing
        words = []
        lines = text.split("\n")
        widths = []
        for li, line in enumerate(lines):
            toks = []
            for part in re.split(r"(\*[^*]+\*)", line):
                if not part:
                    continue
                accent = part.startswith("*") and part.endswith("*")
                for w in (part.strip("*") if accent else part).split():
                    toks.append((w, accent))
            rtl = is_rtl(line)
            adv = [f.getlength(w) for w, _ in toks]
            lw = sum(adv) + space * max(0, len(toks) - 1)
            widths.append(lw)
            words.append((toks, adv, lw, rtl))
        bw = max(widths) if widths else 0
        bh = line_h * (len(lines) - 1) + asc + desc
        out = []
        box_pad = int(self.size * 0.14)
        for li, (toks, adv, lw, rtl) in enumerate(words):
            if self.align == "left":
                x = 0 if not rtl else lw
            elif self.align == "right":
                x = bw - lw if not rtl else bw
            else:
                x = (bw - lw) / 2 + (lw if rtl else 0)
            base_y = asc + li * line_h
            for (w, accent), a in zip(toks, adv):
                fill = self.accent if accent and self.accent_style == "color" else self.fill
                box = None
                if accent and self.accent_style == "box":
                    box = (box_pad, int(self.size * 0.18), self.accent)
                    fill = self.env.col(self.s.get("box_text", "#111111"))
                sp = word_sprite(w, f, fill, self.stroke, self.stroke_color, self.hollow,
                                 None if (accent and self.accent_style == "box") else self.gradient,
                                 self.shadow, box)
                pen = x - a if rtl else x
                out.append({"sp": sp, "x": pen - sp.ox, "y": base_y - sp.oy, "line": li,
                            "lt": base_y - asc, "lb": base_y + desc})
                x = x - a - space if rtl else x + a + space
        lay = {"words": out, "w": bw, "h": bh, "line_h": line_h}
        if self.box:
            b = self.box if isinstance(self.box, dict) else {}
            pad = px(b.get("pad", 0.025), self.W)
            lay["box"] = (rect_sprite(bw + pad * 2.4, bh + pad * 1.2, self.env.col(b.get("color", "#000000B0")),
                                      px(b.get("radius", 0.02), self.W)), pad * 1.2, pad * 0.6)
        self._cache[text] = lay
        return lay

    def current_text(self, t):
        return self.s.get("text", "")

    def render(self, canvas, ctx):
        t = ctx.t
        lay = self.layout(self.current_text(t))
        if not lay["words"]:
            return
        ax, ay = self.pos(ctx)
        bw, bh = lay["w"], lay["h"]
        ox = ax - bw / 2
        oy = ay - (bh if self.anchor == "bottom" else 0 if self.anchor == "top" else bh / 2)
        if self.s.get("safe", True):  # keep the block inside a 4% safe margin
            mg = self.W * 0.04
            ox = min(max(ox, mg), max(mg, self.W - mg - bw))
            oy = min(max(oy, mg), max(mg, self.H - mg - bh))
            ax = ox + bw / 2
        bs = self.mod_scale(ctx) * self.extra_scale(t)
        op_layer = self.mod_opacity(ctx)
        po = self.p_out(t)
        out_op, out_sc, out_dy = 1.0, 1.0, 0.0
        if self.out_anim in ("fade", "rise_out", "zoom"):
            out_op = ease("out", po)
        if self.out_anim == "pop":
            out_sc = ease("out", po)
        if self.out_anim == "rise_out":
            out_dy = -(1 - ease("in", po)) * lay["line_h"] * 0.6
        if self.out_anim == "zoom":
            out_sc = 1 + 0.2 * (1 - po)
        if self.in_anim == "zoom":
            pz = ease("out", self.p_in(t))
            bs *= 1 + 0.35 * (1 - pz)
            out_op *= pz
        bs *= out_sc
        cxr, cyr = bw / 2, bh / 2
        rtl = is_rtl(self.current_text(t))
        if "box" in lay:  # backing card: sweeps open in reading direction
            bsp, padx, pady = lay["box"]
            pb = ease("out", self.p_in(t))
            r = scaled(bsp.rgba, bs)
            full_w = r.shape[1]
            if pb < 1:
                wv = max(1, int(full_w * pb))
                r = r[:, -wv:] if rtl else r[:, :wv]
            left = ax - (cxr + padx) * bs
            bx = left + (full_w - r.shape[1]) if rtl else left
            by = oy + cyr - (cyr + pady) * bs + out_dy
            blit(canvas, r, bx, by, op_layer * out_op)
        for j, w in enumerate(lay["words"]):
            p = self.p_in(t, j * self.stagger if self.in_anim not in ("zoom", "fade") else 0)
            if p <= 0 and self.in_anim != "none":
                continue
            e = ease("out", p)
            op, ws, dx, dy, clip = op_layer * out_op, 1.0, 0.0, out_dy, None
            if self.in_anim == "pop":
                ws, op = ease("back", p), op * clamp01(p * 3)
            elif self.in_anim == "fade":
                op *= e
            elif self.in_anim == "type":
                op *= 1.0 if p > 0 else 0.0
            elif self.in_anim == "slide":
                d = -1 if rtl else 1
                dx, op = -d * (1 - e) * 0.08 * self.W, op * e
            elif self.in_anim == "rise":
                dy += (1 - e) * lay["line_h"]
            sp = w["sp"]
            r = scaled(sp.rgba, bs * ws)
            h0, w0 = sp.rgba.shape[:2]
            # word centre in block coords -> screen
            wcx, wcy = w["x"] + w0 / 2, w["y"] + h0 / 2
            sx = ox + cxr + (wcx - cxr) * bs + dx
            sy = oy + cyr + (wcy - cyr) * bs + dy
            if self.in_anim == "rise" and p < 1:
                clip = (0, 0, self.W, oy + cyr + (w["lb"] - cyr) * bs)
            blit(canvas, r, sx - r.shape[1] / 2, sy - r.shape[0] / 2, op, clip)

    def extra_scale(self, t):
        return 1.0


class Counter(Text):
    """Animated number. text template uses {n}: e.g. "+{n}K" or "{n}$"."""

    def __init__(self, s, env):
        s = dict(s)
        s.setdefault("in", "pop")
        s.setdefault("stagger", 0)
        self.v0, self.v1 = float(s.get("from", 0)), float(s.get("to", 100))
        self.dec = int(s.get("decimals", 0))
        self.dur = float(s.get("dur", 1.2))
        self.tmpl = s.get("text", "{n}")
        self.arabic_digits = bool(s.get("arabic_digits", False))
        super().__init__(s, env)

    def fmt(self, v):
        txt = f"{v:,.{self.dec}f}" if self.s.get("commas", True) else f"{v:.{self.dec}f}"
        if self.arabic_digits:
            txt = txt.translate(str.maketrans("0123456789,.", "٠١٢٣٤٥٦٧٨٩٬٫"))
        return self.tmpl.replace("{n}", txt)

    def sizing_text(self):
        return self.fmt(max(abs(self.v0), abs(self.v1)))

    def current_text(self, t):
        p = clamp01((t - self.start - float(self.s.get("delay", 0.1))) / self.dur)
        return self.fmt(self.v0 + (self.v1 - self.v0) * ease(self.s.get("ease", "out"), p))

    def extra_scale(self, t):
        if not self.s.get("land_pop", True):
            return 1.0
        dt = t - self.start - float(self.s.get("delay", 0.1)) - self.dur
        return 1 + 0.14 * math.sin(math.pi * dt / 0.25) if 0 <= dt < 0.25 else 1.0


# ============================================================================ code
_TOK = re.compile(
    r"(?P<com>#.*|//.*)|(?P<str>\"[^\"]*\"|'[^']*'|`[^`]*`)|(?P<num>\b\d+(?:\.\d+)?\b)"
    r"|(?P<kw>\b(?:def|return|import|from|class|if|else|elif|for|while|in|not|and|or|const|let|var|"
    r"function|async|await|new|try|catch|except|export|default|true|false|True|False|None|null|with|as)\b)"
    r"|(?P<fn>\b[A-Za-z_]\w*(?=\())|(?P<op>[{}()\[\];:=+\-*/<>.,!&|])")
THEMES = {
    "editor": {"bg": "#0D1117F0", "border": "#30363D", "text": "#E6EDF3", "kw": "#FF7B72", "str": "#A5D6FF",
               "num": "#F2CC60", "com": "#8B949E", "fn": "#D2A8FF", "op": "#79C0FF", "title": "#8B949E"},
    "terminal": {"bg": "#050805F2", "border": "#1F3D1F", "text": "#39FF88", "kw": "#39FF88", "str": "#C6FFDD",
                 "num": "#C6FFDD", "com": "#2E7D4F", "fn": "#39FF88", "op": "#39FF88", "title": "#2E7D4F"},
    "fkra": {"bg": "#0B0B12F0", "border": "#FFC400", "text": "#FFFFFF", "kw": "#FFC400", "str": "#9CF6C1",
             "num": "#FFC400", "com": "#7A7A90", "fn": "#7CC8FF", "op": "#BBBBCC", "title": "#FFC400"},
}


class Code(Layer):
    """Typing code panel. theme: editor | terminal | fkra.  cps = characters per second."""

    def __init__(self, s, env):
        super().__init__(s, env)
        s.setdefault("in", "pop")
        self.in_anim = s.get("in", "pop")
        th = dict(THEMES[s.get("theme", "editor")])
        th.update(s.get("colors", {}))
        self.th = {k: env.col(v) for k, v in th.items()}
        self.lines = s.get("code", "").rstrip("\n").split("\n")
        self.cps = float(s.get("cps", 28))
        self.delay = float(s.get("type_delay", self.in_dur))
        fs = int(px(s.get("size", 0.032), self.W))
        self.f = font("mono", fs, 600)
        self.cw = self.f.getlength("M")
        self.lh = fs * 1.5
        self.maxl = int(s.get("max_lines", min(12, len(self.lines))))
        self.pw = int(px(s.get("width", 0.84), self.W))
        self.pad = int(fs * 0.9)
        self.head = int(fs * 2.0) if s.get("chrome", True) else 0
        self.ph = int(self.head + self.pad * 2 + self.lh * self.maxl)
        self.panel = self._panel(s.get("title", ""))
        self.line_sp = [self._line(ln) for ln in self.lines]

    def _panel(self, title):
        sp = rect_sprite(self.pw, self.ph, self.th["bg"], radius=int(self.W * 0.022),
                         border=(max(2, int(self.W / 540)), self.th["border"]))
        rgba = sp.rgba
        if self.head:
            cy = self.head * 0.55
            for k, c in enumerate(("#FF5F57", "#FEBC2E", "#28C840")):
                cc = color(c)
                cv2.circle(rgba, _p(self.pad + k * self.head * 0.55, cy), int(self.head * 0.17 * (1 << SH)),
                           (cc[0], cc[1], cc[2], 1.0), -1, cv2.LINE_AA, SH)
            if title:
                ws = word_sprite(title, font("mono", int(self.lh * 0.55), 500), self.th["title"])
                blit_rgba(rgba, ws.rgba, (self.pw - ws.rgba.shape[1]) / 2, cy - ws.rgba.shape[0] / 2)
        return rgba

    def _line(self, ln):
        f = self.f
        asc, desc = f.getmetrics()
        w = int(self.cw * max(1, len(ln)) + 8)
        h = int(self.lh)
        from PIL import Image, ImageDraw
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        pos = 0
        for m in _TOK.finditer(ln):
            if m.start() > pos:
                seg = ln[pos:m.start()]
                d.text((self.cw * pos, h * 0.5), seg, font=f, anchor="lm",
                       fill=tuple(int(c * 255) for c in self.th["text"]))
            kind = m.lastgroup
            d.text((self.cw * m.start(), h * 0.5), m.group(), font=f, anchor="lm",
                   fill=tuple(int(c * 255) for c in self.th.get(kind, self.th["text"])))
            pos = m.end()
        if pos < len(ln):
            d.text((self.cw * pos, h * 0.5), ln[pos:], font=f, anchor="lm",
                   fill=tuple(int(c * 255) for c in self.th["text"]))
        return np.asarray(im, np.float32) / 255

    def render(self, canvas, ctx):
        t = ctx.t
        op, sc = self.block_env(t)
        op *= self.mod_opacity(ctx)
        n = int(max(0.0, t - self.start - self.delay) * self.cps)
        panel = self.panel.copy()
        # which lines are visible / typed
        typed, rem = [], n
        for k, ln in enumerate(self.lines):
            if rem <= 0 and k > 0:
                break
            c = min(len(ln), rem)
            typed.append((k, c))
            rem -= len(ln) + 1
        first = max(0, len(typed) - self.maxl)
        y = self.head + self.pad
        cur = None
        for row, (k, c) in enumerate(typed[first:]):
            sp = self.line_sp[k]
            wv = int(self.cw * c) + (8 if c == len(self.lines[k]) else 0)
            if wv > 0:
                blit_rgba(panel, sp[:, :min(wv, sp.shape[1])], self.pad, y + row * self.lh)
            cur = (self.pad + self.cw * c, y + row * self.lh)
        if cur and (int(t * 2.2) % 2 == 0 or n < sum(len(l) + 1 for l in self.lines)):
            x0, y0 = int(cur[0]), int(cur[1] + self.lh * 0.18)
            panel[y0:int(y0 + self.lh * 0.64), x0:x0 + max(2, int(self.cw * 0.55))] = (
                *self.th["text"][:3], 0.9)
        sc *= self.mod_scale(ctx)
        r = scaled(panel, sc)
        x, yy = self.pos(ctx)
        blit(canvas, r, x - r.shape[1] / 2, yy - r.shape[0] / 2, op)


def blit_rgba(dst, src, x, y):
    """Composite RGBA onto an RGBA buffer (straight alpha)."""
    H, W = dst.shape[:2]
    h, w = src.shape[:2]
    x, y = int(round(x)), int(round(y))
    X0, Y0, X1, Y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if X0 >= X1 or Y0 >= Y1:
        return
    s = src[Y0 - y:Y1 - y, X0 - x:X1 - x]
    d = dst[Y0:Y1, X0:X1]
    sa = s[..., 3:4]
    da = d[..., 3:4]
    oa = sa + da * (1 - sa)
    d[..., :3] = (s[..., :3] * sa + d[..., :3] * da * (1 - sa)) / np.maximum(oa, 1e-6)
    d[..., 3:4] = oa


class CodeRain(Layer):
    """Falling code glyph columns (default behind the person)."""
    z_default = "behind"

    def __init__(self, s, env):
        super().__init__(s, env)
        cell = int(px(s.get("cell", 0.03), self.W))
        self.cell = cell
        chars = s.get("chars", "01{}[]<>/=+*#$;:ABCDEFXYZ")
        head, body = env.col(s.get("head_color", "#FFFFFF")), env.col(s.get("color", "accent"))
        f = font("mono", int(cell * 0.9), 700)
        self.g_head = [word_sprite(c, f, head).rgba for c in chars]
        self.g_body = [word_sprite(c, f, body).rgba for c in chars]
        self.cols = self.W // cell + 1
        self.rows = self.H // cell + 1
        rnd = random.Random(int(s.get("seed", 7)))
        self.trail = int(s.get("trail", 14))
        self.cfg = [(rnd.uniform(6, 16) * float(s.get("speed", 1.0)), rnd.uniform(0, self.rows + self.trail),
                     rnd.random() < float(s.get("density", 0.75))) for _ in range(self.cols)]

    def render(self, canvas, ctx):
        op, _ = self.block_env(ctx.t)
        op *= self.mod_opacity(ctx)
        t = ctx.t - self.start
        span = self.rows + self.trail
        tick = int(t * 12)
        for c, (spd, off, on) in enumerate(self.cfg):
            if not on:
                continue
            head = (off + spd * t) % span
            hr = int(head)
            for k in range(self.trail):
                r = hr - k
                if r < 0 or r >= self.rows:
                    continue
                gi = (c * 31 + r * 17 + (tick if k == 0 else tick // 6)) % len(self.g_head)
                g = self.g_head[gi] if k == 0 else self.g_body[gi]
                a = op * (1 - k / self.trail) ** 1.6
                blit(canvas, g, c * self.cell, r * self.cell, a)


# ============================================================================ orbit
class Orbit(Layer):
    """Words/logos circling the person: front half over the body, back half behind it."""

    def __init__(self, s, env):
        super().__init__(s, env)
        s.setdefault("anchor_to", "chest")
        f = font(s.get("font", "display"), int(px(s.get("size", 0.055), self.W)), int(s.get("weight", 800)))
        fill = env.col(s.get("color", "text"))
        acc = env.col(s.get("accent", "accent"))
        self.items = []
        for k, it in enumerate(s.get("items", [])):
            if isinstance(it, str) and it.lower().endswith((".png", ".webp", ".jpg")):
                self.items.append(image_sprite(it, px(s.get("size", 0.055), self.W) * 2).rgba)
            else:
                pill = s.get("pill", True)
                box = (int(f.size * 0.35), int(f.size * 0.5), env.col(s.get("pill_color", "#111118E0"))) if pill else None
                self.items.append(word_sprite(it, f, acc if k % 2 else fill, box=box,
                                              shadow=(0, 4, 8, (0, 0, 0, .6))).rgba)
        self.rx, self.ry = px(s.get("rx", 0.42), self.W), px(s.get("ry", 0.07), self.H)
        self.speed = float(s.get("speed", 0.12))  # revolutions / second
        self.tilt = math.radians(float(s.get("tilt", -8)))
        self.ring = s.get("ring", True)
        self.ring_col = env.col(s.get("ring_color", "accent"))
        self.ring_w = max(2, int(px(s.get("ring_width", 0.004), self.W)))

    def _xy(self, cx, cy, th, grow):
        x, y = self.rx * grow * math.cos(th), self.ry * grow * math.sin(th)
        c, s_ = math.cos(self.tilt), math.sin(self.tilt)
        return cx + x * c - y * s_, cy + x * s_ + y * c

    def draw(self, canvas, ctx, pass_):
        if pass_ not in ("behind", "front"):
            return
        t = ctx.t
        op, sc = self.block_env(t)
        op *= self.mod_opacity(ctx)
        grow = ease("out", self.p_in(t)) * self.mod_scale(ctx)
        cx, cy = self.pos(ctx)
        front = pass_ == "front"
        if self.ring:
            pts = [self._xy(cx, cy, 2 * math.pi * k / 180, grow) for k in range(181)]
            sins = [math.sin(2 * math.pi * k / 180) for k in range(181)]
            seg = [_p(*pts[k]) for k in range(181) if (sins[k] >= 0) == front]
            if len(seg) > 1:
                xs = [p[0] >> SH for p in seg]
                ys = [p[1] >> SH for p in seg]
                m = self.ring_w * 2 + 2

                def fn(rgb, a, x0, y0, seg=seg):
                    sh = [(p[0] - (x0 << SH), p[1] - (y0 << SH)) for p in seg]
                    arr = np.array(sh, np.int32).reshape(-1, 1, 2)
                    cv2.polylines(rgb, [arr], False, self.ring_col[:3], self.ring_w, cv2.LINE_AA, SH)
                    cv2.polylines(a, [arr], False, 1.0, self.ring_w, cv2.LINE_AA, SH)

                patch_draw(canvas, min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m, fn,
                           op * (1.0 if front else 0.55))
        n = max(1, len(self.items))
        order = []
        for k, sp in enumerate(self.items):
            th = 2 * math.pi * (k / n + self.speed * (t - self.start))
            d = math.sin(th)
            if (d >= 0) != front:
                continue
            order.append((d, th, sp))
        for d, th, sp in sorted(order):
            x, y = self._xy(cx, cy, th, grow)
            s2 = sc * (0.78 + 0.3 * (d + 1) / 2)
            r = scaled(sp, s2)
            blit(canvas, r, x - r.shape[1] / 2, y - r.shape[0] / 2, op * (0.6 + 0.4 * (d + 1) / 2))


# ============================================================================ shapes / motion graphics
class Shape(Layer):
    """shape: circle | ring_pulse | burst | corners | underline | arrow | bar | particles | grid"""

    def __init__(self, s, env):
        super().__init__(s, env)
        self.kind = s.get("shape", "circle")
        self.c = env.col(s.get("color", "accent"))
        self.th = max(1, int(px(s.get("width", 0.006), self.W)))
        if self.kind == "particles":
            rnd = random.Random(int(s.get("seed", 3)))
            self.pts = [(rnd.random(), rnd.random(), rnd.uniform(.3, 1), rnd.uniform(0, 6.28))
                        for _ in range(int(s.get("count", 70)))]
        if self.kind in ("particles", "grid"):
            self.z = s.get("z", "behind")

    def render(self, canvas, ctx):
        t = ctx.t
        op, sc = self.block_env(t)
        op *= self.mod_opacity(ctx)
        sc *= self.mod_scale(ctx)
        getattr(self, "_" + self.kind)(canvas, ctx, op, sc)

    def _circle(self, canvas, ctx, op, sc):
        x, y = self.pos(ctx)
        r = px(self.s.get("radius", 0.33), self.W) * sc
        fill = self.s.get("fill", True)

        def fn(rgb, a, x0, y0):
            c = _p(x - x0, y - y0)
            cv2.circle(rgb, c, int(r * (1 << SH)), self.c[:3], -1 if fill else self.th, cv2.LINE_AA, SH)
            cv2.circle(a, c, int(r * (1 << SH)), self.c[3], -1 if fill else self.th, cv2.LINE_AA, SH)
        patch_draw(canvas, x - r - 4, y - r - 4, x + r + 4, y + r + 4, fn, op)

    def _ring_pulse(self, canvas, ctx, op, sc):
        x, y = self.pos(ctx)
        r0, r1 = px(self.s.get("r0", 0.05), self.W), px(self.s.get("r1", 0.4), self.W) * sc
        per, cnt = float(self.s.get("period", 1.2)), int(self.s.get("count", 3))
        for k in range(cnt):
            ph = ((ctx.t - self.start) / per + k / cnt) % 1.0
            r = r0 + (r1 - r0) * ease("out", ph)

            def fn(rgb, a, x0, y0, r=r):
                c = _p(x - x0, y - y0)
                cv2.circle(rgb, c, int(r * (1 << SH)), self.c[:3], self.th, cv2.LINE_AA, SH)
                cv2.circle(a, c, int(r * (1 << SH)), 1.0, self.th, cv2.LINE_AA, SH)
            patch_draw(canvas, x - r - self.th, y - r - self.th, x + r + self.th, y + r + self.th, fn,
                       op * (1 - ph) ** 1.3)

    def _burst(self, canvas, ctx, op, sc, x=None, y=None, t0=None):
        if x is None:
            x, y = self.pos(ctx)
        t0 = self.start if t0 is None else t0
        p = clamp01((ctx.t - t0) / float(self.s.get("dur", 0.5)))
        if p >= 1:
            return
        r0, r1 = px(self.s.get("r0", 0.06), self.W), px(self.s.get("r1", 0.2), self.W) * sc
        n = int(self.s.get("rays", 10))
        a_head, a_tail = ease("out", p), ease("out", max(0, p - 0.35) / 0.65)

        def fn(rgb, a, x0, y0):
            for k in range(n):
                th = 2 * math.pi * k / n + 0.3
                ra, rb = r0 + (r1 - r0) * a_tail, r0 + (r1 - r0) * a_head
                p1 = _p(x - x0 + ra * math.cos(th), y - y0 + ra * math.sin(th))
                p2 = _p(x - x0 + rb * math.cos(th), y - y0 + rb * math.sin(th))
                cv2.line(rgb, p1, p2, self.c[:3], self.th, cv2.LINE_AA, SH)
                cv2.line(a, p1, p2, 1.0, self.th, cv2.LINE_AA, SH)
        patch_draw(canvas, x - r1 - 8, y - r1 - 8, x + r1 + 8, y + r1 + 8, fn, op)

    def _corners(self, canvas, ctx, op, sc):
        f = ctx.tr.get("face")
        if not f:
            return
        m = float(self.s.get("margin", 0.35))
        e = ease("out", self.p_in(ctx.t))
        k = (1 + m) * (1 + 0.4 * (1 - e)) * sc
        cx, cy, w, h = f[0], f[1], f[2] * k, f[3] * k * 1.15
        L = min(w, h) * 0.22
        x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        segs = [((x0, y0 + L), (x0, y0), (x0 + L, y0)), ((x1 - L, y0), (x1, y0), (x1, y0 + L)),
                ((x0, y1 - L), (x0, y1), (x0 + L, y1)), ((x1 - L, y1), (x1, y1), (x1, y1 - L))]

        def fn(rgb, a, X0, Y0):
            for sg in segs:
                arr = np.array([_p(px_ - X0, py_ - Y0) for px_, py_ in sg], np.int32).reshape(-1, 1, 2)
                cv2.polylines(rgb, [arr], False, self.c[:3], self.th, cv2.LINE_AA, SH)
                cv2.polylines(a, [arr], False, 1.0, self.th, cv2.LINE_AA, SH)
        patch_draw(canvas, x0 - 10, y0 - 10, x1 + 10, y1 + 10, fn, op)

    def _underline(self, canvas, ctx, op, sc):
        x, y = self.pos(ctx)
        L = px(self.s.get("length", 0.5), self.W) * sc
        p = ease("out", self.p_in(ctx.t))
        rtl = self.s.get("dir", "rtl") == "rtl"
        xa, xb = (x + L / 2, x + L / 2 - L * p) if rtl else (x - L / 2, x - L / 2 + L * p)
        th = max(self.th, int(px(self.s.get("width", 0.012), self.W)))

        def fn(rgb, a, x0, y0):
            p1, p2 = _p(xa - x0, y - y0), _p(xb - x0, y - y0)
            cv2.line(rgb, p1, p2, self.c[:3], th, cv2.LINE_AA, SH)
            cv2.line(a, p1, p2, 1.0, th, cv2.LINE_AA, SH)
        patch_draw(canvas, min(xa, xb) - th, y - th, max(xa, xb) + th, y + th, fn, op)

    def _arrow(self, canvas, ctx, op, sc):
        """Curved hand-drawn style arrow from `from` to `to` (fractions or anchors)."""
        def P(v):
            if isinstance(v, str):
                return ctx.anchor(v)
            return px(v[0], self.W), px(v[1], self.H)
        (xa, ya), (xb, yb) = P(self.s.get("from", [0.2, 0.3])), P(self.s.get("to", "face"))
        bend = float(self.s.get("bend", 0.25))
        mx, my = (xa + xb) / 2 - (yb - ya) * bend, (ya + yb) / 2 + (xb - xa) * bend
        p = ease("out", self.p_in(ctx.t))
        pts = []
        for k in range(int(40 * p) + 1):
            u = k / 40
            pts.append(((1 - u) ** 2 * xa + 2 * (1 - u) * u * mx + u * u * xb,
                        (1 - u) ** 2 * ya + 2 * (1 - u) * u * my + u * u * yb))
        if len(pts) < 2:
            return
        (ex, ey), (qx, qy) = pts[-1], pts[-2]
        ang = math.atan2(ey - qy, ex - qx)
        hl = self.th * 5
        head = [(ex - hl * math.cos(ang - .5), ey - hl * math.sin(ang - .5)), (ex, ey),
                (ex - hl * math.cos(ang + .5), ey - hl * math.sin(ang + .5))]
        xs = [q[0] for q in pts + head]
        ys = [q[1] for q in pts + head]

        def fn(rgb, a, x0, y0):
            for poly in (pts, head):
                arr = np.array([_p(q[0] - x0, q[1] - y0) for q in poly], np.int32).reshape(-1, 1, 2)
                cv2.polylines(rgb, [arr], False, self.c[:3], self.th, cv2.LINE_AA, SH)
                cv2.polylines(a, [arr], False, 1.0, self.th, cv2.LINE_AA, SH)
        patch_draw(canvas, min(xs) - 10, min(ys) - 10, max(xs) + 10, max(ys) + 10, fn, op)

    def _bar(self, canvas, ctx, op, sc):
        """Progress bar filling to `value` (0..1) over `dur`; pairs with a counter."""
        x, y = self.pos(ctx)
        L, th = px(self.s.get("length", 0.7), self.W) * sc, px(self.s.get("height", 0.03), self.W) * sc
        p = ease("out", clamp01((ctx.t - self.start - float(self.s.get("delay", 0.1))) / float(self.s.get("dur", 1.2))))
        v = float(self.s.get("value", 1.0)) * p
        rtl = self.s.get("dir", "rtl") == "rtl"
        track = self.env.col(self.s.get("track_color", "#FFFFFF33"))
        r = int(th / 2)
        blit(canvas, rect_sprite(L, th, track, r).rgba, x - L / 2, y - th / 2, op)
        if v * L >= 2:
            fill = rect_sprite(max(th, v * L), th, self.c, r).rgba
            blit(canvas, fill, (x + L / 2 - fill.shape[1]) if rtl else x - L / 2, y - th / 2, op)

    def _particles(self, canvas, ctx, op, sc):
        t = ctx.t - self.start
        rmax = px(self.s.get("size", 0.006), self.W)
        rise = float(self.s.get("rise", 0.03))
        for (u, v, s, ph) in self.pts:
            x = u * self.W + math.sin(t * 0.6 + ph) * self.W * 0.01
            y = ((v - t * rise * s) % 1.0) * self.H
            r = rmax * s * sc
            a = op * (0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 2 + ph))) * s

            def fn(rgb, al, x0, y0, x=x, y=y, r=r):
                c = _p(x - x0, y - y0)
                cv2.circle(rgb, c, int(r * (1 << SH)), self.c[:3], -1, cv2.LINE_AA, SH)
                cv2.circle(al, c, int(r * (1 << SH)), 1.0, -1, cv2.LINE_AA, SH)
            patch_draw(canvas, x - r - 2, y - r - 2, x + r + 2, y + r + 2, fn, a)

    def _grid(self, canvas, ctx, op, sc):
        cell = px(self.s.get("cell", 0.09), self.W)
        drift = (ctx.t - self.start) * float(self.s.get("drift", 0.02)) * self.H
        a = np.zeros((self.H, self.W), np.float32)
        for x in np.arange(0, self.W, cell):
            cv2.line(a, (int(x), 0), (int(x), self.H), 1.0, 1, cv2.LINE_AA)
        for y in np.arange(-cell + drift % cell, self.H, cell):
            cv2.line(a, (0, int(y)), (self.W, int(y)), 1.0, 1, cv2.LINE_AA)
        yy = np.linspace(-1, 1, self.H)[:, None]
        xx = np.linspace(-1, 1, self.W)[None, :]
        vign = np.clip(1.2 - np.sqrt(xx ** 2 + yy ** 2), 0, 1)
        blend_full(canvas, self.c, a * vign * op * self.c[3] * float(self.s.get("strength", 0.35)))


# ============================================================================ person effects
class Outline(Layer):
    """Sticker outline / neon glow around the person (drawn just behind them)."""
    z_default = "behind"

    def render(self, canvas, ctx):
        op, _ = self.block_env(ctx.t)
        op *= self.mod_opacity(ctx)
        if op <= 0:
            return
        k = 2  # half-res for speed
        m = cv2.resize(ctx.mask, (self.W // k, self.H // k), interpolation=cv2.INTER_AREA)
        w = max(1, int(px(self.s.get("width", 0.012), self.W) / k * (1 + 0.6 * ctx.rms * (self.s.get("react") or 0))))
        ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * w + 1, 2 * w + 1))
        d = cv2.dilate(m, ker)
        c = self.env.col(self.s.get("color", "accent"))
        glow = float(self.s.get("glow", 0.02))
        if glow:
            g = cv2.GaussianBlur(d, (0, 0), px(glow, self.W) / k)
            g = cv2.resize(g, (self.W, self.H))
            blend_full(canvas, c, np.clip(g * 1.4, 0, 1) * op * 0.9)
        if self.s.get("stroke", True):
            d = cv2.resize(d, (self.W, self.H))
            blend_full(canvas, c, d * op)


class Echo(Layer):
    """Trailing ghost copies of the person behind them (needs a full sequential render)."""
    z_default = "behind"

    def __init__(self, s, env):
        super().__init__(s, env)
        self.delays = s.get("delays", [4, 8, 12])
        self.hist = deque(maxlen=max(self.delays) + 1)
        self.tint = env.col(s.get("color", "accent"))

    def draw(self, canvas, ctx, pass_):
        if pass_ == "bg":
            self.hist.append((ctx.frame, ctx.mask))
            return
        if pass_ != "behind":
            return
        op, _ = self.block_env(ctx.t)
        op *= self.mod_opacity(ctx)
        for j, d in enumerate(sorted(self.delays, reverse=True)):
            if len(self.hist) <= d:
                continue
            fr, m = self.hist[-1 - d]
            mix = float(self.s.get("tint", 0.35))
            img = fr * (1 - mix) + np.asarray(self.tint[:3], np.float32) * mix
            blend_full(canvas, img, m * op * float(self.s.get("strength", 0.5)) * (j + 1) / len(self.delays))

    def active(self, t):
        return self.start - 1.0 <= t < self.end  # keep history warm


class Background(Layer):
    """Restyle only what is behind the person: dim, blur, desat, tint, color/gradient/image replace, spotlight."""
    z_default = "bg"

    def __init__(self, s, env):
        super().__init__(s, env)
        self.img = None
        if s.get("image"):
            from PIL import Image
            im = Image.open(s["image"]).convert("RGB")
            # cover-fit
            k = max(self.W / im.width, self.H / im.height)
            im = im.resize((int(im.width * k + 1), int(im.height * k + 1)))
            l, tp = (im.width - self.W) // 2, (im.height - self.H) // 2
            self.img = np.asarray(im.crop((l, tp, l + self.W, tp + self.H)), np.float32) / 255
        if s.get("gradient"):
            c1, c2 = env.col(s["gradient"][0]), env.col(s["gradient"][1])
            y = np.linspace(0, 1, self.H, dtype=np.float32)[:, None, None]
            self.img = np.broadcast_to(np.asarray(c1[:3]) * (1 - y) + np.asarray(c2[:3]) * y,
                                       (self.H, self.W, 3)).astype(np.float32).copy()
        if s.get("color"):
            self.img = np.broadcast_to(np.asarray(env.col(s["color"])[:3], np.float32), (self.H, self.W, 3)).copy()

    def render(self, canvas, ctx):
        s = self.s
        op, _ = self.block_env(ctx.t)
        op *= self.mod_opacity(ctx)
        if op <= 0:
            return
        orig = canvas.copy() if op < 1 else None
        if s.get("blur"):
            k = px(s["blur"], self.W)
            canvas[:] = cv2.GaussianBlur(canvas, (0, 0), k)
        if s.get("desat"):
            g = canvas.mean(2, keepdims=True)
            canvas[:] = canvas * (1 - s["desat"]) + g * s["desat"]
        if self.img is not None:
            canvas[:] = canvas * (1 - float(s.get("replace", 1.0))) + self.img * float(s.get("replace", 1.0))
        if s.get("tint"):
            c = self.env.col(s["tint"])
            canvas[:] = canvas * (1 - c[3]) + np.asarray(c[:3], np.float32) * c[3]
        if s.get("dim"):
            canvas *= 1 - float(s["dim"])
        if s.get("spotlight"):
            x, y = ctx.anchor(s.get("spot_on", "face"))
            r = px(s["spotlight"], self.W)
            yy, xx = np.ogrid[:self.H, :self.W]
            d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / r
            canvas *= np.clip(1.25 - d * 0.6, 0.15, 1)[..., None].astype(np.float32)
        if orig is not None:
            canvas[:] = orig * (1 - op) + canvas * op


class ImageLayer(Layer):
    """PNG/JPG sprite (logo, screenshot, sticker). width as fraction of frame width."""

    def __init__(self, s, env):
        super().__init__(s, env)
        s.setdefault("in", "pop")
        self.in_anim = s["in"]
        sp = image_sprite(s["path"], px(s.get("width", 0.5), self.W)).rgba
        if s.get("radius") or s.get("shadow", True):
            h, w = sp.shape[:2]
            if s.get("radius"):
                from PIL import Image, ImageDraw
                m = Image.new("L", (w, h), 0)
                ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), int(px(s["radius"], self.W)), fill=255)
                sp[..., 3] *= np.asarray(m, np.float32) / 255
            if s.get("shadow", True):
                pad = int(self.W * 0.03)
                big = np.zeros((h + pad * 2, w + pad * 2, 4), np.float32)
                sh = np.zeros(big.shape[:2], np.float32)
                sh[pad:pad + h, pad:pad + w] = sp[..., 3]
                sh = cv2.GaussianBlur(np.roll(sh, int(pad * .35), 0), (0, 0), pad / 3) * 0.6
                big[..., 3] = sh
                blit_rgba(big, sp, pad, pad)
                sp = big
        self.sp = sp

    def render(self, canvas, ctx):
        op, sc = self.block_env(ctx.t)
        op *= self.mod_opacity(ctx)
        sc *= self.mod_scale(ctx)
        r = scaled(self.sp, sc)
        x, y = self.pos(ctx)
        dy = (1 - ease("out", self.p_in(ctx.t))) * self.H * 0.05 if self.in_anim == "rise" else 0
        blit(canvas, r, x - r.shape[1] / 2, y - r.shape[0] / 2 + dy, op)


# ============================================================================ interaction
class HandFollow(Layer):
    """Element glued to the index fingertip: glowing orb with trail, or text/label."""

    def __init__(self, s, env):
        super().__init__(s, env)
        self.c = env.col(s.get("color", "accent"))
        self.trail = deque(maxlen=int(s.get("trail", 10)))
        self.label = None
        if s.get("text"):
            self.label = word_sprite(s["text"], font("display", int(px(s.get("size", 0.05), self.W)), 800),
                                     env.col(s.get("text_color", "#111111")),
                                     box=(int(self.W * 0.015), int(self.W * 0.02), self.c)).rgba

    def render(self, canvas, ctx):
        op, _ = self.block_env(ctx.t)
        op *= self.mod_opacity(ctx) * ctx.hand_presence
        p = self.env.hand_point(ctx.idx, self.s.get("point", "tip"))
        if p is None:
            self.trail.clear()
            return
        self.trail.append(p)
        r = px(self.s.get("radius", 0.018), self.W) * self.mod_scale(ctx)
        n = len(self.trail)
        for k, (x, y) in enumerate(self.trail):
            rr = r * (0.3 + 0.7 * (k + 1) / n)
            aa = op * ((k + 1) / n) ** 2

            def fn(rgb, a, x0, y0, x=x, y=y, rr=rr):
                c = _p(x - x0, y - y0)
                cv2.circle(rgb, c, int(rr * 2.2 * (1 << SH)), self.c[:3], -1, cv2.LINE_AA, SH)
                cv2.circle(a, c, int(rr * 2.2 * (1 << SH)), 0.25, -1, cv2.LINE_AA, SH)
                cv2.circle(rgb, c, int(rr * (1 << SH)), (1, 1, 1), -1, cv2.LINE_AA, SH)
                cv2.circle(a, c, int(rr * (1 << SH)), 1.0, -1, cv2.LINE_AA, SH)
            patch_draw(canvas, x - rr * 3, y - rr * 3, x + rr * 3, y + rr * 3, fn, aa)
        if self.label is not None:
            x, y = self.trail[-1]
            off = self.s.get("offset", [0, -0.06])
            blit(canvas, self.label, x + px(off[0], self.W) - self.label.shape[1] / 2,
                 y + px(off[1], self.H) - self.label.shape[0] / 2, op)


class PinchBurst(Layer):
    """Every pinch (thumb meets index) fires a burst + optional popping word at that point."""

    def __init__(self, s, env):
        super().__init__(s, env)
        thr = float(s.get("threshold", 0.22))
        self.events, was = [], False
        for k, f in enumerate(env.frames):
            t = k / env.fps
            hs = f["hands"]
            closed = any(h["pinch"] < thr for h in hs)
            if closed and not was and self.start <= t < self.end:
                h = min(hs, key=lambda h: h["pinch"])
                self.events.append((t, (h["tip"][0] + h["thumb"][0]) / 2, (h["tip"][1] + h["thumb"][1]) / 2))
            was = closed if hs else False
        self.burst = Shape(dict(s, shape="burst", z=self.z), env)
        words = s.get("words") or ([s["text"]] if s.get("text") else [])
        f = font("display", int(px(s.get("size", 0.06), self.W)), 800)
        self.words = [word_sprite(w, f, env.col(s.get("text_color", "text")),
                                  shadow=(0, 4, 8, (0, 0, 0, .7))).rgba for w in words]

    def active(self, t):
        return any(e[0] <= t < e[0] + 0.9 for e in self.events)

    def render(self, canvas, ctx):
        for j, (t0, x, y) in enumerate(self.events):
            dt = ctx.t - t0
            if not 0 <= dt < 0.9:
                continue
            self.burst._burst(canvas, ctx, 1.0, 1.0, x, y, t0)
            if self.words:
                w = self.words[j % len(self.words)]
                s2 = ease("back", clamp01(dt / 0.3))
                r = scaled(w, max(0.05, s2))
                o = clamp01((0.9 - dt) / 0.25)
                blit(canvas, r, x - r.shape[1] / 2, y - r.shape[0] / 2 - self.H * 0.06 * ease("out", dt / 0.9), o)


# ============================================================================ camera (post)
class Camera(Layer):
    """Post move on the final composite: punch-in zoom (tracks the face), shake, flash."""
    z_default = "post"

    def render(self, canvas, ctx):
        s, t = self.s, ctx.t
        zoom = float(s.get("zoom", 1.0))
        e = ease("out", self.p_in(t)) * ease("inout", self.p_out(t)) if s.get("return", True) else ease("out", self.p_in(t))
        z = 1 + (zoom - 1) * e
        ax, ay = ctx.anchor(s.get("anchor_to", "face"))
        dx = dy = 0.0
        if s.get("shake"):
            amp = px(s["shake"], self.W) * (1 - clamp01((t - self.start) / max(self.end - self.start, 1e-3)))
            dx, dy = amp * math.sin(t * 97), amp * math.cos(t * 83)
            z = max(z, 1 + 2.2 * abs(amp) / self.W)
        if abs(z - 1) > 1e-3 or dx or dy:
            M = np.float32([[z, 0, (1 - z) * ax + dx], [0, z, (1 - z) * ay + dy]])
            canvas[:] = cv2.warpAffine(canvas, M, (self.W, self.H), flags=cv2.INTER_LINEAR,
                                       borderMode=cv2.BORDER_REFLECT)
        if s.get("flash"):
            f = float(s["flash"]) * (1 - clamp01((t - self.start) / 0.25))
            if f > 0:
                canvas[:] = canvas * (1 - f) + f


TYPES = {"text": Text, "counter": Counter, "code": Code, "code_rain": CodeRain, "orbit": Orbit,
         "shape": Shape, "outline": Outline, "echo": Echo, "background": Background, "image": ImageLayer,
         "hand_follow": HandFollow, "pinch_burst": PinchBurst, "camera": Camera}


def make_layer(spec, env):
    t = spec.get("type", "text")
    if t not in TYPES:
        raise ValueError(f"unknown layer type '{t}'. Known: {', '.join(TYPES)}")
    return TYPES[t](spec, env)
