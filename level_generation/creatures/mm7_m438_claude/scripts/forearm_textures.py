#!/usr/bin/env python3
"""Severed-forearm prop textures (512 x 512) from the composed body set: each prop triangle copies its body-atlas
triangle (work/forearm_uv.npz: old UVMap -> new PropUV, an exact per-triangle affine map, bilinear samples; normals
turned with the UV frame and written in the glTF +y-up convention), the cap
(the elbow wound, review 2026-10-20) takes the native wound ramp (textures/m438_swatches.json, the same crimson as the
re-graded stump) through a smooth noise field (dark cores, lighter flesh), the two bone shafts the stump's ivory with
mottling; flat normals, wound/bone specular and roughness. Gutters padded with the nearest island texel.
Writes textures/m438_forearm_{basecolor,normal,metal_rough,material_classes}.png."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]; T = HERE / 'textures'
S = 512
D = np.load(HERE / 'work' / 'forearm_uv.npz'); old, new, cap = D['old'], D['new'], D['cap']
bone = D['bone'] if 'bone' in D else np.zeros_like(cap)
src = {k: np.asarray(Image.open(T / f'm438_{k}.png').convert('RGB'), np.float64) / 255
       for k in ('basecolor_1k', 'normal_1k', 'metal_rough_1k')}
cls = np.asarray(Image.open(T / 'm438_material_classes.png'))
out = {k: np.zeros((S, S, 3)) for k in src}; oc = np.zeros((S, S), np.uint8); cov = np.zeros((S, S), bool)
SW = json.loads((T / 'm438_swatches.json').read_text())
WR = np.array(SW['wound_ramp_srgb']) / 255; BONE = np.array(SW['bone_srgb']) / 255
NZ = ndimage.gaussian_filter(np.random.default_rng(438).normal(0, 1, (S, S)), 3.0); NZ = (NZ - NZ.min()) / max(NZ.max() - NZ.min(), 1e-6)
NB = ndimage.gaussian_filter(np.random.default_rng(439).normal(0, 1, (S, S)), 1.5); NB /= max(np.abs(NB).max(), 1e-6)


def sample(img, u, v):
    H, W = img.shape[:2]
    x = np.clip(u * W - 0.5, 0, W - 1.001); y = np.clip((1 - v) * H - 0.5, 0, H - 1.001)
    x0, y0 = x.astype(int), y.astype(int); fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    if img.ndim == 2:
        return img[y0, x0]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy) + img[y0 + 1, x0] * (1 - fx) * fy
            + img[y0 + 1, x0 + 1] * fx * fy)


for t in range(len(new)):
    P = new[t] * S                                               # texel space (x right, y up)
    lo = np.floor(P.min(0)).astype(int) - 1; hi = np.ceil(P.max(0)).astype(int) + 1
    xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], S)), np.arange(max(lo[1], 0), min(hi[1], S)))
    q = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
    a, b, c = P
    m = np.array([b - a, c - a]).T
    if abs(np.linalg.det(m)) < 1e-9:
        continue
    w = np.linalg.solve(m, (q - a).T).T; l1, l2 = w[:, 0], w[:, 1]; l0 = 1 - l1 - l2
    inside = (l0 >= -0.02) & (l1 >= -0.02) & (l2 >= -0.02)
    if not inside.any():
        continue
    px, py = xs.ravel()[inside], (S - 1 - ys.ravel()[inside])     # image rows top-down
    if bone[t]:
        out['basecolor_1k'][py, px] = np.clip(BONE[None, :] * (1 + 0.12 * NB[py, px][:, None]), 0, 1)
        out['normal_1k'][py, px] = (0.5, 0.5, 1.0)
        out['metal_rough_1k'][py, px] = (0.45, 0.45, 0.0)
        oc[py, px] = 5
    elif cap[t]:
        tt = np.clip(NZ[py, px] * 1.4 - 0.2, 0, 1) * (len(WR) - 1)
        i0 = np.minimum(tt.astype(int), len(WR) - 2); f_ = (tt - i0)[:, None]
        out['basecolor_1k'][py, px] = WR[i0] * (1 - f_) + WR[i0 + 1] * f_
        out['normal_1k'][py, px] = (0.5, 0.5, 1.0)
        out['metal_rough_1k'][py, px] = (0.45, 0.5, 0.0)
        oc[py, px] = 1
    else:
        uv = l0[inside, None] * old[t][0] + l1[inside, None] * old[t][1] + l2[inside, None] * old[t][2]
        for k in src:
            out[k][py, px] = sample(src[k], uv[:, 0], uv[:, 1])
        # tangent-space normals follow the UV frame: turn their xy by the rotation (polar part, reflection kept) of
        # this triangle's old -> new UV map, or the relaid islands would light from the wrong side
        Jo = np.array([old[t][1] - old[t][0], old[t][2] - old[t][0]]).T; Jn = np.array([new[t][1] - new[t][0], new[t][2] - new[t][0]]).T
        if abs(np.linalg.det(Jo)) > 1e-12:
            A = Jn @ np.linalg.inv(Jo); U_, _, Vt = np.linalg.svd(A); Rr = U_ @ Vt
            nv = out['normal_1k'][py, px] * 2 - 1; nv[:, 1] *= -1         # Meshy's +y-down map -> glTF +y up first
            nv[:, :2] = nv[:, :2] @ Rr.T
            out['normal_1k'][py, px] = np.clip((nv + 1) / 2, 0, 1)
        oc[py, px] = sample(cls, uv[:, 0], uv[:, 1])
    cov[py, px] = True
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
for k, name in (('basecolor_1k', 'basecolor'), ('normal_1k', 'normal'), ('metal_rough_1k', 'metal_rough')):
    o = out[k][iy, ix]
    Image.fromarray((np.clip(o, 0, 1) * 255 + 0.5).astype(np.uint8)).save(T / f'm438_forearm_{name}.png', optimize=True)
Image.fromarray(np.where(cov, oc, 0).astype(np.uint8)).save(T / 'm438_forearm_material_classes.png')
print('PROPTEX coverage', round(float(cov.mean()), 3), 'triangles', len(new), 'cap', int(cap.sum()))
