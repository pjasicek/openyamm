#!/usr/bin/env python3
"""Targeted fixes of the Meshy face paint, by position on the mesh (texel -> bind position raster of the face skin): (1) Meshy's dark
midline marks under the lower lip and on the chin (a goatee-like stroke, seen in the viewer close-up r1-r3) take the skin of the
same height 1.2-2.4 cm either side of the midline, faded in over |x| 0.6-1.2 cm; (2) the forehead in the fringe's V (paler than the
cheeks: it read as a pale band) is toned to the cheek skin's mean; (3) the nostril blobs lifted 35 %. Args: <in head colour 2K> <out png>"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
IN, OUT = sys.argv[1:3]
D = np.load('work/uv_dump.npz'); co, tri, uvc, mat, part = D['co'], D['tri'], D['uvc'], D['mat'], D['part']
S = 2048
sel = np.nonzero((mat == 1) & np.isin(part, (20, 22)))[0]
P3 = np.zeros((S, S, 3), np.float32); N3 = np.zeros((S, S, 3), np.float32); PART = np.zeros((S, S), np.uint8)
for f in sel:
    uv = uvc[f] * [S, S]; uv[:, 1] = S - uv[:, 1]
    x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, S - 1), min(y1, S - 1)
    if x1 < x0 or y1 < y0: continue
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a, b, c = uv
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-12: continue
    l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
    l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
    l3 = 1 - l1 - l2
    m = (l1 >= -0.02) & (l2 >= -0.02) & (l3 >= -0.02)
    if not m.any(): continue
    v = co[tri[f]]
    p = l1[m, None] * v[0] + l2[m, None] * v[1] + l3[m, None] * v[2]
    n = np.cross(v[1] - v[0], v[2] - v[0]); n /= max(np.linalg.norm(n), 1e-12)
    yy, xx = np.nonzero(m); yy += y0; xx += x0
    P3[yy, xx] = p; N3[yy, xx] = n; PART[yy, xx] = part[f]
src = np.asarray(Image.open(IN).convert('RGB'), np.float32) / 255
out = src.copy()
cov = (PART == 20) & (N3[..., 1] < -0.2)
def sst(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
X, Y, Z = P3[..., 0], P3[..., 1], P3[..., 2]
# (1) chin and under-lip midline
zb = np.round(Z / 0.002).astype(int)
m_src = cov & (np.abs(X) > 0.012) & (np.abs(X) < 0.024) & (Z > 0.675) & (Z < 0.712)
ref = {}
for k in np.unique(zb[m_src]): ref[k] = src[m_src & (zb == k)].mean(0)
m_dst = cov & (np.abs(X) < 0.014) & (Z > 0.674) & (Z < 0.709)
w1 = (1 - sst(np.abs(X), 0.006, 0.012)) * sst(Z, 0.674, 0.68) * (1 - sst(Z, 0.704, 0.709))
n1 = 0
for yy, xx in zip(*np.nonzero(m_dst)):
    k = zb[yy, xx]
    r = ref.get(k, ref.get(k + 1, ref.get(k - 1)))
    if r is None: continue
    w = w1[yy, xx]; out[yy, xx] = src[yy, xx] * (1 - w) + r * w; n1 += 1
# (2) forehead in the fringe's V toned to the cheeks
cheek = cov & (np.abs(X) > 0.025) & (np.abs(X) < 0.045) & (Z > 0.72) & (Z < 0.755)
fore = cov & (Z > 0.79) & (Z < 0.845) & (np.abs(X) < 0.03) & (N3[..., 1] < -0.6) & (src.mean(-1) > 0.35)
g = np.clip(src[cheek].mean(0) / np.maximum(src[fore].mean(0), 1e-3), 0.8, 1.1)
w2 = sst(Z, 0.785, 0.80)[..., None] * fore[..., None]
out = out * (1 - w2) + np.clip(out * g, 0, 1) * w2
# (3) nostrils
nos = cov & (np.abs(X) < 0.016) & (Z > 0.731) & (Z < 0.746)
dark = 1 - sst(src.mean(-1), 0.15, 0.4)
w3 = (nos * dark * 0.35)[..., None]
out = out * (1 - w3) + np.clip(out * 1.6, 0, 1) * w3
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype('u1')).save(OUT)
print('FACEFIX chin texels', n1, 'forehead gain', np.round(g, 3).tolist(), 'forehead texels', int(fore.sum()), 'nostril texels', int(nos.sum()))
