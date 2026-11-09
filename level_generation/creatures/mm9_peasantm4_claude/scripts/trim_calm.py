#!/usr/bin/env python3
"""PeasantM4 jerkin braid (2026-11-02, close-ups r1): Meshy painted MM9's woven cream-and-brown chevron braid on the jerkin's
neckline and shoulder pieces (Forad's lapel and cap-sleeve strips) as a stark leopard/zebra print. Body texels on the upper
torso (rest z > ZMIN) whose 7 px luminance spread is high and that hold near-black next to near-white within 9 px (the print) and that are not the green jerkin wool, plus a 2 px
dilation, keep their own pattern at CONTRAST x its local deviation round a Gaussian local mean (sigma 6 px) pulled
toward the braid's mid brown (BRAID, weight TINT): a calm woven band in MM9's colours. Feathered 2 px.
Reads textures/pm4_basecolor_graded_pretrim.png (made on the first run), writes textures/pm4_basecolor_graded.png.
Usage (project folder): trim_calm.py <dump npz> [ZMIN 0.45] [CONTRAST 0.45] [TINT 0.5]"""
import shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
dump = sys.argv[1]
ZMIN = float(sys.argv[2]) if len(sys.argv) > 2 else 0.45
CON = float(sys.argv[3]) if len(sys.argv) > 3 else 0.45
TINT = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
BRAID = np.array([118, 82, 52]) / 255.0
src = Path('textures/pm4_basecolor_graded.png'); bak = Path('textures/pm4_basecolor_graded_pretrim.png')
if not bak.exists(): shutil.copy(src, bak)
img = np.asarray(Image.open(bak).convert('RGB'), np.float64) / 255; N = img.shape[0]
d = np.load(dump, allow_pickle=True)
P, L, ls, lt, U = d['P'], d['L'], d['ls'], d['lt'], d['uv']
zt = np.full((N, N), np.nan)
for f in np.where(~(d['head'].astype(bool) | d['hand'].astype(bool)))[0]:
    li = np.arange(ls[f], ls[f] + lt[f]); xyz = P[L[li]]
    if xyz[:, 2].max() < ZMIN - 0.05: continue
    for k in range(1, lt[f] - 1):
        tri = [li[0], li[k], li[k + 1]]; uv = U[tri] * N; uv[:, 1] = N - uv[:, 1]; z = P[L[tri]][:, 2]
        x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
        xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, N)), np.arange(max(y0, 0), min(y1, N)))
        if xs.size == 0: continue
        a, b, c = uv; m = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
        if abs(np.linalg.det(m)) < 1e-12: continue
        q = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        l = np.linalg.solve(m, (q - a).T).T; w = np.column_stack([1 - l.sum(1), l]); ok = (w >= -0.02).all(1)
        zt[q[ok, 1].astype(int), q[ok, 0].astype(int)] = w[ok] @ z
upper = np.nan_to_num(zt, nan=-9) > ZMIN
lum = img @ [0.299, 0.587, 0.114]
spread = np.sqrt(np.maximum(ndi.uniform_filter(lum ** 2, 7) - ndi.uniform_filter(lum, 7) ** 2, 0))
mx, mn = img.max(2), img.min(2); sat = (mx - mn) / np.maximum(mx, 1e-6)
hue = np.degrees(np.arctan2(np.sqrt(3) * (img[..., 1] - img[..., 2]), 2 * img[..., 0] - img[..., 1] - img[..., 2])) % 360
green = (hue > 45) & (hue < 100) & (sat > 0.3)
locmax = ndi.maximum_filter(lum, 9); locmin = ndi.minimum_filter(lum, 9)
# the print: very dark brown next to near-white within 9 px (the cream shirt weave and the green wool never reach both)
cand = upper & (spread > 0.12) & ~green & (locmax > 0.62) & (locmin < 0.2)
cand = ndi.binary_fill_holes(ndi.binary_closing(cand, iterations=4))
cand = ndi.binary_opening(cand, iterations=1)
lab, n = ndi.label(cand); sizes = ndi.sum(cand, lab, range(1, n + 1))
mask = np.isin(lab, 1 + np.where(sizes > 150)[0])
mask = ndi.binary_dilation(mask, iterations=2) & upper & ~green
al = ndi.gaussian_filter(mask.astype(float), 1.2)
mean = np.stack([ndi.gaussian_filter(img[..., k], 6) for k in range(3)], 2)
calm = (mean * (1 - TINT) + BRAID * TINT) + CON * (img - mean)
out = img * (1 - al[..., None]) + np.clip(calm, 0, 1) * al[..., None]
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(src)
Image.fromarray((mask * 255).astype(np.uint8)).save('work/trim_mask.png')
print('TRIM_CALM texels', int(mask.sum()), 'blobs', int((sizes > 150).sum()))
