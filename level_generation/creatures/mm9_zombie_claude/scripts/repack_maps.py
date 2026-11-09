#!/usr/bin/env python3
"""Body maps into the repacked 2K layout, from the 4K final (one resample): colour, region mask, ORM; normal with its tangent frames turned per face (islands may rotate). Convention stays Meshy's +y down for prepare_actor_glb.py to convert."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, 'scripts')
import project_lib as PL
Image.MAX_IMAGE_PIXELS = None
TX = Path('textures')
F = np.load('work/faces.npz'); R = np.load('work/repack.npz')
idx = R['body']; uvn = R['uvn']; uvo = F['uvb'][idx]; co = F['co'][idx]
S = 2048
_, _, cov, bar, fid = PL.raster(uvn, co, S)
print('atlas use', round(float(cov.mean()), 3))
auv = (bar[..., None] * uvo[fid]).sum(2)
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
def warp(path, size, blur, out, mode='RGB'):
    im = np.asarray(Image.open(path).convert(mode), np.float32)
    im = np.stack([ndimage.gaussian_filter(im[..., c], blur) for c in range(im.shape[2])], -1) if blur else im
    r = PL.sample(im, auv)[iy, ix]
    res = Image.fromarray(np.clip(r + 0.5, 0, 255).astype('u1'), mode)
    if size != S: res = res.resize((size, size), Image.LANCZOS)
    res.save(TX / out)
d1 = np.linalg.norm(uvo[:, 1] - uvo[:, 0], axis=1).sum() / np.linalg.norm(uvn[:, 1] - uvn[:, 0], axis=1).sum()
print('scale new/old', round(float(1 / d1), 3))
warp(TX / 'zombie4k_final.png', S, 0.6, 'zombie_basecolor_final.png')
warp(TX / 'zombie_metal_rough_1k.png', 1024, 0, 'zombie_orm_rp.png')
warp(TX / 'zombie_region_mask_old.png', 1024, 0, 'zombie_region_mask.png', 'RGBA')
# normal
N = np.asarray(Image.open('meshy/zombie_body_retex/texture_urls_0_normal.png').convert('RGB'), np.float32) / 127.5 - 1
N[..., :2] *= 0.5; N /= np.linalg.norm(N, axis=2, keepdims=True); N[..., 1] *= -1
n_ = np.stack([ndimage.gaussian_filter(N[..., c], 0.8) for c in range(3)], -1)
def frames(uv):
    e1, e2 = co[:, 1] - co[:, 0], co[:, 2] - co[:, 0]; d1_, d2_ = uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
    det = d1_[:, 0] * d2_[:, 1] - d1_[:, 1] * d2_[:, 0]; det = np.where(np.abs(det) < 1e-12, 1e-12, det)
    T = (e1 * d2_[:, 1:2] - e2 * d1_[:, 1:2]) / det[:, None]; B = (e2 * d1_[:, 0:1] - e1 * d2_[:, 0:1]) / det[:, None]
    return T / np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-12), B / np.maximum(np.linalg.norm(B, axis=1, keepdims=True), 1e-12)
Ta, Ba = frames(uvo); Tn, Bn = frames(uvn)
sn = PL.sample(n_, auv)
aa = (Ta * Tn).sum(1)[fid]; ab = (Ba * Tn).sum(1)[fid]; ba = (Ta * Bn).sum(1)[fid]; bb = (Ba * Bn).sum(1)[fid]
n2 = np.stack([sn[..., 0] * aa + sn[..., 1] * ab, sn[..., 0] * ba + sn[..., 1] * bb, sn[..., 2]], -1)[iy, ix]
n2 /= np.maximum(np.linalg.norm(n2, axis=2, keepdims=True), 1e-6); n2[..., 1] *= -1
Image.fromarray(((np.clip(n2, -1, 1) + 1) * 127.5 + 0.5).astype('u1')).resize((1024, 1024), Image.LANCZOS).save(TX / 'zombie_normal_soft.png')
print('REPACK maps done')
