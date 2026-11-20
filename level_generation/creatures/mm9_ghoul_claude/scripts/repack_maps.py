#!/usr/bin/env python3
"""Body maps into the split-chart 2K layout, straight from Meshy's 4K output (one resample, as the rule says), before the grade: colour, normal with its tangent frames turned per face (islands may rotate), and the 1K ORM
and the AO from the old layout. Writes textures/ghoul_basecolor.png, ghoul_normal_1k.png, ghoul_metal_rough_1k.png, ghoul_ao_2k.png in the new layout and work/faces.npz with the new body UVs. Old layout: textures/old_layout/, work/faces_oldlayout.npz."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, 'scripts')
import project_lib as PL
Image.MAX_IMAGE_PIXELS = None
TX = Path('textures'); OLD = TX / 'old_layout'
F = dict(np.load('work/faces_oldlayout.npz')); R = np.load('work/repack.npz')
idx = R['body']; uvn = R['uvn']; uvo = F['uvb'][idx]; co = F['co'][idx]
S = 2048
_, _, cov, bar, fid = PL.raster(uvn, co, S)
print('atlas use', round(float(cov.mean()), 3))
auv = (bar[..., None] * uvo[fid]).sum(2)
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)


def warp(im, blur):
    im = np.stack([ndimage.gaussian_filter(im[..., c], blur) for c in range(im.shape[2])], -1) if blur else im
    return PL.sample(im, auv)[iy, ix]


b4 = np.asarray(Image.open('meshy/ghoul_body_retex/texture_urls_0_base_color.png').convert('RGB'), np.float32)
Image.fromarray(np.clip(warp(b4, 0.8) + 0.5, 0, 255).astype('u1')).save(TX / 'ghoul_basecolor.png')
ao = np.asarray(Image.open(OLD / 'ghoul_ao_2k.png').convert('RGB'), np.float32)
Image.fromarray(np.clip(warp(ao, 0) + 0.5, 0, 255).astype('u1')).save(TX / 'ghoul_ao_2k.png')
orm = np.asarray(Image.open(OLD / 'ghoul_metal_rough_1k.png').convert('RGB'), np.float32)
Image.fromarray(np.clip(warp(orm, 0) + 0.5, 0, 255).astype('u1')).resize((1024, 1024), Image.LANCZOS).save(TX / 'ghoul_metal_rough_1k.png')
N = np.asarray(Image.open('meshy/ghoul_body_retex/texture_urls_0_normal.png').convert('RGB'), np.float32) / 127.5 - 1
N[..., 1] *= -1
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
Image.fromarray(((np.clip(n2, -1, 1) + 1) * 127.5 + 0.5).astype('u1')).resize((1024, 1024), Image.LANCZOS).save(TX / 'ghoul_normal_1k.png')
F['uvb'] = F['uvb'].copy(); F['uvb'][idx] = uvn
np.savez('work/faces.npz', **F)
print('REPACK maps done')
