#!/usr/bin/env python3
"""Inflate a flat weapon painting (RGBA side view, tip up) into a closed relief mesh.

Silhouette: the alpha 0.5 iso-points on a pixel grid plus interior grid points, Delaunay-triangulated and kept where
the triangle lies inside the silhouette. Thickness: per row, the span a pixel lies in gives a radius R; narrow parts
(R <= round_max) get a round cross-section sqrt(d (2R - d)), wider parts (blades, guards) a plate profile capped at
plate_max, with a smooth blend between. Front surface +t, back surface -t, sealed at the silhouette (t = 0).
UV = the painting (front) and its mirror (back). Glow pixels (hot, saturated) are flagged per triangle.

Usage: weapon_relief.py <painting.png> <out.npz> --length METRES [--step PX] [--round-max M] [--plate-max M]
       [--glow-hue LO,HI] [--crop x0,y0,x1,y1]
The mesh is in metres: x across the painting, y along it (tip +y), z thickness; origin at the bottom centre."""
import argparse
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import Delaunay

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('out')
ap.add_argument('--length', type=float, required=True)
ap.add_argument('--step', type=int, default=4)
ap.add_argument('--round-max', type=float, default=0.022)
ap.add_argument('--plate-max', type=float, default=0.006)
ap.add_argument('--plate-slope', type=float, default=0.35)
ap.add_argument('--glow-sat', type=float, default=0.55)
ap.add_argument('--glow-val', type=float, default=0.80)
ap.add_argument('--alpha', type=float, default=0.5)
a = ap.parse_args()

im = Image.open(a.src).convert('RGBA')
rgba = np.asarray(im).astype(np.float32) / 255
alpha = rgba[..., 3]
H, W = alpha.shape
inside = alpha > a.alpha
# keep the largest component only
lab, n = ndimage.label(inside)
if n > 1:
    sizes = ndimage.sum(inside, lab, range(1, n + 1))
    inside = lab == (1 + int(np.argmax(sizes)))
    alpha = np.where(inside | (ndimage.binary_dilation(inside, iterations=2) & (alpha > 0)), alpha, 0)
ys, xs = np.nonzero(inside)
top, bottom = ys.min(), ys.max()
px = a.length / (bottom - top + 1)          # metres per pixel
cx = (xs.min() + xs.max()) / 2

d = ndimage.distance_transform_edt(inside) * px      # distance to the silhouette (m)
# Row-span radius: half-width of the run each pixel belongs to.
R = np.zeros_like(d)
for y in range(H):
    row = inside[y]
    if not row.any():
        continue
    edges = np.flatnonzero(np.diff(np.concatenate([[0], row.astype(np.int8), [0]])))
    for s, e in zip(edges[::2], edges[1::2]):
        R[y, s:e] = (e - s) * px / 2
R = np.maximum(R, d)
R = ndimage.grey_closing(R, size=(5, 1))             # bridge single-row notches
roundness = np.sqrt(np.clip(d * (2 * R - d), 0, None))
plate = np.minimum(d * a.plate_slope, a.plate_max)
blend = np.clip((R - a.round_max) / a.round_max, 0, 1)
blend = blend * blend * (3 - 2 * blend)
thick = (1 - blend) * np.minimum(roundness, a.round_max) + blend * np.maximum(plate, np.minimum(roundness, a.plate_max))
thick = ndimage.gaussian_filter(thick, 1.0) * inside


def sample(field, x, y):
    return ndimage.map_coordinates(field, [y, x], order=1, mode='nearest')


# Points: interior grid + iso-points on grid edges.
s = a.step
gy, gx = np.mgrid[0:H:s, 0:W:s]
gx = gx.ravel().astype(float); gy = gy.ravel().astype(float)
keep = sample(inside.astype(float), gx, gy) > 0.99
interior = np.stack([gx[keep], gy[keep]], 1)
iso = []
al = ndimage.gaussian_filter(np.where(inside, alpha, 0).astype(float), 0.6)
for y in range(0, H, 1):
    r = al[y] - a.alpha
    c = np.flatnonzero(np.sign(r[:-1]) != np.sign(r[1:]))
    for x in c:
        t = r[x] / (r[x] - r[x + 1]); iso.append((x + t, y))
