#!/usr/bin/env python3
"""Repaint the beard-coloured body texels under the beard (user review 2026-11-02, Talk "twists his clothing on the
breast/collarbones"): Meshy painted the beard onto the shirt/vest under it. While those faces carried the beard's
Ponytail1/Head weights they swung with the beard (the twist); with chest weights (body_reweight.py) they stay on the chest and
show when the head turns. Body texels (rest, glTF: height H0..H1, |x| < XM, front z < 0.06) whose colour is beard-like
(seeds: hue 3-26 deg, saturation > 0.7, red > 110; grown 25 px through connected texels of hue < 29, saturation > 0.5:
the dark vest pattern overlaps that hue but is not connected to the patch; the 3D window keeps the beard-hued boots out) become real cloth: each takes the class (linen shirt, blue
collar band, ochre vest) of its nearest clear cloth texels in 3D and is cloned from the purest window of that class on the
atlas (tiled), scaled to the class's local shading (normalised 12 px Gaussian); orange flecks near the patch join it (2026-11-02 review: a blurred fill read as a smudge). Reads textures/pdm4_tp_basecolor_graded_prebeard.png
(first-run backup), writes textures/pdm4_tp_basecolor_graded.png and review/under_beard_mask.png.
Usage (project folder): under_beard_paint.py [export glb work/pdm4_body_tex.glb]"""
import shutil, sys
sys.path.insert(0, 'scripts')
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from headpos import texel_positions
glb = sys.argv[1] if len(sys.argv) > 1 else 'work/pdm4_body_tex.glb'
H0, H1, XM = 0.78, 1.05, 0.18
HUE1 = float(sys.argv[2]) if len(sys.argv) > 2 else 29.0   # beard red-orange 22-25 deg, dark vest 27+, vest 33
f = Path('textures/pdm4_tp_basecolor_graded.png'); bk = f.with_name(f.stem + '_prebeard.png')
if not bk.exists():
    shutil.copyfile(f, bk)
