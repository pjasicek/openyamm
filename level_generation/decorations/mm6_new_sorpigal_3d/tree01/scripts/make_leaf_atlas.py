#!/usr/bin/env python3
"""Leaf-cluster atlas (1024 RGBA base colour + 1024 normal) from ambientCG LeafSet022 (CC0, six single leaves).
Cells (512 px, 2 x 2): top row = clusters A/B in full colour (outer canopy), bottom row = the same clusters darkened
(inner canopy, a cheap baked occlusion selected per card by depth). Each cluster scatters ~230 small leaves (rotated about
their stems, scaled, hue/value jittered) round a short twig; the normal map rotates each leaf's tangent normal with
it. RGB is dilated into transparent texels so mips and the alpha cutoff never pick up a dark halo.
Colour: LeafSet022 is remapped to the sprite's dark green (6tree01 canopy, lit by the sun, reads ~RGB 22/43/24)."""
import os, math
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, 'source', 'leafset022')
OUT = os.path.join(HERE, 'work')
rng = np.random.default_rng(22)
color = np.asarray(Image.open(os.path.join(SRC, 'LeafSet022_1K-PNG_Color.png')).convert('RGB'), np.float32) / 255
alpha = np.asarray(Image.open(os.path.join(SRC, 'LeafSet022_1K-PNG_Opacity.png')).convert('L'), np.float32) / 255
normal = np.asarray(Image.open(os.path.join(SRC, 'LeafSet022_1K-PNG_NormalGL.png')).convert('RGB'), np.float32) / 255
lab, n = ndimage.label(alpha > 0.5)
leaves = []
for sl in ndimage.find_objects(lab):
    if sl[0].stop - sl[0].start < 100:
        continue
    pad = 6
    ys = slice(max(sl[0].start - pad, 0), sl[0].stop + pad); xs = slice(max(sl[1].start - pad, 0), sl[1].stop + pad)
    leaves.append((color[ys, xs], alpha[ys, xs], normal[ys, xs]))
print('leaves', len(leaves), [l[1].shape for l in leaves])
# target colour: linear mean of the leaves -> dark green, keep each leaf's relative detail
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)
mean = np.mean([lin(c)[a > 0.5].mean(0) for c, a, _ in leaves], 0)
TARGET = lin(np.array([36, 84, 32]) / 255.0)          # albedo; the sun-lit canopy then reads like the sprite
print('source mean linear', mean.round(4), 'target', TARGET.round(4))

CELL = 512


def rotate_rgba(img, angle, order=1):
    return ndimage.rotate(img, angle, reshape=True, order=order, mode='constant', cval=0.0)


