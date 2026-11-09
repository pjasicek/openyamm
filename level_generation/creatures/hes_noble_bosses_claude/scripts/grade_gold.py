#!/usr/bin/env python3
"""Lift a shell's gold toward the concept's pale rich gold: texels of gold hue (20-55 degrees) gain value and a little
saturation, smoothly weighted by hue and saturation; ivory, resin and glow are untouched. Keeps <base>_raw.png.
Usage: grade_gold.py <textures/boss_shell_base.png> [value_gain=1.22] [sat_gain=1.1]"""
import sys, shutil
from pathlib import Path
import numpy as np
from PIL import Image
p = Path(sys.argv[1]); raw = p.with_name(p.stem + '_raw.png')
if not raw.exists():
    shutil.copy(p, raw)
vg = float(sys.argv[2]) if len(sys.argv) > 2 else 1.22
sg = float(sys.argv[3]) if len(sys.argv) > 3 else 1.1
im = np.asarray(Image.open(raw).convert('RGB')).astype(np.float32) / 255
mx = im.max(-1); mn = im.min(-1); d = np.maximum(mx - mn, 1e-6); sat = (mx - mn) / np.maximum(mx, 1e-6)
r, g, b = im[..., 0], im[..., 1], im[..., 2]
hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
w = np.clip(1 - np.abs(hue - 38) / 22, 0, 1) * np.clip((sat - 0.15) / 0.2, 0, 1) * np.clip((mx - 0.08) / 0.15, 0, 1)
w = w[..., None]
grey = im.mean(-1, keepdims=True)
out = grey + (im - grey) * (1 + (sg - 1) * w)
out = out * (1 + (vg - 1) * w)
out = np.clip(out, 0, 1)
Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(p)
print('graded', p.name, 'gold texels', round(float((w > 0.5).mean()), 3))