img = np.asarray(Image.open(bk).convert('RGB')).astype(float); N = img.shape[0]
pos, cov = texel_positions(glb, 'PeasantDM4', N)
x, y, z = (np.nan_to_num(pos[..., i], nan=9) for i in range(3))
region = cov & (y > H0) & (y < H1) & (np.abs(x) < XM) & (z < 0.08)
mx = img.max(2); mn = img.min(2); sat = (mx - mn) / np.maximum(mx, 1)
r, g, b = img[..., 0], img[..., 1], img[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
seed = region & (hue > 3) & (hue < 26) & (sat > 0.7) & (r > 110)          # clear beard orange
seed = ndi.binary_opening(seed, iterations=1)
loose = region & (hue < HUE1) & (sat > 0.5) & (r > 60)                       # beard-like (dark vest overlaps)
beard = seed.copy()
for _ in range(25):                                                          # grow only through connected beard-like texels
    beard = ndi.binary_dilation(beard) & (loose | seed)
beard = ndi.binary_closing(beard, iterations=2) & region
beard = ndi.binary_dilation(beard, iterations=2) & cov
beard = beard | (ndi.binary_dilation(beard, iterations=4) & (hue < 30) & (sat > 0.5) & cov & ~ndi.binary_erosion(cov, iterations=3))   # the islands' orange rims
# fill only from clear cloth: the ochre vest (hue 30-50, sat > 0.6), linen (sat < 0.4, bright) or the blue band
# orange flecks next to the patch join it
fleck = region & (hue > 3) & (hue < 27) & (sat > 0.6) & (r > 100) & ndi.binary_dilation(beard, iterations=20)
beard = ndi.binary_dilation(beard | fleck, iterations=1) & cov
# Meshy's featureless paint under the beard (smooth gold, no weave) connected to the patch is cloth to clone too
Lum = img @ [0.2126, 0.7152, 0.0722]
detail = ndi.gaussian_filter(np.abs(Lum - ndi.gaussian_filter(Lum, 2)), 4)
smooth = region & (detail < 4.0) & (hue < 55) & (sat > 0.35)
grow = beard.copy()
for _ in range(40):
    grow = ndi.binary_dilation(grow) & (smooth | beard)
beard = ndi.binary_closing(grow, iterations=2) & cov
# clear cloth classes: 1 linen shirt (low saturation, bright), 2 blue collar band, 3 ochre vest
L = img @ [0.2126, 0.7152, 0.0722]
cls = np.zeros(beard.shape, np.uint8)
cls[(sat < 0.4) & (mx > 120)] = 1
blue = (hue > 190) & (hue < 260) & (sat > 0.3)
cls[ndi.binary_closing(blue, iterations=4) & cov] = 2            # the collar band: navy with its gold knots
cls[(hue > 30) & (hue < 50) & (sat > 0.6)] = 3
cls[~cov | beard] = 0
# each patch texel takes the class of the nearest clear cloth texel IN 3D (UV neighbours can be far away on the body)
from scipy.spatial import cKDTree
src_i = np.nonzero(region & (cls > 0))
tree = cKDTree(pos[src_i])
tgt_i = np.nonzero(beard)
_, nn = tree.query(pos[tgt_i], k=9)
lab = cls[src_i][nn]
tcls = np.array([np.bincount(row, minlength=4)[1:].argmax() + 1 for row in lab])
# exemplars: the most uniform window of each class anywhere on the atlas (real woven/knot texture)
def exemplar(c, wsz):
    # a window wholly inside islands, >= 95 % of the class, with the strongest weave detail (a smooth blob or a gutter
    # streak made a poor clone)
    m = ((cls == c) & cov).astype(float)
    f = ndi.uniform_filter(m, wsz)
    det = ndi.uniform_filter(np.abs(Lum - ndi.gaussian_filter(Lum, 2)), wsz)
    for thr in (0.95, 0.9, 0.8, 0.7):
        score = np.where(f > thr, det, -1.0)
        score[region] = -1
        if (score[wsz:-wsz, wsz:-wsz] > 0).any():
            break
    score[:wsz, :] = -1; score[-wsz:, :] = -1; score[:, :wsz] = -1; score[:, -wsz:] = -1
    score[region] = -1                                  # not from under the beard itself
    cy, cx = np.unravel_index(np.argmax(score), score.shape)
    ex = img[cy - wsz // 2:cy + wsz // 2, cx - wsz // 2:cx + wsz // 2].copy()
    return ex, float(f[cy, cx]), (int(cy), int(cx))
EX = {1: exemplar(1, 48), 2: exemplar(2, 28), 3: exemplar(3, 48)}
# low-frequency target: normalised Gaussian of the same class around (keeps the shading of the neighbourhood)
out = img.copy()
for c in (1, 2, 3):
    ex, frac, at = EX[c]; h, w = ex.shape[:2]; exm = ex.reshape(-1, 3).mean(0)
    sel = tcls == c
    ty, tx = tgt_i[0][sel], tgt_i[1][sel]
    srcm = (cls == c) & region
    den = ndi.gaussian_filter(srcm.astype(float), 12)
    low = np.stack([ndi.gaussian_filter(np.where(srcm, img[..., k], 0), 12) for k in range(3)], -1) / np.maximum(den, 1e-6)[..., None]
    lowc = np.where((den[ty, tx] > 0.02)[:, None], low[ty, tx], exm)
    ry = ty % (2 * h); ry = np.where(ry < h, ry, 2 * h - 1 - ry)   # mirrored tiling: no seams at the tile edges
    rx = tx % (2 * w); rx = np.where(rx < w, rx, 2 * w - 1 - rx)
    tex = ex[ry, rx]
    out[ty, tx] = tex * (lowc / np.maximum(exm, 1))
    print('UNDER_BEARD class', c, 'texels', int(sel.sum()), 'exemplar', at, 'purity', round(frac, 2))
# the UV gutters round the patch (outside every island) still held orange and bled into the mips: pad them from the
# nearest covered texel
gut = ~cov & ndi.binary_dilation(beard, iterations=8)
_, (gy, gx) = ndi.distance_transform_edt(~cov, return_indices=True)
out[gut] = out[gy[gut], gx[gut]]
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(f)
Image.fromarray(np.uint8(beard) * 255).save('review/under_beard_mask.png')
print('UNDER_BEARD texels', int(beard.sum()), 'region', int(region.sum()))
