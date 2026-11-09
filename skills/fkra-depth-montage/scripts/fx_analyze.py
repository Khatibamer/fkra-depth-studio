# Copyright (c) 2026 Amer Khatib (FKRA AI). All rights reserved.
# FKRA Depth Studio — licensed under the FKRA Source-Available License 1.0 (see LICENSE).
# Commercial use, redistribution or re-publishing requires written permission.
"""Analyse a talking-head video once: person matte (mask.mkv) + tracking (track.json).

track.json per frame:
  face  [cx, cy, w, h]          face box centre/size (px, smoothed, gaps interpolated)
  head  [x, y]                  top of the head incl. hair (px)  -> anchor for "above head"
  body  [x0, y0, x1, y1]        person bounding box from the matte
  hands [{tip, thumb, palm, pinch}]  index tip / thumb tip / palm centre (px), pinch = tip-thumb distance / face width
  rms   0..1                    audio loudness (normalised)  -> audio-reactive moves
"""
from __future__ import annotations

import json
import os
import subprocess
import wave

import cv2
import numpy as np

from fx_core import FrameReader, FrameWriter, asset, probe


def _guided(I, p, r, eps):
    m = lambda x: cv2.boxFilter(x, -1, (r, r))
    mI, mp = m(I), m(p)
    a = (m(I * p) - mI * mp) / (m(I * I) - mI * mI + eps)
    b = mp - a * mI
    return m(a) * I + m(b)