for x in range(0, W, 1):
    r = al[:, x] - a.alpha
    c = np.flatnonzero(np.sign(r[:-1]) != np.sign(r[1:]))
    for y in c:
        t = r[y] / (r[y] - r[y + 1]); iso.append((x, y + t))
iso = np.array(iso)
# thin the iso-points to about the grid step
order = np.lexsort((iso[:, 0], iso[:, 1]))
iso = iso[order]
kept = []
tree_pts = []
from scipy.spatial import cKDTree
tree = cKDTree(iso)
taken = np.zeros(len(iso), bool)
for i in range(len(iso)):
    if taken[i]:
        continue
    kept.append(i)
    for j in tree.query_ball_point(iso[i], s * 0.45):
        taken[j] = True
iso = iso[kept]
# drop interior points too close to the boundary
ti = cKDTree(iso)
dist, _ = ti.query(interior)
interior = interior[dist > s * 0.5]
pts = np.concatenate([iso, interior])
nb = len(iso)
tri = Delaunay(pts).simplices
P = pts[tri]
cent = P.mean(1)
mids = (P + np.roll(P, 1, axis=1)) / 2
ok = sample(al, cent[:, 0], cent[:, 1]) > a.alpha
for k in range(3):
    ok &= sample(al, mids[:, k, 0], mids[:, k, 1]) > a.alpha * 0.6
tri = tri[ok]
# remove unreferenced points
used = np.unique(tri)
remap = -np.ones(len(pts), int); remap[used] = np.arange(len(used))
pts = pts[used]; tri = remap[tri]
is_b = used < nb
t = sample(thick, pts[:, 0], pts[:, 1])
t[is_b] = 0.0
X = (pts[:, 0] - cx) * px
Y = (bottom - pts[:, 1]) * px
U = pts[:, 0] / W
V = 1 - pts[:, 1] / H
# Front (z = +t) and back (z = -t); boundary vertices shared.
nv = len(pts)
back_index = np.where(is_b, np.arange(nv), nv + np.cumsum(~is_b) - 1)
vb = ~is_b
verts = np.concatenate([np.stack([X, Y, t], 1), np.stack([X[vb], Y[vb], -t[vb]], 1)])
uvs = np.concatenate([np.stack([U, V], 1), np.stack([U[vb], V[vb]], 1)])
front = tri[:, [0, 1, 2]]
# orient front faces toward +z
p = verts[front]
nz = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])[:, 2]
front[nz < 0] = front[nz < 0][:, [0, 2, 1]]
back = back_index[front][:, [0, 2, 1]]
faces = np.concatenate([front, back])
# Glow flag from the painting colour (bright, saturated) under each face.
rgb = rgba[..., :3]
mx = rgb.max(-1); mn = rgb.min(-1)
sat = (mx - mn) / np.maximum(mx, 1e-6)
glow_px = (mx > a.glow_val) & (sat > a.glow_sat) & inside
glow_px = ndimage.binary_opening(glow_px, iterations=1)
cuv = uvs[faces].mean(1)
glow = sample(glow_px.astype(float), cuv[:, 0] * W, (1 - cuv[:, 1]) * H) > 0.5
np.savez(a.out, verts=verts.astype(np.float32), uvs=uvs.astype(np.float32), faces=faces.astype(np.int32),
         glow=glow, px=px, size=(W, H), bottom=bottom, cx=cx)
print(f'{a.src}: {len(verts)} verts, {len(faces)} tris, glow {glow.mean():.2f}, '
      f'max half-thickness {t.max()*100:.2f} cm, px {px*1000:.2f} mm, width {(X.max()-X.min())*100:.1f} cm')
