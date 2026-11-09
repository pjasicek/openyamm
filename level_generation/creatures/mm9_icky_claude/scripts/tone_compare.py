#!/usr/bin/env python3
"""Colour drift of a repaint on the surface (TEXTURE_QUALITY_PASS.md, wing-tone check of ../mm9_wingedmutant_claude):
area-weighted points on the same bind-pose triangles, the approved texture sampled through the old UVs and the new
texture through the new UVs, grouped by the approved texel's hue class.

Usage: tone_compare.py <old uv3d npz> <new uv3d npz> <old texture> <new texture> [--json out]
The two npz files are dump_uv3d.py dumps of the same mesh (same triangle order). Prints per class: share, mean sRGB,
luminance sd, linear p95, for approved -> new, plus the mean per-triangle colour error."""
import argparse, json
import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument('old_uv'); ap.add_argument('new_uv'); ap.add_argument('old_tex'); ap.add_argument('new_tex')
ap.add_argument('--json'); ap.add_argument('--samples', type=int, default=400000)
a = ap.parse_args()
old, new = np.load(a.old_uv), np.load(a.new_uv)
if old['uv'].shape != new['uv'].shape:
    raise SystemExit('dumps do not match')
tri = new['xyz']
area = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) / 2
rng = np.random.default_rng(1)
t = rng.choice(len(tri), a.samples, p=area / area.sum())
r = rng.random((a.samples, 2)); s = np.sqrt(r[:, 0])
bary = np.stack([1 - s, s * (1 - r[:, 1]), s * r[:, 1]], 1)


def sample(path, uv):
    img = np.asarray(Image.open(path).convert('RGB'), np.float32) / 255
    h, w = img.shape[:2]
    p = (uv[t] * bary[:, :, None]).sum(1)
    x = np.clip(p[:, 0] * w - 0.5, 0, w - 1.001); y = np.clip((1 - p[:, 1]) * h - 0.5, 0, h - 1.001)
    x0, y0 = x.astype(int), y.astype(int); fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


A, B = sample(a.old_tex, old['uv']), sample(a.new_tex, new['uv'])


def lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


W = np.array([0.2126, 0.7152, 0.0722])


def hue(c):
    mx, mn = c.max(1), c.min(1); d = mx - mn + 1e-9
    r, g, b = c.T
    return np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60, d / (mx + 1e-9), mx


def stats(c):
    L = lin(c) @ W
    return {'rgb': [round(float(v) * 255, 1) for v in c.mean(0)], 'sd': round(float((c @ W).std() * 255), 1),
            'p95': round(float(np.percentile(L, 95)), 3), 'p5': round(float(np.percentile(L, 5)), 3)}


h, sat, val = hue(A)
classes = {'red': ((h >= 320) | (h < 25)) & (sat > 0.25), 'yellow/olive': (h >= 25) & (h < 90) & (sat > 0.25),
           'green': (h >= 90) & (h < 170) & (sat > 0.25), 'blue/violet': (h >= 170) & (h < 320) & (sat > 0.25),
           'grey': sat <= 0.25, 'all': np.ones(len(A), bool)}
report = {}
for name, m in classes.items():
    if m.sum() < 500:
        continue
    report[name] = {'share': round(float(m.mean()), 3), 'approved': stats(A[m]), 'new': stats(B[m])}
    print(f"{name:13s} {m.mean()*100:5.1f}%  approved {report[name]['approved']}  new {report[name]['new']}")
per = np.zeros((len(tri), 3)); num = np.bincount(t, minlength=len(tri))[:, None].clip(1)
diff = A - B
for c in range(3):
    per[:, c] = np.bincount(t, diff[:, c], minlength=len(tri))
per /= num
report['mean_triangle_error_8bit'] = round(float(np.abs(per).mean() * 255), 2)
print('mean per-triangle colour error (8 bit)', report['mean_triangle_error_8bit'])
if a.json:
    json.dump(report, open(a.json, 'w'), indent=1)
