# Copyright (c) 2026 Amer Khatib (FKRA AI). All rights reserved.
# FKRA Depth Studio — licensed under the FKRA Source-Available License 1.0 (see LICENSE).
# Commercial use, redistribution or re-publishing requires written permission.
"""Core helpers for the FKRA depth-montage engine: media I/O, assets, easing,
colours, text sprites and alpha blitting. Pure numpy + Pillow + OpenCV."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import urllib.request
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

__author__ = "Amer Khatib (FKRA AI)"
SIGNATURE = "Made with FKRA Depth Studio by Amer Khatib"

# --------------------------------------------------------------------------- assets
CACHE = os.path.expanduser(os.environ.get("FKRA_DEPTH_CACHE", "~/.cache/fkra-depth"))
# Every download is pinned to a fixed version and checked against its SHA-256, so a
# tampered or swapped file is refused instead of being loaded (see SECURITY.md).
_MP = "https://storage.googleapis.com/mediapipe-models"
_GF = "https://raw.githubusercontent.com/google/fonts/5bb28733cec313b63fbd415b574b5ae35c8aa8b8/ofl"
ASSETS = {
    "seg": ("models", "selfie_multiclass_256x256.tflite",
            f"{_MP}/image_segmenter/selfie_multiclass_256x256/float32/1/selfie_multiclass_256x256.tflite",
            "c6748b1253a99067ef71f7e26ca71096cd449baefa8f101900ea23016507e0e0"),
    "face": ("models", "blaze_face_short_range.tflite",
             f"{_MP}/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite",
             "b4578f35940bf5a1a655214a1cce5cab13eba73c1297cd78e1a04c2380b0152f"),
    "hand": ("models", "hand_landmarker.task",
             f"{_MP}/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
             "fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1"),
    "display": ("fonts", "Cairo.ttf", f"{_GF}/cairo/Cairo%5Bslnt%2Cwght%5D.ttf",
                "667c987182391c91f4e57a2f455b1794fb5e3ee6ca4ef3383e86bb690fa9c964"),
    "body": ("fonts", "Tajawal-Bold.ttf", f"{_GF}/tajawal/Tajawal-Bold.ttf",
             "0342ab6b74b6bd1b4b5bf7beda45a9734a2b3147a31e8a3a45b6a3417a52d9d7"),
    "mono": ("fonts", "JetBrainsMono.ttf", f"{_GF}/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
             "48715a42ec242c21e9f02692891e147d022299a52e48d5e413e1a942193ffeda"),
}


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def asset(key: str) -> str:
    """Return a verified local path for a model/font, downloading it once into the cache."""
    sub, name, url, digest = ASSETS[key]
    path = os.path.join(CACHE, sub, name)
    if os.path.exists(path) and _sha256(path) == digest:
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print(f"[fkra-depth] downloading {name} ...")
    tmp = path + ".part"
    urllib.request.urlretrieve(url, tmp)
    got = _sha256(tmp)
    if got != digest:
        os.remove(tmp)
        raise RuntimeError(f"[fkra-depth] checksum mismatch for {name}: expected {digest}, got {got}. "
                           "Refusing to load it.")
    os.replace(tmp, path)
    return path


# --------------------------------------------------------------------------- media
def probe(path: str) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height,r_frame_rate,nb_frames",
         "-of", "json", path], capture_output=True, text=True, check=True).stdout
    info = json.loads(out)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    num, den = (int(x) for x in v["r_frame_rate"].split("/"))
    dur = float(info["format"].get("duration", 0) or 0)
    fps = num / den
    n = int(v.get("nb_frames") or 0) or int(round(dur * fps))
    return {"w": int(v["width"]), "h": int(v["height"]), "fps": fps, "rate": v["r_frame_rate"],
            "duration": dur, "frames": n,
            "audio": any(s["codec_type"] == "audio" for s in info["streams"])}


class FrameReader:
    """Stream decoded frames (rgb24 or gray) from ffmpeg."""

    def __init__(self, path, w, h, gray=False, start=0.0, duration=None):
        self.w, self.h, self.c = w, h, 1 if gray else 3
        cmd = ["ffmpeg", "-v", "fatal"]  # readers may be closed early (preview)
        if start:
            cmd += ["-ss", f"{start:.3f}"]
        cmd += ["-i", path]
        if duration:
            cmd += ["-t", f"{duration:.3f}"]
        cmd += ["-vf", f"scale={w}:{h}:flags=bicubic", "-f", "rawvideo",
                "-pix_fmt", "gray" if gray else "rgb24", "-"]
        self.p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        self.size = w * h * self.c

    def read(self):
        buf = self.p.stdout.read(self.size)
        if len(buf) < self.size:
            return None
        a = np.frombuffer(buf, np.uint8).reshape(self.h, self.w, self.c)
        return a[..., 0] if self.c == 1 else a

    def close(self):
        self.p.stdout.close()
        self.p.wait()


class FrameWriter:
    def __init__(self, path, w, h, rate, audio_src=None, start=0.0, duration=None,
                 gray=False, crf=18, codec="libx264"):
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo",
               "-pix_fmt", "gray" if gray else "rgb24", "-s", f"{w}x{h}", "-r", str(rate), "-i", "-"]
        if audio_src:
            if start:
                cmd += ["-ss", f"{start:.3f}"]
            if duration:
                cmd += ["-t", f"{duration:.3f}"]
            cmd += ["-i", audio_src, "-map", "0:v", "-map", "1:a?", "-c:a", "aac", "-b:a", "192k",
                    "-shortest"]
        if codec == "ffv1":
            cmd += ["-c:v", "ffv1", "-pix_fmt", "gray" if gray else "rgb24"]
        else:
            cmd += ["-c:v", "libx264", "-crf", str(crf), "-preset", "medium",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-metadata", f"comment={SIGNATURE}"]
        cmd += [path]
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def write(self, frame: np.ndarray):
        self.p.stdin.write(np.ascontiguousarray(frame).tobytes())

    def close(self):
        self.p.stdin.close()
        if self.p.wait() != 0:
            raise RuntimeError("ffmpeg encode failed")


# --------------------------------------------------------------------------- easing / colour
def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def ease(name: str, x: float) -> float:
    x = clamp01(x)
    if name == "linear":
        return x
    if name == "in":
        return x ** 3
    if name == "inout":
        return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
    if name == "back":
        c1, c3 = 1.70158, 2.70158
        return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
    if name == "elastic":
        if x in (0, 1):
            return x
        return 2 ** (-10 * x) * math.sin((x * 10 - .75) * (2 * math.pi) / 3) + 1
    return 1 - (1 - x) ** 3  # "out" (default)


def color(c, default=(1, 1, 1, 1)):
    """'#RRGGBB' / '#RRGGBBAA' / [r,g,b(,a)] 0-255 -> floats 0..1 (r,g,b,a)."""
    if c is None:
        return default
    if isinstance(c, (list, tuple)):
        v = [x / 255 for x in c]
        return tuple(v + [1.0] * (4 - len(v)))
    s = c.lstrip("#")
    v = [int(s[i:i + 2], 16) / 255 for i in range(0, len(s), 2)]
    return tuple(v + [1.0] * (4 - len(v)))


# --------------------------------------------------------------------------- fonts / text
ARABIC = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]")


def is_rtl(s: str) -> bool:
    return bool(ARABIC.search(s))


@lru_cache(maxsize=256)
def font(name: str, size: int, weight: int = 800) -> ImageFont.FreeTypeFont:
    path = asset(name) if name in ASSETS else name
    f = ImageFont.truetype(path, max(4, int(size)), layout_engine=ImageFont.Layout.RAQM)
    try:
        axes = f.get_variation_axes()
        vals = []
        for ax in axes:
            nm = ax.get("name", b"")
            nm = nm.decode() if isinstance(nm, bytes) else str(nm)
            if nm.lower().startswith("weight") or nm.lower() == "wght":
                vals.append(max(ax["minimum"], min(ax["maximum"], weight)))
            else:
                vals.append(ax.get("default", 0))
        f.set_variation_by_axes(vals)
    except Exception:
        pass  # static font
    return f


def _mask(fnt, text, size_wh, xy, stroke=0):
    im = Image.new("L", size_wh, 0)
    ImageDraw.Draw(im).text(xy, text, font=fnt, fill=255, anchor="ls",
                            stroke_width=stroke, stroke_fill=255)
    return np.asarray(im, np.float32) / 255.0


class Sprite:
    """Straight-alpha RGBA float32 image + its pen origin (for text)."""
    __slots__ = ("rgba", "ox", "oy", "advance")

    def __init__(self, rgba, ox=0, oy=0, advance=None):
        self.rgba, self.ox, self.oy = rgba, ox, oy
        self.advance = advance if advance is not None else rgba.shape[1]


def word_sprite(word, fnt, fill=(1, 1, 1, 1), stroke=0, stroke_color=(0, 0, 0, 1),
                hollow=False, gradient=None, shadow=None, box=None) -> Sprite:
    """Render one word with baseline-consistent geometry.

    shadow: (dx, dy, blur, rgba)   box: (pad_px, radius_px, rgba)
    """
    asc, desc = fnt.getmetrics()
    x0, y0, x1, y1 = fnt.getbbox(word, anchor="ls", stroke_width=stroke)
    adv = fnt.getlength(word)
    pad = 4 + stroke
    if shadow:
        pad += int(abs(shadow[0]) + abs(shadow[1]) + shadow[2] * 2)
    bpad = box[0] if box else 0
    pad += bpad
    top, bot = min(y0, -asc), max(y1, desc)
    left, right = min(x0, 0), max(x1, adv)
    ox, oy = -left + pad, -top + pad
    W, H = int(math.ceil(right - left + 2 * pad)), int(math.ceil(bot - top + 2 * pad))
    fillm = _mask(fnt, word, (W, H), (ox, oy), 0)
    strokem = _mask(fnt, word, (W, H), (ox, oy), stroke) if stroke else None
    rgb = np.zeros((H, W, 3), np.float32)
    a = np.zeros((H, W), np.float32)

    def over(col, alpha):
        nonlocal rgb, a
        col = np.asarray(col, np.float32)
        al = alpha if col.ndim > 1 else alpha * (col[3] if col.shape[-1] == 4 else 1)
        c3 = col[..., :3] if col.ndim > 1 else col[:3]
        out_a = al + a * (1 - al)
        safe = np.maximum(out_a, 1e-6)[..., None]
        rgb = (c3 * al[..., None] + rgb * (a * (1 - al))[..., None]) / safe
        a = out_a

    if box:
        bm = Image.new("L", (W, H), 0)
        ImageDraw.Draw(bm).rounded_rectangle(
            (ox + min(x0, 0) - bpad, oy - asc * 0.92 - bpad * 0.4,
             ox + adv + bpad, oy + desc * 0.55 + bpad * 0.4), radius=box[1], fill=255)
        over(box[2], np.asarray(bm, np.float32) / 255)
    if shadow:
        base = strokem if strokem is not None else fillm
        M = np.float32([[1, 0, shadow[0]], [0, 1, shadow[1]]])
        sh = cv2.warpAffine(base, M, (W, H))
        if shadow[2] > 0:
            sh = cv2.GaussianBlur(sh, (0, 0), shadow[2])
        over(shadow[3], sh)
    if strokem is not None:
        over(stroke_color, np.clip(strokem - fillm, 0, 1) if hollow else strokem)
    if not hollow:
        if gradient:
            c1, c2 = np.asarray(gradient[0], np.float32), np.asarray(gradient[1], np.float32)
            ys = np.clip((np.arange(H, dtype=np.float32) - (oy - asc)) / max(asc, 1), 0, 1)
            grad = c1[None, None, :] * (1 - ys)[:, None, None] + c2[None, None, :] * ys[:, None, None]
            grad = np.broadcast_to(grad, (H, W, 4)).copy()
            over(grad, fillm * grad[..., 3])
        else:
            over(fill, fillm)
    return Sprite(np.dstack([rgb, a]), ox, oy, adv)


def rect_sprite(w, h, rgba, radius=0, border=None) -> Sprite:
    """Rounded rectangle; border=(px, rgba)."""
    w, h = max(1, int(w)), max(1, int(h))
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=int(radius), fill=255)
    a = np.asarray(m, np.float32) / 255
    rgb = np.broadcast_to(np.asarray(rgba[:3], np.float32), (h, w, 3)).copy()
    alpha = a * rgba[3]
    if border:
        bw, bc = border
        inner = Image.new("L", (w, h), 0)
        ImageDraw.Draw(inner).rounded_rectangle((bw, bw, w - 1 - bw, h - 1 - bw),
                                                radius=max(0, int(radius) - bw), fill=255)
        ring = np.clip(a - np.asarray(inner, np.float32) / 255, 0, 1)
        rgb = rgb * (1 - ring[..., None]) + np.asarray(bc[:3], np.float32) * ring[..., None]
        alpha = np.maximum(alpha, ring * bc[3])
    return Sprite(np.dstack([rgb, alpha]))


def image_sprite(path, width=None) -> Sprite:
    im = Image.open(path).convert("RGBA")
    if width:
        im = im.resize((int(width), int(im.height * width / im.width)), Image.LANCZOS)
    return Sprite(np.asarray(im, np.float32) / 255)


# --------------------------------------------------------------------------- compositing
def scaled(rgba: np.ndarray, s: float) -> np.ndarray:
    if abs(s - 1) < 1e-3:
        return rgba
    h, w = rgba.shape[:2]
    nw, nh = max(1, int(round(w * s))), max(1, int(round(h * s)))
    return cv2.resize(rgba, (nw, nh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)


def blit(canvas: np.ndarray, rgba: np.ndarray, x: float, y: float, opacity=1.0, clip=None):
    """Alpha-blend rgba (float 0..1) onto canvas (H,W,3 float) with top-left at x,y.
    clip=(x0,y0,x1,y1) in canvas coords limits the visible area (mask reveals)."""
    if opacity <= 0.003:
        return
    H, W = canvas.shape[:2]
    h, w = rgba.shape[:2]
    x, y = int(round(x)), int(round(y))
    cx0, cy0, cx1, cy1 = (0, 0, W, H) if clip is None else (
        max(0, int(clip[0])), max(0, int(clip[1])), min(W, int(clip[2])), min(H, int(clip[3])))
    X0, Y0, X1, Y1 = max(x, cx0), max(y, cy0), min(x + w, cx1), min(y + h, cy1)
    if X0 >= X1 or Y0 >= Y1:
        return
    src = rgba[Y0 - y:Y1 - y, X0 - x:X1 - x]
    a = src[..., 3:4] * opacity
    dst = canvas[Y0:Y1, X0:X1]
    dst *= (1 - a)
    dst += src[..., :3] * a


def blend_full(canvas, rgb, alpha):
    """canvas = canvas*(1-alpha) + rgb*alpha  (alpha HxW, rgb tuple or HxWx3)."""
    a = alpha[..., None]
    rgb = np.asarray(rgb, np.float32)
    if rgb.ndim == 1:
        rgb = rgb[:3]
    canvas *= (1 - a)
    canvas += rgb * a
