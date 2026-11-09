#!/usr/bin/env python3
"""Scimitar mesh from the HD master's alpha (references_prop/scimitar_flat.png): a pillowed plate, the silhouette at z = 0 and
each interior point lifted by its distance from the outline, by zone: thin lens for the blade, round for the grip, flat bars
for the guard and pommel. One side mirrored for the other; both sample the same image. Writes work/scimitar_mesh.npz (verts in
px with z in px, faces, uv) and textures/skelwar_scimitar_basecolor.png (padded, 1K wide crop). Args: none (project folder)."""
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import Delaunay
im = Image.open('references_prop/scimitar_flat.png').convert('RGBA')
W, H = im.size
a = np.asarray(im, np.float32)
mask = a[..., 3] > 128
mask = ndimage.binary_opening(mask, iterations=1)
lab, n = ndimage.label(mask); sizes = ndimage.sum(mask, lab, range(1, n + 1)); mask = lab == (1 + int(np.argmax(sizes)))
mask = ndimage.binary_fill_holes(mask)
d = ndimage.distance_transform_edt(mask)
# contour by walking the boundary (Moore)
ys, xs = np.where(mask)
start = (ys[np.argmin(xs)], xs.min())
dirs = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]
path = [start]; cur = start; k = 0
for _ in range(100000):
    for i in range(8):
        j = (k + i) % 8; p = (cur[0] + dirs[j][0], cur[1] + dirs[j][1])
        if 0 <= p[0] < H and 0 <= p[1] < W and mask[p]:
            cur = p; k = (j + 6) % 8; break
    path.append(cur)
    if cur == start and len(path) > 10: break
path = np.array(path[:-1], float)[:, ::-1]


def dp(pts, eps):
    keep = np.zeros(len(pts), bool); keep[0] = keep[-1] = True; st = [(0, len(pts) - 1)]
    while st:
        a_, b_ = st.pop()
        if b_ <= a_ + 1: continue
        p, q = pts[a_], pts[b_]; dv = q - p; L = np.linalg.norm(dv) + 1e-9
        t = np.abs((pts[a_ + 1:b_, 0] - p[0]) * dv[1] - (pts[a_ + 1:b_, 1] - p[1]) * dv[0]) / L
        m = int(np.argmax(t))
        if t[m] > eps:
            m += a_ + 1; keep[m] = True; st += [(a_, m), (m, b_)]
    return pts[keep]


n = len(path); half = n // 2
c = np.vstack([dp(path[:half + 1], 1.6)[:-1], dp(path[half:], 1.6)[:-1]])
print('contour', n, '->', len(c))
HX0, HX1, GX0, GX1 = 118, 345, 340, 470        # grip and guard columns in the master
px_m = 0.82 / (1523 - 21)


def zone(x, y):
    if x < HX0: return 'pommel'
    if x < HX1: return 'grip'
    if x < GX1 and (d[int(y), int(x)] < 34): return 'guard' if x < 425 or y < 500 else 'blade'
    return 'blade'


inner = []
gy, gx = np.mgrid[0:H:6, 0:W:6]
for y, x in zip(gy.ravel(), gx.ravel()):
    if not mask[y, x] or d[y, x] < 3: continue
    z = zone(x, y)
    # local maximum of the distance (the ridge) in all zones, plus inset rings on the round grip
    win = d[max(0, y - 6):y + 7, max(0, x - 6):x + 7]
    ridge = d[y, x] >= win.max() - 0.75
    if ridge and (x % 36 == 0 or z != 'blade'): inner.append((x, y))
    elif z == 'grip' and abs(d[y, x] - 9) < 1.5 and x % 24 == 0: inner.append((x, y))
inner = np.array(inner, float)
# thin out
keep = []
for p in inner:
    if all(np.linalg.norm(p - q) > (16 if p[0] < GX1 else 30) for q in keep): keep.append(p)
inner = np.array(keep)
pts = np.vstack([c, inner])
tri = Delaunay(pts).simplices
cen = pts[tri].mean(1)
ok = mask[np.clip(cen[:, 1].astype(int), 0, H - 1), np.clip(cen[:, 0].astype(int), 0, W - 1)]
e1 = pts[tri[:, 1]] - pts[tri[:, 0]]; e2 = pts[tri[:, 2]] - pts[tri[:, 0]]
area = np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0])
tri = tri[ok & (area > 1.0)]


def height(p):
    x, y = p; dd = d[int(y), int(x)] if mask[int(y), int(x)] else 0.0
    z = zone(x, y)
    if z == 'grip':
        R = 32.0; return np.sqrt(max(0.0, R ** 2 - max(0.0, R - dd) ** 2))
    hm = {'blade': 0.0042, 'guard': 0.0085, 'pommel': 0.011}[z] / px_m
    return min(hm, dd * (0.32 if z == 'blade' else 0.9))


h = np.array([height(p) for p in pts]); h[:len(c)] = 0
nv = len(pts)
# two shells: the silhouette is a real (hard) edge, and a triangle with three outline corners exists on both sides
V = np.vstack([np.c_[pts, h], np.c_[pts, -h]])
F = np.vstack([tri, tri + nv])
SIDE = np.r_[np.ones(len(tri)), -np.ones(len(tri))]
# orient front faces toward +z in image coordinates (y down)
a0 = V[F[0]]
uv = np.c_[V[:, 0] / W, 1 - V[:, 1] / H]
np.savez('work/scimitar_mesh.npz', v=V, f=F, uv=uv, side=SIDE, px_m=px_m, w=W, h=H)
print('scimitar verts', len(V), 'tris', len(F))
rgb = a[..., :3].astype(np.uint8)
_, (iy, ix) = ndimage.distance_transform_edt(~ndimage.binary_erosion(mask, iterations=1), return_indices=True)
Image.fromarray(rgb[iy, ix]).save('textures/skelwar_scimitar_basecolor.png')
