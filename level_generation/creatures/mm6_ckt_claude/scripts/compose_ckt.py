#!/usr/bin/env python3
"""Cockatrice texture set from the Meshy retexture (meshy/retexture_v1, painted from the Codex HD masters).

Writes textures/ckt_a_basecolor.png (Meshy base colour, islands padded), ckt_normal_1k.png, ckt_metal_rough_1k.png
(R 1 until the AO bake, G roughness by class, B 0), ckt_material_classes.png and ckt_region_weights.npz with one
region, `membrane`: the turquoise wing membranes, the only part the native palettes 680/681/682 recolour (sprite
package note: brown body and tail, pink neck, orange beak and legs, red brow and ivory spikes/wing bones/talons stay).
Membrane = wing texels (part 1 in work/uv3d.npz) with a turquoise hue; wing bones and claws are pale and excluded.
Next: bake AO, grade, then scripts/tier_ramps.py."""
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
wing = part_map == 1
membrane = wing & (h > 140) & (h < 215) & (s > 0.2)
membrane = ndimage.binary_closing(membrane, iterations=2) & wing
pale = valid & (s < 0.28) & (v > 0.55)                       # ivory spikes, wing bones, talons
orange = valid & (h > 25) & (h < 55) & (s > 0.45) & (v > 0.45)   # beak, feet
pink = (part_map == 4) & ((h < 20) | (h > 330)) & (s > 0.2) & (s < 0.6) & (v > 0.5)
weight = ndimage.gaussian_filter(membrane.astype(np.float32), 1.0) * valid

classes = np.zeros(part_map.shape, np.uint8)
classes[valid] = 2                                          # feathers
classes[pink | orange] = 1                                  # bare skin, scaly legs, beak
classes[membrane] = 3
classes[pale] = 4                                           # spikes, wing bones, talons
save(base, OUT / 'ckt_a_basecolor.png')
save(normal, OUT / 'ckt_normal_1k.png', 1024)
r = np.clip(rough * 0.3 + 0.6, 0.5, 0.85); r[membrane] = 0.7; r[pale] = 0.45
save(np.stack([np.ones_like(r), r, np.zeros_like(r)], -1), OUT / 'ckt_metal_rough_1k.png', 1024)
Image.fromarray(classes, 'L').resize((1024, 1024), Image.NEAREST).save(OUT / 'ckt_material_classes.png')
np.savez_compressed(OUT / 'ckt_region_weights.npz', names=np.array(['membrane']), membrane=pad(weight))
print('COMPOSED', {'membrane': int(membrane.sum()), 'wing': int(wing.sum()), 'pale': int(pale.sum())})
