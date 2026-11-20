#!/usr/bin/env python3
"""Willow strand texture for a species with crown.moss (tree59): work/<id>/moss_basecolor.png (256 x 1024 RGBA, image
top = the strand's top) and moss_normal.png. Each card carries 3-4 hanging twigs that sway slightly and end at
different lengths, with narrow leaves (ambientCG LeafSet018, CC0, narrowed to 35 %) alternating down both sides,
pointing down and out. Leaves are recoloured from the shared green palette (make_shared.GREEN), normalised to the
mean of the shared green cells, so build_tree.py tints the strands with the species leaf tint like the cards.
Usage: make_willow.py <id>"""
import json, math, os
import numpy as np
from PIL import Image
from scipy import ndimage
import common

spec = common.load(); W = spec['work']
lin, srgb = common.lin, common.srgb
SRC = os.path.join(common.SOURCE, 'LeafSet018')
color = np.asarray(Image.open(os.path.join(SRC, 'LeafSet018_1K-PNG_Color.png')).convert('RGB'), np.float32) / 255
alpha = np.asarray(Image.open(os.path.join(SRC, 'LeafSet018_1K-PNG_Opacity.png')).convert('L'), np.float32) / 255
normal = np.asarray(Image.open(os.path.join(SRC, 'LeafSet018_1K-PNG_NormalGL.png')).convert('RGB'), np.float32) / 255
if alpha.shape != color.shape[:2]:
    alpha = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).resize(color.shape[1::-1]), np.float32) / 255
if normal.shape[:2] != color.shape[:2]:
    normal = np.asarray(Image.fromarray((normal * 255).astype(np.uint8)).resize(color.shape[1::-1]), np.float32) / 255
lab, _ = ndimage.label(alpha > 0.5)
leaves = []
for sl in ndimage.find_objects(lab):
    if sl[0].stop - sl[0].start < 100:
        continue
    c, a, n = color[sl], alpha[sl], normal[sl]
    leaves.append((c, a, n, lin(c)[a > 0.5].mean(0)))
meta = json.load(open(common.shared_path('atlas.json')))
green = [c for c in meta['cells'] if c['group'] == 'green']
REF = np.average([c['mean_linear'] for c in green], axis=0, weights=[c['coverage'] for c in green])
PALETTE = [([176, 214, 64], 0.45), ([194, 222, 72], 0.2), ([150, 200, 60], 0.15), ([222, 220, 68], 0.2)]
SW, SH = 256, 1024
rng = np.random.default_rng(spec['crown']['moss'].get('seed', 707) + 11)
acc_c = np.zeros((SH, SW, 3), np.float32); acc_a = np.zeros((SH, SW), np.float32)
acc_n = np.zeros((SH, SW, 3), np.float32); acc_n[...] = (0.5, 0.5, 1.0)


def resize(img, w, h):
    return np.asarray(Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((w, h), Image.LANCZOS),
                      np.float32) / 255


def paste(bx, by, angle_deg, length, value):
    """A leaf with its base at (bx, by), tip at screen angle angle_deg (0 = up, clockwise; 180 = straight down)."""
    c, a, nm, mean = leaves[int(rng.integers(len(leaves)))]
    s = length / c.shape[0]
    h, w = max(int(c.shape[0] * s), 4), max(int(c.shape[1] * s * 0.35), 3)
    c, a, nm = resize(c, w, h), resize(a, w, h), resize(nm, w, h)
    n = nm * 2 - 1
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    pad = lambda img: np.concatenate([img, np.zeros(img.shape, img.dtype)], 0)
    cR = ndimage.rotate(pad(c), -angle_deg, reshape=True, order=1)
    aR = ndimage.rotate(pad(a), -angle_deg, reshape=True, order=1)
    nR = ndimage.rotate(pad(n), -angle_deg, reshape=True, order=1)
    th = math.radians(-angle_deg)
    nx, ny = nR[..., 0], -nR[..., 1]
    rx = nx * math.cos(th) - ny * math.sin(th); ry = nx * math.sin(th) + ny * math.cos(th)
    nR = np.stack([rx, -ry, nR[..., 2]], -1) * 0.5 + 0.5
    weights = np.array([p[1] for p in PALETTE]); weights /= weights.sum()
    target = lin(np.array(PALETTE[int(rng.choice(len(PALETTE), p=weights))][0]) / 255.0)
    ratio = lin(np.clip(cR, 0, 1)) / mean
    cl = target * value * ratio
    hh, ww = aR.shape
    ox, oy = int(round(bx - ww / 2)), int(round(by - hh / 2))
    x0, y0 = max(ox, 0), max(oy, 0); x1, y1 = min(ox + ww, SW), min(oy + hh, SH)
    if x1 <= x0 or y1 <= y0:
        return
    sub = (slice(y0 - oy, y1 - oy), slice(x0 - ox, x1 - ox))
    av = np.clip(aR[sub], 0, 1)[..., None]
    region = (slice(y0, y1), slice(x0, x1))
    acc_c[region] = acc_c[region] * (1 - av) + srgb(np.clip(cl[sub], 0, 1)) * av
    acc_n[region] = acc_n[region] * (1 - av) + nR[sub] * av
    acc_a[region] = np.maximum(acc_a[region], av[..., 0])


yy, xx = np.mgrid[:SH, :SW]
twigs = 4
for t in range(twigs):
    x0 = SW * (0.2 + 0.6 * t / (twigs - 1)) + rng.uniform(-12, 12)
    end = SH * rng.uniform(0.72, 0.97)
    phase = rng.uniform(0, 6.3); amp = rng.uniform(6, 14)
    path = [(x0 + amp * math.sin(y / rng.uniform(140, 220) + phase) + (y / SH) * rng.uniform(-18, 18), y)
            for y in np.arange(8, end, 2.0)]
    for i, (px, py) in enumerate(path):          # thin stem, tapering
        w = 1.8 * (1 - i / len(path)) + 0.7
        m = (xx - px) ** 2 + (yy - py) ** 2 < w * w
        acc_c[m] = (0.26, 0.21, 0.12); acc_a[m] = 1
    k = 0
    y = 20.0
    while y < end - 10:
        i = min(int((y - 8) / 2), len(path) - 1); px, py = path[i]
        side = 1 if k % 2 == 0 else -1
        f = y / end
        paste(px, py, 180 - side * rng.uniform(18, 38), rng.uniform(58, 80) * (1.0 - 0.25 * f),
              rng.uniform(0.8, 1.2) * (0.85 + 0.15 * (1 - f)))
        y += rng.uniform(13, 19); k += 1
acc_a[:, :3] = acc_a[:, -3:] = 0; acc_a[:4] = 0; acc_a[-4:] = 0
inside = acc_a > 0.5
# normalise to the shared green cells' mean, so the species leaf tint gives the same colour as on the cards
scale = REF / lin(acc_c[inside]).mean(0)
acc_c = srgb(np.clip(lin(acc_c) * scale, 0, 1)).astype(np.float32)
idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
acc_c = acc_c[idx[0], idx[1]]; acc_n = np.where(inside[..., None], acc_n, acc_n[idx[0], idx[1]])
Image.fromarray((np.dstack([np.clip(acc_c, 0, 1), acc_a]) * 255).astype(np.uint8), 'RGBA').save(
    os.path.join(W, 'moss_basecolor.png'))
Image.fromarray((np.clip(acc_n, 0, 1) * 255).astype(np.uint8), 'RGB').save(os.path.join(W, 'moss_normal.png'))
print('WILLOW strand texture coverage', round(float(inside.mean()), 3))
