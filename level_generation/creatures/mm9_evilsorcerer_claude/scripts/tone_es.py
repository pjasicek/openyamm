#!/usr/bin/env python3
"""Tone towards MM9, on the shared images (not per tier): our brass is pale and bright, MM9's is an olive, dark gold. Pixels in the gold hue band come down in value, up in saturation and a little towards olive. Reads *_raw_graded / head *_final, writes *_tone.png. Project folder."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ni
GAIN, SAT, HUE = 0.60, 1.15, 5.0
T = Path('textures')
def tone(p, out):
    a = np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
    mx, mn = a.max(2), a.min(2); s = (mx - mn) / np.maximum(mx, 1e-6); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    h = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    m = np.clip((h - 20) / 8, 0, 1) * np.clip((66 - h) / 8, 0, 1) * np.clip((s - 0.28) / 0.15, 0, 1) * np.clip((mx - 0.25) / 0.15, 0, 1)
    m = ni.gaussian_filter(m, 0.6)
    v2 = mx * (1 - m * (1 - GAIN)); s2 = np.clip(s * (1 + m * (SAT - 1)), 0, 1); h2 = h + m * HUE
    # back to rgb
    c = v2 * s2; hp = (h2 / 60) % 6; x = c * (1 - np.abs(hp % 2 - 1)); z = np.zeros_like(c)
    sel = [(hp < 1, c, x, z), ((hp >= 1) & (hp < 2), x, c, z), ((hp >= 2) & (hp < 3), z, c, x), ((hp >= 3) & (hp < 4), z, x, c), ((hp >= 4) & (hp < 5), x, z, c), (hp >= 5, c, z, x)]
    out_rgb = np.zeros_like(a); M = v2 - c
    for sl, rr, gg, bb in sel:
        out_rgb[sl, 0] = (rr + M)[sl]; out_rgb[sl, 1] = (gg + M)[sl]; out_rgb[sl, 2] = (bb + M)[sl]
    res = a * (1 - m[..., None]) + out_rgb * m[..., None]
    if 'esa_' in str(out):              # tier A's navy reads black under the viewer's and game's light: MM9's is a visible dark blue
        nv = np.clip((h - 195) / 12, 0, 1) * np.clip((265 - h) / 12, 0, 1) * np.clip((s - 0.2) / 0.15, 0, 1)
        res = res * (1 + 0.8 * nv[..., None])
    Image.fromarray((np.clip(res, 0, 1) * 255 + .5).astype('u1')).save(out)
    print('TONE', out, round(float(m.mean()), 3))
for src, dst in (('es_up_raw_graded', 'es_up_tone'), ('es_low_raw_graded', 'es_low_tone'), ('esa_low_raw_graded', 'esa_low_tone'), ('esa_up_raw_graded', 'esa_up_tone'), ('es_head_a_final', 'es_head_a_tone'), ('es_head_b_final', 'es_head_b_tone'), ('es_head_c_final', 'es_head_c_tone')):
    tone(T / f'{src}.png', T / f'{dst}.png')
