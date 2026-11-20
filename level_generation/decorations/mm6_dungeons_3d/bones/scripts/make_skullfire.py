#!/usr/bin/env python3
"""Fire-lit skull texture for torskul0: the Meshy skull's base colour (textures/skull at 2k from the retexture
download) mapped by its luminance through a ramp of the native torskul0 skull colours (measured quantiles: dark
red-brown, saturated orange, yellow-cream highlights), so the sockets and sutures stay dark and the bone glows as the
sprite paints it. The torch builder darkens it further by height in COLOR_0 (bright crowns, near-black jaws).
Run `make_tex.py ../meshy/skull_retexture_v1 skullfire 512` first (normal and metallic-roughness); this replaces
its base colour. Usage: make_skullfire.py"""
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOB = os.path.join(HERE, 'meshy', 'skull_retexture_v1')
OUT = os.path.join(HERE, 'textures')
SIZE = (512, 512)
# (relative luminance, sRGB) stops after the native sprite's skull pixels (25th..98th percentiles, brightened).
# The ramp is the crown's light (the builder's COLOR_0 gradient only darkens it toward the jaws), so its mean sits
# at the native crown colour (252, 168, 96): the crowns' COLOR_0 tint then clamps at one onto that saturated orange,
# not onto pale cream (the first ramp's highlights read washed out in the gallery).
RAMP = [(0.0, (60, 10, 2)), (0.3, (170, 58, 14)), (0.6, (226, 104, 44)), (0.85, (246, 146, 76)),
        (1.0, (252, 172, 100))]

base = np.asarray(Image.open(os.path.join(JOB, 'texture_urls_0_base_color.png')).convert('RGB').resize(
    SIZE, Image.LANCZOS), np.float64)
lum = base @ np.array([0.2126, 0.7152, 0.0722])
lo, hi = np.percentile(lum, 2), np.percentile(lum, 98)
t = np.clip((lum - lo) / (hi - lo), 0, 1)
stops = np.array([s for s, _ in RAMP])
colours = np.array([c for _, c in RAMP], np.float64)
out = np.stack([np.interp(t, stops, colours[:, k]) for k in range(3)], axis=-1)
Image.fromarray(np.round(out).astype(np.uint8)).save(os.path.join(OUT, 'skullfire_basecolor.png'))
print('SKULLFIRE mean', out.reshape(-1, 3).mean(0).round(1).tolist())