def _smooth_series(arr: np.ndarray, valid: np.ndarray, sigma: float) -> np.ndarray:
    """Interpolate gaps then gaussian-smooth each column (offline, zero lag)."""
    n = len(arr)
    out = arr.astype(np.float64).copy()
    idx = np.arange(n)
    if valid.sum() == 0:
        return out
    for c in range(arr.shape[1]):
        out[:, c] = np.interp(idx, idx[valid], arr[valid, c])
    if sigma > 0 and n > 3:
        k = int(sigma * 3) * 2 + 1
        g = np.exp(-0.5 * (np.arange(k) - k // 2) ** 2 / sigma ** 2)
        g /= g.sum()
        pad = np.pad(out, ((k // 2, k // 2), (0, 0)), mode="edge")
        out = np.stack([np.convolve(pad[:, c], g, mode="valid") for c in range(arr.shape[1])], 1)
    return out


def _audio_rms(path, fps, n):
    tmp = path + ".rms.wav"
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vn", "-ac", "1", "-ar", "16000",
                        "-f", "wav", tmp])
    if r.returncode != 0 or not os.path.exists(tmp):
        return [0.0] * n
    with wave.open(tmp) as w:
        s = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    os.remove(tmp)
    hop = 16000 / fps
    v = np.array([np.sqrt(np.mean(s[int(i * hop):int((i + 1) * hop)] ** 2) + 1e-12) if int(i * hop) < len(s)
                  else 0.0 for i in range(n)])
    hi = np.percentile(v, 98) if v.max() > 0 else 1
    v = np.clip(v / max(hi, 1e-6), 0, 1)
    # light attack/release so pulses feel musical
    out, prev = [], 0.0
    for x in v:
        prev = x if x > prev else prev * 0.82 + x * 0.18
        out.append(round(float(prev), 3))
    return out


def analyze(video, outdir, hands=True, long_side=960, temporal=0.35, max_frames=None):
    from mediapipe import Image as MPImage, ImageFormat
    from mediapipe.tasks.python import BaseOptions, vision

    info = probe(video)
    W, H, fps = info["w"], info["h"], info["fps"]
    k = min(1.0, long_side / max(W, H))
    aw, ah = int(round(W * k / 2) * 2), int(round(H * k / 2) * 2)
    os.makedirs(outdir, exist_ok=True)
    VM = vision.RunningMode.VIDEO
    seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=BaseOptions(model_asset_path=asset("seg")), running_mode=VM,
        output_confidence_masks=True, output_category_mask=False))
    face = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
        base_options=BaseOptions(model_asset_path=asset("face")), running_mode=VM,
        min_detection_confidence=0.5))
    hand = vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=asset("hand")), running_mode=VM, num_hands=2,
        min_hand_detection_confidence=0.5, min_tracking_confidence=0.5)) if hands else None

    rd = FrameReader(video, aw, ah)
    mw = FrameWriter(os.path.join(outdir, "mask.mkv"), W, H, info["rate"], gray=True, codec="ffv1")
    sx, sy = W / aw, H / ah
    faces, fvalid, heads, bodies, hand_rows = [], [], [], [], []
    prev = None
    i = 0
    while True:
        fr = rd.read()
        if fr is None or (max_frames and i >= max_frames):
            break
        ts = int(i * 1000 / fps)
        mpi = MPImage(image_format=ImageFormat.SRGB, data=np.ascontiguousarray(fr))
        conf = seg.segment_for_video(mpi, ts).confidence_masks
        m = 1.0 - conf[0].numpy_view().astype(np.float32)
        if m.ndim == 3:
            m = m[..., 0]
        if prev is not None and temporal > 0:
            m = m * (1 - temporal) + prev * temporal
        prev = m
        g = cv2.cvtColor(fr, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
        m2 = np.clip(_guided(g, m, 9, 2e-3), 0, 1)
        m2 = np.clip((m2 - 0.25) / 0.5, 0, 1)
        m2 = m2 * m2 * (3 - 2 * m2)  # smoothstep: crisp but not aliased
        full = cv2.resize(m2, (W, H), interpolation=cv2.INTER_LINEAR)
        mw.write((full * 255).astype(np.uint8))

        # body box + head top from matte
        ys, xs = np.where(m2 > 0.5)
        if len(xs) > 50:
            body = [float(xs.min() * sx), float(ys.min() * sy), float(xs.max() * sx), float(ys.max() * sy)]
        else:
            body = None
        bodies.append(body)

        det = face.detect_for_video(mpi, ts).detections
        if det:
            b = max(det, key=lambda d: d.bounding_box.width * d.bounding_box.height).bounding_box
            cx, cy = (b.origin_x + b.width / 2), (b.origin_y + b.height / 2)
            faces.append([cx * sx, cy * sy, b.width * sx, b.height * sy])
            fvalid.append(True)
            # head top = first matte row above the face, inside the face columns
            c0, c1 = int(max(0, b.origin_x + b.width * .25)), int(min(aw, b.origin_x + b.width * .75))
            col = m2[:, c0:max(c0 + 1, c1)].mean(1)
            rows = np.where(col[:int(max(1, b.origin_y + b.height * .3))] > 0.5)[0]
            top = rows.min() if len(rows) else b.origin_y - b.height * .45
            heads.append([cx * sx, float(top * sy)])
        else:
            faces.append([0, 0, 0, 0])
            fvalid.append(False)
            heads.append([body[0] / 2 + body[2] / 2, body[1]] if body else [W / 2, H * .25])

        hs = []
        if hand:
            res = hand.detect_for_video(mpi, ts)
            fw = faces[-1][2] if fvalid[-1] else W * .25
            for lm in res.hand_landmarks:
                p = lambda k: [lm[k].x * W, lm[k].y * H]
                tip, th = p(8), p(4)
                palm = [(lm[0].x + lm[9].x) / 2 * W, (lm[0].y + lm[9].y) / 2 * H]
                pinch = float(np.hypot(tip[0] - th[0], tip[1] - th[1]) / max(fw, 1))
                hs.append({"tip": tip, "thumb": th, "palm": palm, "pinch": round(pinch, 3)})
        hand_rows.append(hs)
        i += 1
        if i % 60 == 0:
            print(f"[fkra-depth] analysed {i}/{info['frames']} frames")
    rd.close()
    mw.close()
    for det in (seg, face, hand):
        if det:
            det.close()

    n = i
    fa = _smooth_series(np.array(faces), np.array(fvalid), sigma=2.0)
    he = _smooth_series(np.array(heads), np.ones(n, bool), sigma=2.5)
    rms = _audio_rms(video, fps, n) if info["audio"] else [0.0] * n
    frames = []
    for k in range(n):
        frames.append({
            "face": [round(float(v), 1) for v in fa[k]] if any(fvalid) else None,
            "face_seen": bool(fvalid[k]),
            "head": [round(float(v), 1) for v in he[k]],
            "body": [round(v, 1) for v in bodies[k]] if bodies[k] else None,
            "hands": [{kk: ([round(x, 1) for x in vv] if isinstance(vv, list) else vv) for kk, vv in h.items()}
                      for h in hand_rows[k]],
            "rms": rms[k],
        })
    track = {"video": os.path.abspath(video), "w": W, "h": H, "fps": fps, "rate": info["rate"],
             "frames": frames}
    with open(os.path.join(outdir, "track.json"), "w") as f:
        json.dump(track, f, separators=(",", ":"))
    seen = sum(fvalid)
    hands_seen = sum(1 for h in hand_rows if h)
    print(f"[fkra-depth] done: {n} frames, face in {seen}, hands in {hands_seen} -> {outdir}")
    return track
