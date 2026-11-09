#!/usr/bin/env python3
"""Keep the approved colours on a fresh paint (MM9_TEXTURE_PASS_BRIEF.md step 3; wing-tone correction of
../mm9_wingedmutant_claude): per hue class of the NEW paint, each channel's distribution is mapped onto the approved
paint's distribution at the same surface points. A monotone curve per class, soft-blended between classes: levels
change, edges and the new paint's detail stay where they are, nothing spatial comes from the old paint.

Usage: tone_match.py <old uv3d npz> <new uv3d npz> <old texture> <new texture> <out texture> [--json report]
                     [--strength 1.0] [--push class=r,g,b]
The npz files are dump_uv3d.py dumps of the same mesh. Classes: red (mouth, tips), orange (spike tips: a class of its
own, or the yellow belly's curve washes them out), yellow (belly, horns, stalk, limbs), green (scales), blue/violet
(mouth interior); empty classes are skipped."""
import argparse, json
import numpy as np
from PIL import Image
from scipy import ndimage

ap = argparse.ArgumentParser()
ap.add_argument('old_uv'); ap.add_argument('new_uv'); ap.add_argument('old_tex'); ap.add_argument('new_tex')
ap.add_argument('out'); ap.add_argument('--json'); ap.add_argument('--strength', type=float, default=1.0)
ap.add_argument('--samples', type=int, default=600000)
ap.add_argument('--push', action='append', default=[], help="class=r,g,b gain after the curves, e.g. orange=1.2,0.75,0.8")
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


def rows_cols(uv, h, w):
    p = (uv[t] * bary[:, :, None]).sum(1)
    return (np.clip(((1 - p[:, 1]) * h).astype(int), 0, h - 1), np.clip((p[:, 0] * w).astype(int), 0, w - 1))


A_img = np.asarray(Image.open(a.old_tex).convert('RGB'), np.float32) / 255
B_img = np.asarray(Image.open(a.new_tex).convert('RGB'), np.float32) / 255
ar, ac = rows_cols(old['uv'], *A_img.shape[:2])
br, bc = rows_cols(new['uv'], *B_img.shape[:2])
A, B = A_img[ar, ac], B_img[br, bc]

blur = ndimage.gaussian_filter(B_img, (1.5, 1.5, 0))
mx, mn = blur.max(-1), blur.min(-1); d = mx - mn + 1e-9
R, G, Bl = blur[..., 0], blur[..., 1], blur[..., 2]
h = np.where(mx == R, ((G - Bl) / d) % 6, np.where(mx == G, (Bl - R) / d + 2, (R - G) / d + 4)) * 60
bins = {'red': (h >= 320) | (h < 18), 'orange': (h >= 18) & (h < 46), 'yellow': (h >= 46) & (h < 85),
        'green': (h >= 85) & (h < 170),
        'blue': (h >= 170) & (h < 320)}
names, curves, weights, report = [], [], [], {}
x = np.linspace(0, 1, 256)
q = np.linspace(0, 1, 513)
for name, m in bins.items():
    picked = m[br, bc]
    if picked.sum() < 3000:
        continue
    curve = []
    for c in range(3):
        src, dst = np.quantile(B[picked, c], q), np.quantile(A[picked, c], q)
        src = src + np.arange(len(src)) * 1e-7           # strictly rising for flat stretches
        f = ndimage.gaussian_filter1d(np.interp(x, src, dst), 3, mode='nearest')
        curve.append(np.maximum.accumulate((1 - a.strength) * x + a.strength * f))
    names.append(name); curves.append(np.array(curve))
    weights.append(ndimage.gaussian_filter(m.astype(np.float32), 2.0))
    report[name] = {'share': round(float(picked.mean()), 3)}
w = np.stack(weights, -1)
w /= np.maximum(w.sum(-1, keepdims=True), 1e-6)
pushes = {k: tuple(float(v) for v in vals.split(',')) for k, vals in (p.split('=') for p in a.push)}
out = np.zeros_like(B_img)
for i, curve in enumerate(curves):
    for c in range(3):
        gain = pushes.get(names[i], (1, 1, 1))[c]
        out[..., c] += w[..., i] * gain * np.interp(B_img[..., c], x, curve[c])
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(a.out)
print('TONE_MATCH', json.dumps(report))
if a.json:
    json.dump({'classes': names, 'report': report, 'curves': {n: c.round(4).tolist() for n, c in zip(names, curves)}},
              open(a.json, 'w'))
