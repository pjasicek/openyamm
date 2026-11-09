#!/usr/bin/env python3
"""v2 leaf-cluster atlas (work_v2/leaves_basecolor.png 1024 RGBA, work_v2/leaves_normal.png 1024): four 512 px cells,
each a whorl of ~100 real-scale leaves on 8-10 twigs radiating from the centre (a cell spans one 0.5 m card, so a 65-85 px leaf is 6-8 cm).
Leaves come from ambientCG LeafSet022 (CC0). Each leaf keeps its own tangent normal, rotated with it, plus a fold
across its width (the halves tilt +-25 degrees), so in-engine lighting picks out individual leaves. Value varies per
leaf and darkens toward each twig's base; there is no baked crown occlusion here (that is the COLOR_0 vertex colour).
RGB/normals are dilated into transparent texels so mips and the alpha cutoff never pick up a halo."""
import os, math
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, 'source', 'leafset022')
OUT = os.path.join(HERE, 'work_v2')
os.makedirs(OUT, exist_ok=True)
color = np.asarray(Image.open(os.path.join(SRC, 'LeafSet022_1K-PNG_Color.png')).convert('RGB'), np.float32) / 255
alpha = np.asarray(Image.open(os.path.join(SRC, 'LeafSet022_1K-PNG_Opacity.png')).convert('L'), np.float32) / 255
normal = np.asarray(Image.open(os.path.join(SRC, 'LeafSet022_1K-PNG_NormalGL.png')).convert('RGB'), np.float32) / 255
lab, _ = ndimage.label(alpha > 0.5)
leaves = []
for sl in ndimage.find_objects(lab):
    if sl[0].stop - sl[0].start < 100:
        continue
    pad = 6
    ys = slice(max(sl[0].start - pad, 0), sl[0].stop + pad); xs = slice(max(sl[1].start - pad, 0), sl[1].stop + pad)
    leaves.append((color[ys, xs], alpha[ys, xs], normal[ys, xs]))
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)
mean = np.mean([lin(c)[a > 0.5].mean(0) for c, a, _ in leaves], 0)
TARGET = lin(np.array([56, 138, 38]) / 255.0)       # leaf albedo; the vertex occlusion (0.3..1) darkens the crown
CELL = 512


def resize(img, w, h):
    return np.asarray(Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((w, h), Image.LANCZOS),
                      np.float32) / 255


def paste_leaf(acc_c, acc_a, acc_n, r, bx, by, angle_deg, length_px, value):
    """One leaf with its stem end at (bx, by), tip pointing at screen angle angle_deg (0 = up, clockwise)."""
    c, a, nm = leaves[r.integers(len(leaves))]
    s = length_px / c.shape[0]
    hgt, wid = max(int(c.shape[0] * s), 4), max(int(c.shape[1] * s), 3)
    c, a, nm = resize(c, wid, hgt), resize(a, wid, hgt), resize(nm, wid, hgt)
    # fold: the left/right halves tilt about the midrib (tangent x), mild cup toward the tip
    x = (np.arange(wid) - (wid - 1) / 2) / max(wid / 2, 1)
    fold = np.clip(x, -1, 1)[None, :] * math.sin(math.radians(25)) * r.choice([-1.0, 1.0])
    n = nm * 2 - 1
    n[..., 0] = n[..., 0] + fold
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    # stem at the bottom: pad below so rotation about the image centre is rotation about the stem end
    pad = lambda img: np.concatenate([img, np.zeros(img.shape, img.dtype)], 0)
    cR = ndimage.rotate(pad(c), -angle_deg, reshape=True, order=1)
    aR = ndimage.rotate(pad(a), -angle_deg, reshape=True, order=1)
    nR = ndimage.rotate(pad(n), -angle_deg, reshape=True, order=1)
    th = math.radians(-angle_deg)                        # rotate tangent xy with the image (image y is down)
    nx, ny = nR[..., 0], -nR[..., 1]
    rx = nx * math.cos(th) - ny * math.sin(th); ry = nx * math.sin(th) + ny * math.cos(th)
    nR = np.stack([rx, -ry, nR[..., 2]], -1) * 0.5 + 0.5
    cl = lin(np.clip(cR, 0, 1)) / mean * TARGET * value
    cl *= np.array([r.uniform(0.88, 1.12), 1.0, r.uniform(0.85, 1.1)])
    hh, ww = aR.shape
    ox, oy = int(round(bx - ww / 2)), int(round(by - hh / 2))
    ys_, xs_ = np.nonzero(aR > 0.05)
    if ys_.size == 0 or oy + ys_.min() < 8 or ox + xs_.min() < 8 or oy + ys_.max() >= CELL - 8 \
            or ox + xs_.max() >= CELL - 8:
        return False
    x0, y0 = max(ox, 0), max(oy, 0); x1, y1 = min(ox + ww, CELL), min(oy + hh, CELL)
    sub = (slice(y0 - oy, y1 - oy), slice(x0 - ox, x1 - ox))
    av = np.clip(aR[sub], 0, 1)[..., None]
    region = (slice(y0, y1), slice(x0, x1))
    acc_c[region] = acc_c[region] * (1 - av) + srgb(cl[sub]) * av
    acc_n[region] = acc_n[region] * (1 - av) + nR[sub] * av
    acc_a[region] = np.maximum(acc_a[region], av[..., 0])
    return True


