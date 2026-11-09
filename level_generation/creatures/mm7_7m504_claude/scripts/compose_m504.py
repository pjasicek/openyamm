#!/usr/bin/env python3
"""Textures for the MM7 Chicken (CLAUDE_CREATURE_TEXTURES.md; small animal: one atlas, our Smart UV islands with the
head at 2.5x density). Run after uv_raster.py (UVMap at 2048 and 1024) and bake_ao.py.
ONE look: descriptors 466-468 (zchicken a/b/c) all draw sprite group m504 in palette 545, so no colour tiers, no region
mask, no ramps (build_runtime.sh applies the material extras only, scripts/set_extras.py).
- Classes: eyes (pieces 9-10) 6; legs and beak (keratin: the shell below 9.5 cm at rest, and the yellow head texels) 4;
  comb and wattles (red head texels) 3 'skin'; feathers 2 (everything else, with the tail feather cards 1-8).
  Specular mask feather 0.15, keratin 0.5, skin 0.35, eye 0.9; roughness feather 0.85.
- Base colour 2K graded by the rest-pose AO (strength 0.35); normal/ORM 1K. Writes textures/m504_*."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
T = HERE / 'textures'; T.mkdir(exist_ok=True)
SPEC = {'fur': 0.15, 'claw': 0.5, 'eye': 0.9, 'skin': 0.35}
ROUGH = {'fur': 0.85, 'claw': 0.45, 'eye': 0.15, 'skin': 0.6}
CLS = {'fur': 2, 'claw': 4, 'eye': 6, 'skin': 3}
M = HERE / 'meshy' / 'retexture_v1'


def load(path, n, mode='RGB'):
    im = Image.open(path).convert(mode)
    return np.asarray(im.resize((n, n), Image.LANCZOS) if im.size != (n, n) else im, np.float64) / 255


def save(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, optimize=True)


def pad(img, cov):
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    out = img[iy, ix]; out[cov] = img[cov]; return out


def classes(n):
    Rz = np.load(HERE / 'work' / f'uvraster_UVMap_{n}.npz'); pc = Rz['piece']; cov = pc >= 0; pos = Rz['pos']
    base = load(M / 'texture_urls_0_base_color.png', n); v = base.max(-1)
    head = cov & (pc == 0) & (pos[..., 2] > 0.37)
    r, g, b = base[..., 0], base[..., 1], base[..., 2]
    red = (r > 0.35) & (r > 1.6 * g) & (r > 1.6 * b)
    yellow = (r > 0.45) & (g > 0.3) & (b < 0.6 * g) & ~red
    C = {'eye': cov & np.isin(pc, (9, 10)), 'skin': head & red}
    C['claw'] = cov & (pc == 0) & ((pos[..., 2] < 0.095) | (head & yellow)) & ~C['skin']
    C['fur'] = cov & ~C['eye'] & ~C['claw'] & ~C['skin']
    return C, cov, base


C2, cov2, base2 = classes(2048)
ao = load(HERE / 'work' / 'ao_UVMap.png', 2048, 'L')
f = np.clip(1 - 0.35 + 0.35 * np.maximum(ao, 0.45), 0, 1)
g = base2.copy(); g[cov2] = base2[cov2] * f[cov2][:, None]
save(pad(g, cov2), T / 'm504_basecolor_2k.png')
C1, cov1, _ = classes(1024)
save(pad(load(M / 'texture_urls_0_normal.png', 1024), cov1), T / 'm504_normal_1k.png')
rough_m = load(M / 'texture_urls_0_roughness.png', 1024, 'L')
cls = np.zeros((1024, 1024), np.uint8); spec = np.zeros((1024, 1024)); rgh = np.full((1024, 1024), 0.85)
for name, m in C1.items():
    if m.any():
        cls[m] = CLS[name]; spec[m] = SPEC[name]
        rgh[m] = np.clip(ROUGH[name] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
save(np.stack([pad(spec, cov1), pad(rgh, cov1), np.zeros((1024, 1024))], -1), T / 'm504_metal_rough_1k.png')
Image.fromarray(cls).save(T / 'm504_material_classes.png')
print('CLASSES', {k: int(m.sum()) for k, m in C1.items()}, 'covered', int(cov1.sum()))
