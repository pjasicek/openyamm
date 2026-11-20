#!/usr/bin/env python3
"""Fringe edge of the head paint (orchestrator lesson 2026-11-01: PeasantM1d and Ebora shipped a pale jagged band where the
fringe meets the brow). Meshy painted forehead skin onto the lower rim of the separate hair shell; on tier B it reads as a
light seam under the fringe and on tier A (hair ramp) as a pale ginger band. Every texel of the hair shell's UV islands
that is skin-coloured (bright, warm, not hair-dark) takes the colour of the nearest hair texel of the same shell.

The hair shell = the loose part of the head primitive (positions welded) with the most faces above the eyes.
Reads work/pm3_body_tex.glb (build_export_v2.py output, head UVs in TEXCOORD_0 of material PeasantM3Head) and the composed
head colour (kept as work/pm3_tp_head_basecolor_composed.png on the first run), writes textures/pm3_tp_head_basecolor.png
and review/fringe_fix_mask_<prefix>.png. Usage (project folder): fringe_fix.py <head set prefix>"""
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from pygltflib import GLTF2

# mm9_peasantm3: one run per head set, in place, inside the chain fix_neck_pm3.py (from the _preneck backups) ->
# fringe_fix.py <prefix> -> hand_clean.py -> pad_head.py; the forehead step only with FOREHEAD=1
import os
PREFIX = sys.argv[1] if len(sys.argv) > 1 else 'pm3_tp'
OUT = Path(f'textures/{PREFIX}_head_basecolor.png')
img = np.asarray(Image.open(OUT).convert('RGB')).astype(np.float64) / 255
N = img.shape[0]

g = GLTF2().load('work/pm3_body_tex.glb')
blob = g.binary_blob()


def acc(i):
    a = g.accessors[i]
    bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a.type]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}[a.componentType]
    return np.frombuffer(blob, dtype=dt, count=a.count * n, offset=(bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)


prim = next(p for m in g.meshes for p in m.primitives if g.materials[p.material].name.startswith('PeasantM3Head'))
P = acc(prim.attributes.POSITION).astype(np.float64)
UV = acc(prim.attributes.TEXCOORD_0).astype(np.float64)
I = acc(prim.indices).reshape(-1, 3).astype(np.int64)
# weld by position, then loose parts
_, weld = np.unique(np.round(P, 5), axis=0, return_inverse=True)
weld = weld.ravel()
F = weld[I]
rows = np.concatenate([F[:, 0], F[:, 1], F[:, 2]])
cols = np.concatenate([F[:, 1], F[:, 2], F[:, 0]])
n = weld.max() + 1
_, lab = connected_components(coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)), directed=False)
face_part = lab[F[:, 0]]
cy = P[I].mean(1)[:, 1]
eye_y = 1.66                                       # glTF y up, metres (eyes at about 1.67 on this body)
parts, counts = np.unique(face_part[cy > eye_y], return_counts=True)
hair_part = parts[np.argmax(counts)]
hair_faces = np.where(face_part == hair_part)[0]
print('FRINGE hair part', int(hair_part), 'faces', len(hair_faces), 'of', len(I))

# rasterise the hair shell's islands
cover = np.zeros((N, N), bool)
for f in hair_faces:
    uv = UV[I[f]] * N
    x0, y0 = np.floor(uv.min(0)).astype(int)
    x1, y1 = np.ceil(uv.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, N)), np.arange(max(y0, 0), min(y1, N)))
    if xs.size == 0:
        continue
    q = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
    a, b, c = uv
    m = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
    if abs(np.linalg.det(m)) < 1e-12:
        continue
    l = np.linalg.solve(m, (q - a).T).T
    ok = (l >= -0.02).all(1) & (l.sum(1) <= 1.02)
    cover[q[ok, 1].astype(int), q[ok, 0].astype(int)] = True
cover = ndi.binary_dilation(cover, iterations=2)    # the islands' gutter texels too (bilinear filtering reads them)

mx, mn = img.max(2), img.min(2)
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
lum = img @ np.array([0.299, 0.587, 0.114])
hair_lum = np.percentile(lum[cover], 60)
skinlike = cover & (lum > max(hair_lum * float(os.environ.get('RIM_K', '1.45')), 0.38)) & (sat < 0.72)   # PeasantM3 B: RIM_K 2.4 (1.45 took the brown highlights)
skinlike = ndi.binary_dilation(skinlike, iterations=1) & cover
hairtex = cover & ~skinlike
idx = ndi.distance_transform_edt(~hairtex, return_distances=False, return_indices=True)
out = img.copy()
out[skinlike] = img[idx[0][skinlike], idx[1][skinlike]]
# soften the patched texels into their surroundings (1 px) so the fill keeps no hard outline
blur = ndi.gaussian_filter(out, (0.8, 0.8, 0))
out[skinlike] = blur[skinlike]
print('FRINGE hair texels', int(cover.sum()), 'repainted', int(skinlike.sum()), 'hair lum p60 %.3f' % hair_lum)
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT)
vis = (img * 255).astype(np.uint8).copy()
vis[skinlike] = (255, 0, 255)
Image.fromarray(vis).resize((1024, 1024), Image.NEAREST).save('review/fringe_fix_mask_' + PREFIX + '.png')

