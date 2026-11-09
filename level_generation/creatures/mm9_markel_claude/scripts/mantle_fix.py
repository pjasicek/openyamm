#!/usr/bin/env python3
"""Fur mantle under the old hair tail (mm9_markel, hair reshape 2026-11-02): hair_reshape.py cut the hair shell to the nape, which
exposed the body paint behind the neck where Meshy had painted the hanging hair and its shadow onto the fur mantle (a brown patch
with streaks, review/hair_r1.png). Body texels behind the neck (glTF bind: 1.36 < y < 1.66 m, z < 0.03, |x| < 0.16) that are
hair-coloured (saturated warm, or dark), in patches on fur islands, are refilled by reflecting the clean fur of the same chart
across the patch's bounding-box edge (the strands continue across it), feathered 5 px. Runs on
textures/mk_tp_basecolor_graded.png in place after sleeve_paint_fix.py (the graded original is work/mk_tp_basecolor_graded_orig.png).
Usage (project folder): mantle_fix.py"""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from pygltflib import GLTF2
T = 'textures/mk_tp_basecolor_graded.png'
img = np.asarray(Image.open(T).convert('RGB')).astype(np.float64) / 255
N = img.shape[0]
g = GLTF2().load('work/mk_body_tex.glb'); blob = g.binary_blob()
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a.type]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}[a.componentType]
    return np.frombuffer(blob, dtype=dt, count=a.count * n, offset=(bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)
prim = next(p for m in g.meshes for p in m.primitives if not g.materials[p.material].name.startswith('MarkelHead'))
P = acc(prim.attributes.POSITION).astype(np.float64); UV = acc(prim.attributes.TEXCOORD_0).astype(np.float64)
I = acc(prim.indices).reshape(-1, 3).astype(np.int64)
pos = np.full((N, N, 3), np.nan)
cen = P[I].mean(1)
for f in np.where((cen[:, 1] > 1.30) & (cen[:, 2] < 0.08) & (np.abs(cen[:, 0]) < 0.25))[0]:
    tri = I[f]; uv = UV[tri] * N
    x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0 - 1, 0), min(x1 + 1, N)), np.arange(max(y0 - 1, 0), min(y1 + 1, N)))
    q = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
    a, b, c = uv; m = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
    if xs.size == 0 or abs(np.linalg.det(m)) < 1e-12:
        continue
    l = np.linalg.solve(m, (q - a).T).T; w = np.column_stack([1 - l.sum(1), l]); ok = (w >= -0.03).all(1)
    pos[q[ok, 1].astype(int), q[ok, 0].astype(int)] = w[ok] @ P[tri]
cov = ~np.isnan(pos[..., 0]); X, Y, Z = (np.nan_to_num(pos[..., k]) for k in range(3))
zone = cov & (Y > 1.36) & (Y < 1.66) & (Z < 0.03) & (np.abs(X) < 0.16)
mx, mn = img.max(2), img.min(2); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
lum = img @ np.array([0.299, 0.587, 0.114])
def smooth(x, lo, hi):
    t = np.clip((x - lo) / (hi - lo), 0, 1); return t * t * (3 - 2 * t)
# the patch = body texels within REACH of the old hair tail (the head primitive of the pre-reshape runtime GLB, kept in
# work/rollback_r2/mm9_mk.glb; that file is mirrored to true handedness, so x is flipped back): Meshy painted the tail's colour
# and its contact shadow there, partly as a grey smudge that no colour test catches
from scipy.spatial import cKDTree
REACH = 0.022
go = GLTF2().load('work/rollback_r2/mm9_mk.glb'); bo = go.binary_blob()
def acc_o(i):
    a_ = go.accessors[i]; bv = go.bufferViews[a_.bufferView]
    return np.frombuffer(bo, dtype=np.float32, count=a_.count * 3, offset=(bv.byteOffset or 0) + (a_.byteOffset or 0)).reshape(a_.count, 3)
mesh0 = next(m for m in go.meshes if 'LOD' not in (m.name or '') and 'Shadow' not in (m.name or ''))
ph = next(p_ for p_ in mesh0.primitives if go.materials[p_.material].name.startswith('MarkelHead'))
OP = acc_o(ph.attributes.POSITION).astype(np.float64) * np.array([-1.0, 1, 1])
tail = OP[(OP[:, 1] < 1.62) & (OP[:, 2] < -0.03) & (OP[:, 1] > 1.2)]
d_, _ = cKDTree(tail).query(pos[zone]) if len(tail) else (np.full(zone.sum(), 9.0), None)
near = np.zeros_like(zone); near[zone] = d_ < REACH
pm = ndi.binary_fill_holes(ndi.binary_closing(ndi.binary_dilation(near, iterations=3), iterations=10)) & cov
pm |= ndi.binary_dilation(pm, iterations=25) & ((sat > 0.45) | (lum < 0.38)) & zone     # the brown rim of the same smudge
pm = ndi.binary_closing(pm, iterations=3) & cov
isl, _ = ndi.label(cov)
clean = ~pm & ~((sat > 0.62) | (lum < 0.22))      # gutters too: they hold padded copies of the fur beside them     # any fur of the chart (its dark strand crevices included), not hair-brown
# fill column by column: each patch texel takes the texel mirrored about the patch's top edge in its column (the clean fur above
# it in the same chart, strands continuing across the edge); where that is not clean fur of the same island, the nearest clean
# texel. (A luminance-ramp recolour came out flat grey-beige: review/hair_r2.png)
out = img.copy()
_, (iy2, ix2) = ndi.distance_transform_edt(~clean, return_indices=True)
nfill = nref = 0
for c_ in np.unique(np.where(pm)[1]):
    rows = np.where(pm[:, c_])[0]
    # runs of consecutive rows
    splits = np.where(np.diff(rows) > 1)[0] + 1
    for run in np.split(rows, splits):
        top = run.min()
        for r_ in run:
            k_ = r_ - top
            for sr_ in (top - 1 - k_, top - 1 - (k_ % 70), top - 1 - (k_ % 35)):   # mirror, then ping-pong over a shorter strip
                if 0 <= sr_ < N and clean[sr_, c_]:     # any clean fur above (the fur continues across this chart seam)
                    out[r_, c_] = img[sr_, c_]; nref += 1
                    break
            else:
                out[r_, c_] = img[iy2[r_, c_], ix2[r_, c_]]; nfill += 1
al = np.clip(ndi.distance_transform_edt(pm) / 5.0, 0, 1)
out = img * (1 - al[..., None]) + out * al[..., None]
patch_all = pm
print('MANTLE_FIX tail verts', len(tail), 'patch texels', int(pm.sum()), 'reflected', nref, 'nearest', nfill)
mem = patch_all.astype(float)
dist, (iy, ix) = ndi.distance_transform_edt(~cov, return_indices=True)
gut = (~cov) & (dist <= 4) & (mem[iy, ix] > 0.05)
out[gut] = out[iy[gut], ix[gut]]
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(T)
vis = (img * 255).astype(np.uint8).copy(); vis[mem > 0.5] = (255, 0, 255)
Image.fromarray(vis).resize((1024, 1024), Image.NEAREST).save('review/mantle_fix_mask.png')
print('MANTLE_FIX texels', int(patch_all.sum()), 'zone', int(zone.sum()))