def cluster(seed):
    r = np.random.default_rng(seed)
    acc_c = np.zeros((CELL, CELL, 3), np.float32); acc_a = np.zeros((CELL, CELL), np.float32)
    acc_n = np.zeros((CELL, CELL, 3), np.float32); acc_n[...] = (0.5, 0.5, 1.0)
    # twig: a slightly curved line from the bottom centre up into the cluster
    twig = []
    x0, y0 = CELL * 0.5 + r.uniform(-20, 20), CELL * 0.98
    ang = -math.pi / 2 + r.uniform(-0.3, 0.3)
    for i in range(34):
        twig.append((x0, y0)); x0 += math.cos(ang) * 5; y0 += math.sin(ang) * 5; ang += r.uniform(-0.04, 0.04)
    yy, xx = np.mgrid[:CELL, :CELL]
    for i, (tx, ty) in enumerate(twig):
        w = 5.5 * (1 - i / len(twig)) + 1.5
        m = (xx - tx) ** 2 + (yy - ty) ** 2 < w * w
        acc_c[m] = (0.20, 0.12, 0.07); acc_a[m] = 1
    count = 230
    order = r.permutation(count)
    for k in order:
        # round spray: leaf stems point back toward the cluster centre, leaves fill a disc
        rad = CELL * 0.33 * math.sqrt(r.uniform(0.0, 1.0)); phi = r.uniform(0, 2 * math.pi)
        bx, by = CELL * 0.5 + rad * math.cos(phi), CELL * 0.47 + rad * math.sin(phi)
        t = rad / (CELL * 0.33)
        c, a, nm = leaves[r.integers(len(leaves))]
        s = r.uniform(0.12, 0.18)
        hgt = int(c.shape[0] * s); wid = int(c.shape[1] * s)
        c = np.asarray(Image.fromarray((c * 255).astype(np.uint8)).resize((wid, hgt), Image.LANCZOS), np.float32) / 255
        a = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((wid, hgt), Image.LANCZOS), np.float32) / 255
        nm = np.asarray(Image.fromarray((nm * 255).astype(np.uint8)).resize((wid, hgt), Image.LANCZOS), np.float32) / 255
        # image up = leaf tip; point it away from the centre (screen angle phi), +-35 degrees
        angle = -math.degrees(phi) - 90 + r.uniform(-50, 50)
        if k % 4 == 0:                                   # centre filler: any direction, stem off-centre
            angle = r.uniform(-180, 180); a_ = math.radians(-angle - 90) + math.pi
            bx, by = CELL * 0.5 + r.uniform(0, 90) * math.cos(a_ + r.uniform(-1, 1)), CELL * 0.47 + r.uniform(0, 90) * math.sin(a_ + r.uniform(-1, 1))
        # leaf image: stem at the bottom. Rotate about the stem end: pad so the stem sits at the centre.
        H = c.shape[0]
        padimg = lambda img: np.concatenate([img, np.zeros((H,) + img.shape[1:], img.dtype)], 0)
        cR = rotate_rgba(padimg(c), angle); aR = rotate_rgba(padimg(a), angle)
        nP = padimg(nm - 0.5); nR = rotate_rgba(nP, angle)
        th = math.radians(angle)                                      # rotate the tangent-space xy (image y is down)
        nx, ny = nR[..., 0], -nR[..., 1]
        rx = nx * math.cos(th) - ny * math.sin(th); ry = nx * math.sin(th) + ny * math.cos(th)
        nR = np.stack([rx, -ry, nR[..., 2]], -1) + 0.5
        # colour: remap to the target green with per-leaf hue/value jitter
        cl = lin(np.clip(cR, 0, 1)) / mean * TARGET * r.uniform(0.75, 1.25)
        cl *= np.array([r.uniform(0.85, 1.15), 1.0, r.uniform(0.8, 1.1)])
        cl *= 1 - 0.25 * (1 - t) * r.random()                         # leaves near the twig base a bit darker
        cS = srgb(cl)
        hh, ww = aR.shape
        ox, oy = int(bx - ww / 2), int(by - hh / 2)
        x0_, y0_ = max(ox, 0), max(oy, 0); x1_, y1_ = min(ox + ww, CELL), min(oy + hh, CELL)
        # whole leaf inside the cell (no cut edges); trim the empty padding first
        ys_, xs_ = np.nonzero(aR > 0.05)
        if ys_.size == 0 or oy + ys_.min() < 8 or ox + xs_.min() < 8 or oy + ys_.max() >= CELL - 8 or ox + xs_.max() >= CELL - 8:
            continue
        sub = (slice(y0_ - oy, y1_ - oy), slice(x0_ - ox, x1_ - ox))
        av = np.clip(aR[sub], 0, 1)[..., None]
        acc_c[y0_:y1_, x0_:x1_] = acc_c[y0_:y1_, x0_:x1_] * (1 - av) + cS[sub] * av
        acc_n[y0_:y1_, x0_:x1_] = acc_n[y0_:y1_, x0_:x1_] * (1 - av) + nR[sub] * av
        acc_a[y0_:y1_, x0_:x1_] = np.maximum(acc_a[y0_:y1_, x0_:x1_], av[..., 0])
    # keep everything off the cell border (mip bleed between cells)
    border = np.zeros_like(acc_a); border[6:-6, 6:-6] = 1
    acc_a *= border
    return acc_c, acc_a, acc_n


cells = [cluster(101), cluster(202)]
base = np.zeros((1024, 1024, 4), np.float32); nrm = np.zeros((1024, 1024, 3), np.float32); nrm[...] = (0.5, 0.5, 1.0)
for row, shade in ((0, 1.0), (1, 0.35)):
    for col, (c, a, nm) in enumerate(cells):
        cs = srgb(lin(np.clip(c, 0, 1)) * shade)
        base[row * CELL:(row + 1) * CELL, col * CELL:(col + 1) * CELL, :3] = cs
        base[row * CELL:(row + 1) * CELL, col * CELL:(col + 1) * CELL, 3] = a
        nrm[row * CELL:(row + 1) * CELL, col * CELL:(col + 1) * CELL] = nm
# dilate RGB into transparent texels (nearest opaque colour), normals likewise
inside = base[..., 3] > 0.5
idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
base[..., :3] = base[..., :3][idx[0], idx[1]]
nrm = np.where(inside[..., None], nrm, nrm[idx[0], idx[1]])
Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'leaves_basecolor.png'))
Image.fromarray((np.clip(nrm, 0, 1) * 255).astype(np.uint8), 'RGB').save(os.path.join(OUT, 'leaves_normal.png'))
cov = [float(base[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL, 3].mean()) for r in range(2) for c in range(2)]
print('ATLAS coverage per cell', [round(x, 2) for x in cov])
