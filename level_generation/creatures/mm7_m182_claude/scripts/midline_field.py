"""Midline field c(y, z) of the rest mesh (v2 symmetry pass, system Python).

Meshy built the three-quarter master's lean into the trunk, neck and head: cross-sections are shifted and sheared
off x = 0 by up to ~3 cm (README "v2"). Rays along +X on a 2 mm (y, z) grid give the solid's x-intervals; the
interval nearest the previous estimate is the body (neck, head, trunk or tail) at that row, and its midpoint is the
local mirror plane. Rows where a limb merges with the body (interval much wider than its neighbours) are rejected,
then c is median-filtered, filled by nearest valid row and Gaussian-smoothed (sigma 12 mm).
Usage: midline_field.py <mesh.npz> <out.npz> <preview.png>"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
d = np.load(sys.argv[1]); co = d['co']; T = d['tris']; part = d['part']
STEP = .002
ys = np.arange(-.44, .50, STEP); zs = np.arange(0., .67, STEP)
hits = [[[] for _ in zs] for _ in ys]
ax = np.abs(co[:, 0])
# body triangles only: main shell, not the wings (wing domain of the v1 rig) or crest shells
wing = (ax > .085) & (co[:, 2] > .255) & (co[:, 1] > -.33) & (co[:, 1] < -.08)
keep = (part[T] == 0).all(1) & ~wing[T].any(1)
for t in T[keep]:
    p = co[t]; a, b, c = p[:, 1:]
    lo = np.floor((np.minimum(np.minimum(a, b), c) - [ys[0], zs[0]]) / STEP).astype(int) + 1
    hi = np.floor((np.maximum(np.maximum(a, b), c) - [ys[0], zs[0]]) / STEP).astype(int)
    if (hi < lo).any(): continue
    gy, gz = np.meshgrid(ys[lo[0]:hi[0] + 1], zs[lo[1]:hi[1] + 1], indexing='ij')
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-14: continue
    w0 = ((b[1] - c[1]) * (gy - c[0]) + (c[0] - b[0]) * (gz - c[1])) / den
    w1 = ((c[1] - a[1]) * (gy - c[0]) + (a[0] - c[0]) * (gz - c[1])) / den
    w2 = 1 - w0 - w1; m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
    xs = w0 * p[0, 0] + w1 * p[1, 0] + w2 * p[2, 0]
    for i, j, xv in zip(*np.nonzero(m), xs[m]):
        hits[lo[0] + i][lo[1] + j].append(float(xv))
C = np.full((len(ys), len(zs)), np.nan); Wd = np.full_like(C, np.nan)
for i in range(len(ys)):
    for j in range(len(zs)):
        h = sorted(hits[i][j])
        if len(h) < 2: continue
        iv = [(h[k], h[k + 1]) for k in range(0, len(h) - 1, 2)]
        iv = [q for q in iv if q[1] - q[0] > .003 and q[0] < .03 and q[1] > -.03 and abs(q[0] + q[1]) / 2 < .035]
        if not iv: continue
        best = min(iv, key=lambda q: abs((q[0] + q[1]) / 2) - .3 * (q[1] - q[0]))
        C[i, j] = (best[0] + best[1]) / 2; Wd[i, j] = best[1] - best[0]
valid = np.isfinite(C)
# reject rows whose width exceeds 1.35x the local median width (a limb merged with the body)
wmed = ndimage.generic_filter(np.where(valid, Wd, np.nan), np.nanmedian, size=9, mode='nearest')
valid &= (Wd < 1.35 * wmed) & (np.abs(C) < .035)
Cm = np.where(valid, C, np.nan)
Cm = ndimage.generic_filter(Cm, np.nanmedian, size=7, mode='nearest'); valid2 = np.isfinite(Cm)
idx = ndimage.distance_transform_edt(~valid2, return_distances=False, return_indices=True)
filled = Cm[tuple(idx)]
sig = .012 / STEP
num = ndimage.gaussian_filter(np.where(valid2, Cm, 0), sig); den = ndimage.gaussian_filter(valid2.astype(float), sig)
smooth = np.where(den > .05, num / np.maximum(den, 1e-6), filled)
smooth = ndimage.gaussian_filter(smooth, 4)
np.savez(sys.argv[2], ys=ys, zs=zs, c=smooth, raw=C, valid=valid)
img = np.clip((smooth.T[::-1] / .03) * .5 + .5, 0, 1); rgb = np.stack([img, 1 - np.abs(img - .5) * 2, 1 - img], -1)
rgb[~valid.T[::-1]] *= .55
Image.fromarray(np.uint8(rgb * 255)).resize((len(ys) * 2, len(zs) * 2), Image.NEAREST).save(sys.argv[3])
print('FIELD valid rows', int(valid.sum()), 'c range mm', np.round(np.nanpercentile(C[valid], [1, 50, 99]) * 1000, 1))
