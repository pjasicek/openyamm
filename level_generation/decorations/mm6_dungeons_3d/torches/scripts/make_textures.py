#!/usr/bin/env python3
"""Procedural textures of the torch batch (flames use the shared ../textures/flame02 flipbook, FLAMES.md):
- skulllit: the fire-lit skulls of torskul0, the outdoor props `skull` texture (read only) remapped through an orange
  ramp, so its mean is about the native crown colour and COLOR_0 (at most one) only darkens it toward the jaws; the
  props normal and metallic-roughness maps are copied unchanged under the new name.
- chain: the hanging brazier's (torch03) cut-out gold chain strip.
Writes textures/skulllit_{basecolor,normal,mr}.png and textures/chain_basecolor.png. Usage: make_textures.py"""
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
PROPS = HERE.parents[1] / 'mm6_new_sorpigal_3d' / 'props' / 'textures'
# Luminance (0 = darkest, 1 = brightest texel) to sRGB: sockets near black, bone orange, highlights pale.
RAMP = [(0.0, (40, 10, 0)), (0.3, (190, 80, 30)), (0.55, (250, 150, 80)), (0.8, (255, 195, 130)),
        (1.0, (255, 230, 180))]


def chain_texture():
    """Gold chain strip (64 x 256, cut out): alternating face-on oval links and edge-on links, 8 links per strip,
    shaded like the native chain (gold highlight, brown-pink shadow)."""
    width, height, links = 64, 256, 8
    hi = Image.new('RGBA', (width * 4, height * 4), (0, 0, 0, 0))
    draw = ImageDraw.Draw(hi)
    step = height * 4 / links
    for k in range(links):
        y0 = k * step - step * 0.18
        y1 = (k + 1) * step + step * 0.18
        if k % 2 == 0:
            draw.ellipse((width * 4 * 0.14, y0, width * 4 * 0.86, y1), outline=(255, 255, 255, 255), width=34)
        else:
            draw.rounded_rectangle((width * 4 * 0.42, y0, width * 4 * 0.58, y1), radius=20, fill=(255, 255, 255, 255))
    mask = np.asarray(hi.resize((width, height), Image.LANCZOS))[..., 3].astype(np.float32) / 255.0
    x = np.linspace(-1, 1, width)[None, :]
    shade = 0.55 + 0.45 * np.cos(x * 1.4)                      # rounder links: lighter in the middle
    gold = np.array([226, 168, 72], np.float32); shadow = np.array([120, 70, 58], np.float32)
    rng = np.random.default_rng(3)
    grain = rng.normal(0, 0.05, (height, width))
    colour = shadow[None, None] + (gold - shadow)[None, None] * np.clip(shade + grain, 0, 1)[..., None]
    rgba = np.zeros((height, width, 4), np.uint8)
    rgba[..., :3] = np.clip(colour, 0, 255)
    rgba[..., 3] = np.clip(mask * 255, 0, 255)
    out = HERE / 'textures' / 'chain_basecolor.png'
    Image.fromarray(rgba).save(out, optimize=True)
    print('CHAIN', out)


def main():
    rgb = np.asarray(Image.open(PROPS / 'skull_basecolor.png').convert('RGB')).astype(np.float32) / 255.0
    luminance = rgb @ np.array([0.299, 0.587, 0.114], np.float32)
    low, high = np.percentile(luminance, 1), np.percentile(luminance, 99.5)
    t = np.clip((luminance - low) / (high - low), 0, 1)
    out = np.stack([np.interp(t, [p for p, _ in RAMP], [c[i] for _, c in RAMP]) for i in range(3)], axis=-1)
    Image.fromarray(out.astype(np.uint8)).save(HERE / 'textures' / 'skulllit_basecolor.png', optimize=True)
    for kind in ('normal', 'mr'):
        shutil.copyfile(PROPS / f'skull_{kind}.png', HERE / 'textures' / f'skulllit_{kind}.png')
    chain_texture()
    print('SKULL', HERE / 'textures' / 'skulllit_basecolor.png', out.reshape(-1, 3).mean(0).astype(int))


if __name__ == '__main__':
    main()