if os.environ.get('FOREHEAD') != '1':
    sys.exit(0)
# ---- second step (v1.8): the forehead band of the FACE shell under the fringe. Meshy painted a dark-grey receding hairline
# there; under the hair shell's zigzag edge it read as a grey jagged band (tier B) and took a pale ginger rim from the hair
# ramp (tier A). Face-shell texels on the front of the head above the brows that are not skin-coloured take the colour of
# the nearest skin texel of that shell, so the fringe edge meets clean forehead skin.
face_faces = np.where(face_part != hair_part)[0]
fpos = np.full((N, N, 3), np.nan)
for f in face_faces:
    tri = I[f]
    uv = UV[tri] * N
    x0, y0 = np.floor(uv.min(0)).astype(int)
    x1, y1 = np.ceil(uv.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, N)), np.arange(max(y0, 0), min(y1, N)))
    if xs.size == 0:
        continue
    q = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
    a, b, c = uv
    m = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
    if abs(np.linalg.det(m)) < 1e-12:
        continue
    l = np.linalg.solve(m, (q - a).T).T
    w = np.column_stack([1 - l.sum(1), l])
    ok = (w >= -0.02).all(1)
    fpos[q[ok, 1].astype(int), q[ok, 0].astype(int)] = w[ok] @ P[tri]
fcov = ~np.isnan(fpos[..., 0])
fy, fz = np.nan_to_num(fpos[..., 1]), np.nan_to_num(fpos[..., 2])
headz = np.median(P[I[hair_faces]].reshape(-1, 3)[:, 2])
img2 = out
mx2, mn2 = img2.max(2), img2.min(2)
sat2 = np.where(mx2 > 0, (mx2 - mn2) / np.maximum(mx2, 1e-6), 0)
lum2 = img2 @ np.array([0.299, 0.587, 0.114])
fore = fcov & (fy > 1.705) & (fz > headz + 0.03)
skin_ref = fcov & (fy > 1.66) & (fy < 1.72) & (fz > headz + 0.06) & (sat2 > 0.28) & (lum2 > 0.45)
sk_lum = np.median(lum2[skin_ref])
notskin = fore & ((lum2 < sk_lum * 0.90) | (sat2 < 0.24))
notskin = ndi.binary_dilation(notskin, iterations=6) & fore     # swallow the hair wisps and pale rim of the old hairline
# fill (v1.10): the surrounding forehead skin extended smoothly into the band by normalised convolution at growing radii
# (a flat median patch read lighter than the shaded skin beside it; a nearest-texel fill streaked), plus that skin's grain;
# feathered over 6 texels so the band's edge leaves no line
known = (fcov & ~notskin & (sat2 > 0.24) & (lum2 > sk_lum * 0.80)).astype(np.float64)
est = np.zeros_like(img2); done = np.zeros(known.shape, bool)
for sg in (2, 4, 8, 16, 32, 64):
    wsum = ndi.gaussian_filter(known, sg)
    val = ndi.gaussian_filter(img2 * known[..., None], (sg, sg, 0)) / np.maximum(wsum, 1e-6)[..., None]
    take = (~done) & (wsum > 0.05)
    est[take] = val[take]; done |= take
near = known.astype(bool) & (fy > 1.69) & (fy < 1.725) & (fz > headz + 0.05)
fill = np.median(img2[near], 0)
grain = img2 - ndi.gaussian_filter(img2, (3, 3, 0))
gn = np.std(grain[near], 0)
rng = np.random.default_rng(7)
noise = ndi.gaussian_filter(rng.normal(0, 1, img2.shape[:2]), 0.7)
noise = noise / max(noise.std(), 1e-6)
patch = est * (1 + 0.5 * noise[..., None] * (gn / np.maximum(fill, 1e-3))[None, None, :])
alpha = np.clip(ndi.distance_transform_edt(notskin) / 6.0, 0, 1)
out2 = img2 * (1 - alpha[..., None]) + patch * alpha[..., None]
out2[~fore] = img2[~fore]
print('FRINGE fill colour', (fill * 255).round().tolist())
print('FRINGE forehead texels', int(fore.sum()), 'repainted', int(notskin.sum()), 'skin lum %.3f' % sk_lum, 'head z %.3f' % headz)
Image.fromarray((np.clip(out2, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT)
vis2 = (img2 * 255).astype(np.uint8).copy()
vis2[notskin] = (0, 255, 255)
vis2[fore & ~notskin] = (vis2[fore & ~notskin] * 0.6).astype(np.uint8)
Image.fromarray(vis2).resize((1024, 1024), Image.NEAREST).save('review/fringe_fix_forehead.png')
