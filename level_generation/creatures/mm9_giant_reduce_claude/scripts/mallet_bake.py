#!/usr/bin/env python3
"""Bake the installed mallet's maps onto the rebuilt mallet's UVs (work/mallet_texels.npz + work/mallet_hits.npz):
base colour, ORM and the 4-channel region mask are sampled bilinearly at the old UV of each texel's source point; the
normal map is re-expressed: old shading normal (interpolated split normals, so studs, bands and rings keep their
curvature) perturbed by the old tangent-space map, then written in the new triangle's frame. Frames follow
game/shaders/fs_model.sc: tangent along +u, bitangent along +v (down the image), mapped = T*x - B*y + N*z.
Empty texels take the nearest baked texel (gutters). Writes work/tex_new/gi_mallet_{base,normal,orm,region_mask}.png
and work/mallet_bake_stats.json."""
import json
import os
import numpy as np
from PIL import Image
from scipy import ndimage
RES = 1024
o = np.load('work/mallet_old.npz'); oP, oN, oUV, oI = (o[k].astype(float) if k != 'I' else o[k] for k in ('P', 'N', 'UV', 'I'))
n_ = np.load('work/mallet_new.npz'); nP, nUV, nI = n_['P'].astype(float), n_['UV'].astype(float), n_['I']
t = np.load('work/mallet_texels.npz'); h = np.load('work/mallet_hits.npz')
xs, ys, nf, nor = t['x'], t['y'], t['face'], t['nor']; of, hit = h['face'], h['hit']


def frames(P, UV, I):
    e1 = P[I[:, 1]] - P[I[:, 0]]; e2 = P[I[:, 2]] - P[I[:, 0]]
    d1 = UV[I[:, 1]] - UV[I[:, 0]]; d2 = UV[I[:, 2]] - UV[I[:, 0]]
    det = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]; det = np.where(np.abs(det) < 1e-12, 1e-12, det)
    T = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) / det[:, None]       # dP/du
    B = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) / det[:, None]       # dP/dv
    return T, B


def ortho(V, Nn):
    V = V - Nn * (V * Nn).sum(1, keepdims=True)
    return V / (np.linalg.norm(V, axis=1, keepdims=True) + 1e-12)


# old barycentric of the hit point
A, Bv, C = oP[oI[of, 0]], oP[oI[of, 1]], oP[oI[of, 2]]
v0, v1, v2 = Bv - A, C - A, hit - A
d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1); d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
den = d00 * d11 - d01 * d01; den = np.where(np.abs(den) < 1e-18, 1e-18, den)
bv = (d11 * d20 - d01 * d21) / den; bw = (d00 * d21 - d01 * d20) / den; bu = 1 - bv - bw
L = np.clip(np.column_stack([bu, bv, bw]), 0, None); L /= L.sum(1, keepdims=True)
ouv = (L[:, :, None] * oUV[oI[of]]).sum(1); on = (L[:, :, None] * oN[oI[of]]).sum(1); on /= np.linalg.norm(on, axis=1, keepdims=True)


def load(name):
    return np.asarray(Image.open(f'work/tex/{name}.png'), np.float64) / 255


def sample(img, uv):
    H, W = img.shape[:2]; x = uv[:, 0] * W - 0.5; y = uv[:, 1] * H - 0.5
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = (x - x0)[:, None]; fy = (y - y0)[:, None]
    def at(yy, xx):
        return img[np.clip(yy, 0, H - 1), np.clip(xx, 0, W - 1)]
    return (at(y0, x0) * (1 - fx) * (1 - fy) + at(y0, x0 + 1) * fx * (1 - fy) + at(y0 + 1, x0) * (1 - fx) * fy
            + at(y0 + 1, x0 + 1) * fx * fy)


out = {}
for name in ('gi_mallet_base', 'gi_mallet_orm', 'gi_mallet_region_mask'):
    img = load(name); val = sample(img, ouv)
    canvas = np.zeros((RES, RES, img.shape[2])); canvas[ys, xs] = val; out[name] = canvas
# normals
oT, oB = frames(oP, oUV, oI); nT, nB = frames(nP, nUV, nI)
m = sample(load('gi_mallet_normal'), ouv) * 2 - 1
mx, my = m[:, 0], m[:, 1]; mz = np.sqrt(np.clip(1 - mx * mx - my * my, 0, 1))
To, Bo = ortho(oT[of], on), ortho(oB[of], on)
nobj = To * mx[:, None] - Bo * my[:, None] + on * mz[:, None]; nobj /= np.linalg.norm(nobj, axis=1, keepdims=True)
Tn, Bn = ortho(nT[nf], nor), ortho(nB[nf], nor)
x = (nobj * Tn).sum(1); y = -(nobj * Bn).sum(1); z = (nobj * nor).sum(1)
z = np.maximum(z, 0.15); v = np.column_stack([x, y, z]); v /= np.linalg.norm(v, axis=1, keepdims=True)
canvas = np.zeros((RES, RES, 3)); canvas[ys, xs] = v * 0.5 + 0.5; out['gi_mallet_normal'] = canvas
covered = np.zeros((RES, RES), bool); covered[ys, xs] = True
_, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
os.makedirs('work/tex_new', exist_ok=True)
for name, canvas in out.items():
    filled = canvas[iy, ix]
    mode = 'RGBA' if filled.shape[2] == 4 else 'RGB'
    Image.fromarray((np.clip(filled, 0, 1) * 255 + 0.5).astype(np.uint8), mode).save(f'work/tex_new/{name}.png')
stats = {'texels': int(len(xs)), 'coverage': round(float(covered.mean()), 3), 'ray_hits': int((h['kind'] == 1).sum()),
         'nearest_fallback': int((h['kind'] == 2).sum()), 'normal_z_clamped': int((z <= 0.15).sum()),
         'new_scale_px_per_m': float(n_['scale'])}
json.dump(stats, open('work/mallet_bake_stats.json', 'w'), indent=1); print('BAKE', stats)
