#!/usr/bin/env python3
"""Two paint fixes before the tiers, from the viewer review (2026-10-30):
- the head paint came back more orange than the body's (the head masters run warmer): head skin chroma and level are moved to
  the body's by one per-channel gain in linear light, on the skin class only, by luminance band so shadows follow too;
- the studs are paint (the geometry was deleted) and Meshy painted them chalk white: every pale blob on the black leather gets
  a steel dome: dark rim, soft highlight, and a bump in the normal map.
Inputs *_graded_raw.png (the first grade), outputs imp_basecolor_graded.png, imp_head_basecolor_graded.png, imp_normal_1k.png
(from imp_normal_1k_raw.png)."""
import shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
T = Path('textures')
for n in ('imp_basecolor_graded', 'imp_head_basecolor_graded', 'imp_normal_1k'):
    if not (T / f'{n}_raw.png').exists():
        shutil.copy(T / f'{n}.png', T / f'{n}_raw.png')
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
enc = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.maximum(c, 0) ** (1 / 2.4) - 0.055)
W = np.array([0.2126, 0.7152, 0.0722])


def hsv(rgb):
    mx, mn = rgb.max(2), rgb.min(2)
    sat = (mx - mn) / np.maximum(mx, 1e-4)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360, sat, mx


b = np.asarray(Image.open(T / 'imp_basecolor_graded_raw.png').convert('RGB'), np.float32) / 255
h = np.asarray(Image.open(T / 'imp_head_basecolor_graded_raw.png').convert('RGB'), np.float32) / 255
hb, sb, vb = hsv(b); hh, sh, vh = hsv(h)
mb = (hb > 25) & (hb < 75) & (sb > 0.4) & (vb > 0.2)
mh = (hh > 12) & (hh < 75) & (sh > 0.4) & (vh > 0.2)
lb, lh = lin(b[mb]), lin(h[mh])
print('body skin mean', (enc(lb.mean(0)) * 255).round(), 'head', (enc(lh.mean(0)) * 255).round())
gain = lb.mean(0) / lh.mean(0)
print('gain', gain.round(3))
soft = ndimage.gaussian_filter(((hh > 8) & (hh < 80) & (sh > 0.3)).astype(np.float32), 2.0)
out = lin(h) * (1 + (gain - 1) * soft[..., None])
Image.fromarray((np.clip(enc(out), 0, 1) * 255).astype(np.uint8)).save(T / 'imp_head_basecolor_graded.png')
# studs
hsvb = hsv(b)
s, v = hsvb[1], hsvb[2]
cover = np.asarray(Image.open(T / 'imp_material_classes.png').convert('L').resize((2048, 2048), Image.NEAREST)) > 0
pale = (v > 0.55) & (s < 0.35) & cover
dark = (v < 0.28) & cover
near_dark = ndimage.binary_dilation(dark, iterations=6)
lab, n = ndimage.label(ndimage.binary_opening(pale, iterations=1))
out = b.copy()
nb = np.asarray(Image.open(T / 'imp_normal_1k_raw.png').convert('RGB').resize((2048, 2048), Image.LANCZOS), np.float32) / 255
done = 0
bump = np.zeros(v.shape, np.float32)
for i, sl in enumerate(ndimage.find_objects(lab)):
    m = lab[sl] == i + 1
    area = m.sum()
    hh_, ww_ = m.shape
    if area < 40 or area > 1600 or max(hh_, ww_) > 2.6 * min(hh_, ww_):
        continue
    if near_dark[sl][ndimage.binary_dilation(m, iterations=3) ^ m].mean() < 0.6:   # on leather only
        continue
    cy, cx = ndimage.center_of_mass(m)
    r = np.sqrt(area / np.pi)
    y0, x0 = sl[0].start + cy, sl[1].start + cx
    R = int(r * 1.5) + 2
    ys, xs = np.mgrid[int(y0) - R:int(y0) + R + 1, int(x0) - R:int(x0) + R + 1]
    ok = (ys >= 0) & (ys < 2048) & (xs >= 0) & (xs < 2048)
    ys, xs = ys[ok], xs[ok]
    rr = np.hypot(ys - y0, xs - x0) / (r * 1.15)
    hl = np.exp(-(((ys - y0 + r * 0.35) ** 2 + (xs - x0 + r * 0.3) ** 2) / (r * 0.45) ** 2))
    steel = (0.20 + 0.34 * np.clip(1 - rr, 0, 1) + 0.42 * hl)[:, None] * np.array([1.0, 1.0, 1.04])
    edge = np.clip((1.25 - rr) / 0.25, 0, 1)[:, None]
    ring = np.clip((rr - 1.0) / 0.25, 0, 1)[:, None]
    out[ys, xs] = out[ys, xs] * (1 - edge) + (steel * (1 - ring) + np.array([0.03, 0.03, 0.03]) * ring) * edge
    bump[ys, xs] = np.maximum(bump[ys, xs], np.clip(1 - rr ** 2, 0, 1))
    done += 1
print('studs', done, 'of', n)
Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(T / 'imp_basecolor_graded.png')
gy, gx = np.gradient(ndimage.gaussian_filter(bump, 1.0) * 6.0)
nn = nb * 2 - 1
nn[..., 0] -= gx; nn[..., 1] += gy
nn /= np.linalg.norm(nn, axis=2, keepdims=True)
Image.fromarray(((nn * 0.5 + 0.5) * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(T / 'imp_normal_1k.png')
