#!/usr/bin/env python3
"""Smooth skin shading on the low-poly arms (user review 2026-10-20: angular light and dark patches on the bare arms;
the colour is even in 3D, the patches are the lighting of large triangles whose smooth vertex normals are interpolated
linearly, and the skin's Meshy normal map is flat there). Per skin texel of the arms (material class 1, dominant bone
not a hand or finger), the target normal is the Gaussian-weighted mean (SIGMA m in rest pose) of the interpolated
normals of the nearby skin texels that face the same way (dot > 0.5); it is written into textures/m410_normal_1k.png in
that texel's tangent frame (frame_raster.py) in the map's own +y-down (Meshy) convention, so prepare_actor_glb.py still
measures and converts the whole map. Run after compose_m410.py (which rewrites the normal map from Meshy's).
Args: [SIGMA=0.025]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
SIGMA = float(sys.argv[1]) if len(sys.argv) > 1 else 0.025
R = np.load(HERE / 'work' / 'uvraster_UVMap.npz'); F = np.load(HERE / 'work' / 'frameraster_UVMap.npz')
pos, bone, names = R['pos'], R['bone'], R['bone_names']
nrm, tu, tv = F['nrm'], F['tu'], F['tv']
cl = np.asarray(Image.open(HERE / 'textures' / 'm410_material_classes.png'))
hand = np.array([any(k in str(n) for k in ('Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) for n in names])
ok = (cl == 1) & (np.abs(nrm).sum(2) > 0) & (bone >= 0)
arm = ok & ~hand[np.clip(bone, 0, None)]
idx = np.flatnonzero(ok); aidx = np.flatnonzero(arm)
P = pos.reshape(-1, 3); Nn = nrm.reshape(-1, 3)
tree = cKDTree(P[idx]); d, j = tree.query(P[aidx], k=96, distance_upper_bound=3 * SIGMA)
valid = np.isfinite(d); j = np.where(valid, j, 0)
nb = Nn[idx][j]; n0 = Nn[aidx]
w = np.where(valid, np.exp(-0.5 * (np.where(valid, d, 0) / SIGMA) ** 2), 0) * ((nb * n0[:, None]).sum(2) > 0.5)
ns = (w[..., None] * nb).sum(1); ns /= np.maximum(np.linalg.norm(ns, axis=1, keepdims=True), 1e-9)
# tangent frame of each texel: t = +u, b = +v (both made orthogonal to the interpolated normal)
T = tu.reshape(-1, 3)[aidx]; V = tv.reshape(-1, 3)[aidx]
T = T - n0 * (T * n0).sum(1, keepdims=True); T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
V = V - n0 * (V * n0).sum(1, keepdims=True) - T * (V * T).sum(1, keepdims=True)
V /= np.maximum(np.linalg.norm(V, axis=1, keepdims=True), 1e-9)
x = (ns * T).sum(1); y = -(ns * V).sum(1); z = (ns * n0).sum(1)                  # +y down the image (Meshy)
enc = np.stack([x, y, z], 1); enc /= np.maximum(np.linalg.norm(enc, axis=1, keepdims=True), 1e-9)
path = HERE / 'textures' / 'm410_normal_1k.png'
img = np.asarray(Image.open(path).convert('RGB')).copy().reshape(-1, 3)
img[aidx] = np.clip(np.round((enc + 1) * 127.5), 0, 255).astype(np.uint8)
Image.fromarray(img.reshape(nrm.shape[0], nrm.shape[1], 3)).save(path)
tilt = np.degrees(np.arccos(np.clip(z, -1, 1)))
print(f'SKINNORMALS {aidx.size} arm texels, sigma {SIGMA * 100:.1f} cm: tilt p50 {np.percentile(tilt, 50):.1f} '
      f'p95 {np.percentile(tilt, 95):.1f} max {tilt.max():.1f} deg')
