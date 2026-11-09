#!/usr/bin/env python3
"""Third pass (2026-11-01): the Meshy 4K retexture of the mallet (meshy/mallet_retex_v1, on our uv_atlas.py layout) downsampled once to
OUT px with a gentle grade (texture quality pass), plus the tier region mask: the texels' 3D positions (work/mallet.npz, mallet frame) and
the retexture's metallic map split the surface into R head wood (head, not metal), G iron (metal outside the end plates: bands, rivets,
rims, the shaft's rings, ferrule and cap), B the engraved end plates (metal on the head's end faces). tier_ramps.py ramps the tiers.
Writes textures/gi_mallet_{base,normal,orm,region_mask}.png."""
import numpy as np
from PIL import Image
from scipy import ndimage
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; SRC = HERE / 'meshy' / 'mallet_retex_v1'; T = HERE / 'textures'
OUT = 1024
Z = np.load(HERE / 'work' / 'mallet.npz'); V, F, UV = Z['V'], Z['F'], Z['UVc']
def load(n, size=None):
    im = Image.open(SRC / f'texture_urls_0_{n}.png').convert('RGB')
    return im.resize((OUT, OUT), Image.LANCZOS) if size is None else im
base = np.asarray(load('base_color'), np.float32) / 255
# gentle grade (as the body: saturation 0.95, contrast 1.03)
lum = base @ np.array([0.2126, 0.7152, 0.0722])
base = np.clip(lum[..., None] + (base - lum[..., None]) * 0.95, 0, 1); base = np.clip((base - 0.5) * 1.03 + 0.5, 0, 1)
nrm = np.asarray(load('normal'), np.float32) / 255
rough = np.asarray(load('roughness'), np.float32)[..., 0] / 255; metal = np.asarray(load('metallic'), np.float32)[..., 0] / 255
# texel positions by UV rasterisation at OUT
S = OUT; pos = np.zeros((S, S, 3)); cov = np.zeros((S, S), bool)
Tr = V[F]
for t in range(len(F)):
    u = UV[t]; x = u[:, 0] * S; y = (1 - u[:, 1]) * S
    x0, x1 = int(max(np.floor(x.min()) - 1, 0)), int(min(np.ceil(x.max()) + 1, S - 1)); y0, y1 = int(max(np.floor(y.min()) - 1, 0)), int(min(np.ceil(y.max()) + 1, S - 1))
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
    if abs(d) < 1e-12: continue
    a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d; b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d; c = 1 - a - b
    m = (a >= -0.02) & (b >= -0.02) & (c >= -0.02)
    pos[y0:y1 + 1, x0:x1 + 1][m] = (a[..., None] * Tr[t, 0] + b[..., None] * Tr[t, 1] + c[..., None] * Tr[t, 2])[m]; cov[y0:y1 + 1, x0:x1 + 1][m] = True
idx = ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True); pos = pos[idx[0], idx[1]]
px, py = pos[..., 0], pos[..., 1]
head = (py < -0.02) & (py > -0.36) & (np.hypot(px, pos[..., 2]) > 0.04)
endf = head & (np.abs(px) > 0.235)
met = ndimage.gaussian_filter(metal, 0.7) > 0.45
sat = (base.max(2) - base.min(2)) / np.maximum(base.max(2), 1e-3)
reg = np.zeros((S, S, 4), np.float32)
reg[..., 2] = (endf & met)
reg[..., 1] = met & ~(endf & met)
reg[..., 0] = head & ~met
for c in range(3): reg[..., c] = ndimage.gaussian_filter(reg[..., c], 0.6)
save = lambda arr, name, mode: Image.merge(mode, [Image.fromarray((np.clip(arr[..., c], 0, 1) * 255 + .5).astype('u1'), 'L') for c in range(arr.shape[-1])]).save(T / name)
save(base, 'gi_mallet_base.png', 'RGB'); save(nrm, 'gi_mallet_normal.png', 'RGB')
save(np.dstack([np.ones_like(rough), rough, metal]), 'gi_mallet_orm.png', 'RGB'); save(reg, 'gi_mallet_region_mask.png', 'RGBA')
print('MALLETTEX meshy', OUT, 'covered', round(float(cov.mean()), 3), 'regions wood/iron/plates', [round(float((reg[..., c] > 0.5)[cov].mean()), 3) for c in range(3)])