def cluster(seed):
    r = np.random.default_rng(seed)
    acc_c = np.zeros((CELL, CELL, 3), np.float32); acc_a = np.zeros((CELL, CELL), np.float32)
    acc_n = np.zeros((CELL, CELL, 3), np.float32); acc_n[...] = (0.5, 0.5, 1.0)
    yy, xx = np.mgrid[:CELL, :CELL]
    # a whorl at a branch end: 6-7 twigs radiating from near the centre, alternate leaves along each, leaves
    # filling the centre last (on top) so the card reads as a dense round spray from any side
    origin = np.array([CELL * 0.5, CELL * 0.5]) + r.uniform(-12, 12, 2)
    twigs = int(r.integers(8, 11))
    spread = np.sort(r.uniform(0, 360, twigs))
    spread = np.linspace(0, 360, twigs, endpoint=False) + r.uniform(0, 360) + r.uniform(-14, 14, twigs)
    placed = 0
    for t, heading in enumerate(spread):
        steps = int(r.uniform(70, 95)); ang = math.radians(heading); p = origin.copy(); path = []
        for i in range(steps):
            path.append(p.copy()); p += 2.0 * np.array([math.sin(ang), -math.cos(ang)]); ang += r.uniform(-0.02, 0.02)
        for i, (tx, ty) in enumerate(path):
            w = 2.6 * (1 - i / steps) + 0.9
            m = (xx - tx) ** 2 + (yy - ty) ** 2 < w * w
            acc_c[m] = (0.17, 0.10, 0.06); acc_a[m] = 1
        count = int(r.integers(7, 10))
        for k in range(count):
            f = 0.25 + 0.72 * (k + r.uniform(-0.2, 0.2)) / count
            i = min(int(f * steps), steps - 1); tx, ty = path[i]
            side = 1 if k % 2 == 0 else -1
            value = r.uniform(0.78, 1.15) * (0.75 + 0.25 * f)          # darker toward the whorl centre
            placed += paste_leaf(acc_c, acc_a, acc_n, r, tx, ty, heading + side * r.uniform(30, 55),
                                 r.uniform(66, 84), value)
        tx, ty = path[-1]
        placed += paste_leaf(acc_c, acc_a, acc_n, r, tx, ty, heading + r.uniform(-12, 12), r.uniform(70, 86),
                             r.uniform(0.95, 1.2))
    for k in range(int(r.integers(14, 20))):
        heading = r.uniform(0, 360); d = r.uniform(10, 120)
        tx, ty = origin + d * np.array([math.sin(math.radians(heading)), -math.cos(math.radians(heading))])
        placed += paste_leaf(acc_c, acc_a, acc_n, r, tx, ty, heading, r.uniform(64, 80), r.uniform(0.85, 1.1))
    border = np.zeros_like(acc_a); border[6:-6, 6:-6] = 1
    acc_a *= border
    return acc_c, acc_a, acc_n, placed


base = np.zeros((1024, 1024, 4), np.float32); nrm = np.zeros((1024, 1024, 3), np.float32); nrm[...] = (0.5, 0.5, 1.0)
info = []
for cell, seed in enumerate((11, 23, 37, 52)):
    c, a, nm, placed = cluster(seed)
    row, col = divmod(cell, 2)
    sl = (slice(row * CELL, (row + 1) * CELL), slice(col * CELL, (col + 1) * CELL))
    base[sl[0], sl[1], :3] = c; base[sl[0], sl[1], 3] = a; nrm[sl] = nm
    info.append((placed, round(float(a.mean()), 3)))
inside = base[..., 3] > 0.5
idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
base[..., :3] = base[..., :3][idx[0], idx[1]]
nrm = np.where(inside[..., None], nrm, nrm[idx[0], idx[1]])
Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'leaves_basecolor.png'))
Image.fromarray((np.clip(nrm, 0, 1) * 255).astype(np.uint8), 'RGB').save(os.path.join(OUT, 'leaves_normal.png'))
preview = Image.new('RGBA', (1024, 1024), (150, 160, 175, 255))
preview.alpha_composite(Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8) * inside[..., None], 'RGBA'))
preview.convert('RGB').save(os.path.join(OUT, 'atlas_preview.png'))
print('ATLAS v2 leaves and coverage per cell', info)
