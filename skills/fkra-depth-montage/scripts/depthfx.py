#!/usr/bin/env python3
# Copyright (c) 2026 Amer Khatib (FKRA AI). All rights reserved.
# FKRA Depth Studio — licensed under the FKRA Source-Available License 1.0 (see LICENSE).
# Commercial use, redistribution or re-publishing requires written permission.
"""FKRA depth montage — layered motion design around a person, from the terminal.

  python3 depthfx.py analyze in.mp4 work/            # matte + face/head/hands/audio tracking (once)
  python3 depthfx.py preview plan.json 2.4 3.1 5     # PNG contact sheet at those seconds
  python3 depthfx.py render plan.json [--from 0 --to 8]

Render order per frame:  background → bg layers → BEHIND layers → person (matte) → FRONT layers → post (camera)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fx_core import FrameReader, FrameWriter, probe  # noqa: E402
from fx_layers import Ctx, Env, make_layer  # noqa: E402

BRAND = {"accent": "#FFC400", "text": "#FFFFFF", "dark": "#0B0B12", "pink": "#FF3D7F", "cyan": "#3DE1FF"}


def load_plan(path):
    with open(path) as f:
        plan = json.load(f)
    base = os.path.dirname(os.path.abspath(path))
    rel = lambda p: p if os.path.isabs(p) else os.path.join(base, p)
    work = rel(plan.get("work", "work"))
    plan["_video"] = rel(plan["video"])
    plan["_mask"] = rel(plan.get("mask", os.path.join(work, "mask.mkv")))
    plan["_track"] = rel(plan.get("track", os.path.join(work, "track.json")))
    plan["_out"] = rel(plan.get("out", "out.mp4"))
    for L in plan["layers"]:
        for k in ("path", "image"):
            if isinstance(L.get(k), str):
                L[k] = rel(L[k])
    return plan


def build(plan):
    with open(plan["_track"]) as f:
        track = json.load(f)
    brand = dict(BRAND, **plan.get("brand", {}))
    env = Env(track, brand)
    layers = [make_layer(dict(s), env) for s in plan["layers"]]
    return env, layers


def composite(env, layers, idx, t, frame_u8, mask_u8):
    f = frame_u8.astype(np.float32) / 255
    m = mask_u8.astype(np.float32) / 255
    ctx = Ctx(env, idx, t, f, m)
    act = [L for L in layers if L.active(t)]
    if any(L.z in ("bg", "behind") or L.__class__.__name__ == "Orbit" for L in act):
        bg = f.copy()
        for L in act:
            L.draw(bg, ctx, "bg")
        for L in act:
            L.draw(bg, ctx, "behind")
        mm = m[..., None]
        out = f * mm + bg * (1 - mm)
    else:
        out = f.copy()
    for L in act:
        L.draw(out, ctx, "front")
    for L in act:
        L.draw(out, ctx, "post")
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


def cmd_render(a):
    plan = load_plan(a.plan)
    env, layers = build(plan)
    info = probe(plan["_video"])
    W, H, fps = env.W, env.H, env.fps
    t0 = a.start or 0.0
    dur = (a.end - t0) if a.end else None
    rv = FrameReader(plan["_video"], W, H, start=t0, duration=dur)
    rm = FrameReader(plan["_mask"], W, H, gray=True, start=t0, duration=dur)
    out = a.out or plan["_out"]
    wr = FrameWriter(out, W, H, info["rate"], audio_src=plan["_video"] if info["audio"] else None,
                     start=t0, duration=dur, crf=plan.get("crf", 18))
    i0 = int(round(t0 * fps))
    k, tick = 0, time.time()
    while True:
        fr, m = rv.read(), rm.read()
        if fr is None or m is None:
            break
        idx = i0 + k
        wr.write(composite(env, layers, idx, idx / fps, fr, m))
        k += 1
        if k % 30 == 0:
            print(f"[fkra-depth] {k} frames  ({k / (time.time() - tick):.1f} fps)", flush=True)
    rv.close(), rm.close(), wr.close()
    print(f"[fkra-depth] wrote {out}  ({k} frames)")


def cmd_preview(a):
    from PIL import Image
    plan = load_plan(a.plan)
    env, layers = build(plan)
    W, H = env.W, env.H
    tiles = []
    for t in a.times:
        # warm-up: render ~0.5 s before t so trails / echoes have history
        warm = min(t, 0.5)
        rv = FrameReader(plan["_video"], W, H, start=t - warm)
        rm = FrameReader(plan["_mask"], W, H, gray=True, start=t - warm)
        n = int(round(warm * env.fps)) + 1
        img = None
        for j in range(n):
            fr, m = rv.read(), rm.read()
            if fr is None or m is None:
                break
            tt = t - warm + j / env.fps
            img = composite(env, layers, int(round(tt * env.fps)), tt, fr, m)
        check_occlusion(env, layers, t, m)
        rv.close(), rm.close()
        if img is not None:
            tiles.append((t, Image.fromarray(img)))
    if not tiles:
        sys.exit("no frames")
    th = 640
    tw = int(W * th / H)
    sheet = Image.new("RGB", (tw * len(tiles), th + 28), (20, 20, 24))
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet)
    for k, (t, im) in enumerate(tiles):
        sheet.paste(im.resize((tw, th)), (k * tw, 28))
        d.text((k * tw + 8, 6), f"{t:.2f}s", fill=(255, 196, 0))
    out = a.out or os.path.splitext(plan["_out"])[0] + "_preview.png"
    sheet.save(out)
    print(f"[fkra-depth] preview -> {out}")


def check_occlusion(env, layers, t, mask_u8):
    """Warn when text placed BEHIND the person is mostly hidden by them."""
    from fx_layers import Ctx, Text
    m = mask_u8.astype(np.float32) / 255
    idx = int(round(t * env.fps))
    for k, L in enumerate(layers):
        if not (isinstance(L, Text) and L.z == "behind" and L.active(t)):
            continue
        probe_c = np.full((env.H, env.W, 3), 0.5, np.float32)
        L.render(probe_c, Ctx(env, idx, t, probe_c, m))
        area = np.abs(probe_c - 0.5).max(2) > 0.04
        if area.sum() < 50:
            continue
        hidden = float((m[area] > 0.5).mean())
        tag = "OK" if hidden < 0.5 else "WARNING: move it up/sideways or make it bigger"
        print(f"[fkra-depth] t={t:.2f}s layer #{k} '{L.s.get('text', '')[:20]}' behind person: "
              f"{hidden * 100:.0f}% hidden -> {tag}")


def cmd_analyze(a):
    from fx_analyze import analyze
    analyze(a.video, a.outdir, hands=not a.no_hands, max_frames=a.max_frames)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("analyze")
    p.add_argument("video")
    p.add_argument("outdir")
    p.add_argument("--no-hands", action="store_true")
    p.add_argument("--max-frames", type=int)
    p.set_defaults(fn=cmd_analyze)
    p = sub.add_parser("render")
    p.add_argument("plan")
    p.add_argument("--from", dest="start", type=float)
    p.add_argument("--to", dest="end", type=float)
    p.add_argument("--out")
    p.set_defaults(fn=cmd_render)
    p = sub.add_parser("preview")
    p.add_argument("plan")
    p.add_argument("times", type=float, nargs="+")
    p.add_argument("--out")
    p.set_defaults(fn=cmd_preview)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
