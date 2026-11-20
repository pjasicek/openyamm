#!/usr/bin/env python3
"""Spider texture set from the Meshy retexture (meshy/retexture_v1, painted from the Codex HD masters).

Writes textures/spi1_a_basecolor.png (Meshy base colour, islands padded), spi1_normal_1k.png, spi1_metal_rough_1k.png
(R 1, G roughness by class, B 0) and spi1_region_weights.npz: one region, `chitin` = hair, chitin and legs, which
tiers recolour; the orange eyes and pale fangs stay as painted. Eyes are bright saturated red-orange texels on the
cephalothorax front; fangs are pale texels at the chelicera tips (3D position from work/uv3d.npz).
Next: bake AO, grade, then scripts/tier_ramps.py (ramps from the native palette sprites)."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'mm6_gob_claude' / 'scripts'))
import compose_textures_v2 as C

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'meshy/retexture_v1/texture_urls_0'
OUT = ROOT / 'textures'; OUT.mkdir(exist_ok=True)
data = np.load(ROOT / 'work/uv3d.npz')
part_map, xyz = C.rasterise(data)
strict, _ = C.rasterise(data, tol=0.0)
interior = ndimage.binary_erosion(strict >= 0, iterations=2)
_, (iy, ix) = ndimage.distance_transform_edt(~interior, return_indices=True)


def pad(a):
    o = a[iy, ix]; o[interior] = a[interior]; return o


def save(array, path, size=None):
    image = Image.fromarray(np.clip(array * 255 + 0.5, 0, 255).astype(np.uint8))
    if size:
        image = image.resize((size, size), Image.LANCZOS)
    image.save(path, optimize=True)


base = pad(C.load(str(SRC) + '_base_color.png'))
normal = pad(C.load(str(SRC) + '_normal.png'))
rough = pad(C.load(str(SRC) + '_roughness.png', 'L'))
h, s, v = C.hsv(base)
valid = part_map >= 0
x, y, z = xyz[..., 0], xyz[..., 1], xyz[..., 2]
head = valid & (y < -0.10) & (z > 0.20)
eye = head & ((h < 25) | (h > 340)) & (s > 0.55) & (v > 0.45)
eye = ndimage.binary_dilation(eye, iterations=1) & valid
fang = valid & (y < -0.13) & (z < 0.27) & (np.abs(x) < 0.08) & (s < 0.45) & (v > 0.45)
chitin = valid & ~eye & ~fang
weight = ndimage.gaussian_filter(chitin.astype(np.float32), 1.0) * valid

save(base, OUT / 'spi1_a_basecolor.png')
save(normal, OUT / 'spi1_normal_1k.png', 1024)
r = np.clip(rough * 0.3 + 0.62, 0.55, 0.85); r[eye] = 0.2; r[fang] = 0.35
save(np.stack([np.ones_like(r), r, np.zeros_like(r)], -1), OUT / 'spi1_metal_rough_1k.png', 1024)
np.savez_compressed(OUT / 'spi1_region_weights.npz', names=np.array(['chitin']), chitin=pad(weight))
print('COMPOSED', {'chitin': int(chitin.sum()), 'eye': int(eye.sum()), 'fang': int(fang.sum())})
