#!/usr/bin/env python3
"""Neck seam (2026-11-01, viewer close-ups): the neck below the head-set cut (z 0.66) and the skin in the tunic's
V-opening are body texels, painted hot pale pink by the body retexture (graded median 255/170/130) against the head
set's neck (218/138/97 at z 0.68-0.72), so the cut showed as a pale band. The body's skin texels above z 0.50 (hue
5-30, saturation 0.15-0.65, value > 0.45; soft-edged) take one gain per channel that brings their median to the head
neck's. Runs on the GRADED body colour, after grade_basecolor.py (re-run it after every grade).
Usage (project folder): ../claude_shared/gltf_venv/bin/python scripts/neck_match.py"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

sys.path.insert(0, str(Path(__file__).resolve().parent))
from texel_xyz import texel_xyz  # noqa: E402


def hsv(a):
    mx = a.max(-1); mn = a.min(-1); d = mx - mn + 1e-9; r, g, b = a[..., 0], a[..., 1], a[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, d / (mx + 1e-9), mx


N = 2048
path = Path('textures/pm1d_basecolor_graded.png')
B = np.asarray(Image.open(path).convert('RGB'), float) / 255
d = np.load('v2/work/uv_UVMap.npz')
X, cov, _ = texel_xyz('v2/work/uv_UVMap.npz', N, (d['head'] == 0) & (d['hand'] == 0))
h, s, v = hsv(B); z = X[..., 2]
skin = cov & (z > 0.50) & (h > 5) & (h < 30) & (s > 0.15) & (s < 0.65) & (v > 0.45)
src = np.median(B[skin & (z > 0.56)], 0)
th = np.load('v2/work/texel_head_1k.npz')
H = np.asarray(Image.open('v2/textures/pm1d_head_basecolor.png').convert('RGB').resize((1024, 1024), Image.LANCZOS), float) / 255
mh = th['cov'] & (th['comp'] == 2) & (th['xyz'][..., 2] > 0.68) & (th['xyz'][..., 2] < 0.72) & (th['xyz'][..., 1] < 0.03)
dst = np.median(H[mh], 0)
gain = dst / np.maximum(src, 1e-3)
w = np.clip(ndi.gaussian_filter(skin.astype(float), 1.5) * 1.5, 0, 1) * cov
out = B * (1 - w[..., None]) + np.clip(B * gain, 0, 1) * w[..., None]
Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(path)
print('NECKMATCH texels', int(skin.sum()), 'body median', (src * 255).round(0).tolist(), 'head neck', (dst * 255).round(0).tolist(),
      'gain', gain.round(3).tolist())
