#!/usr/bin/env python3
"""Flying Eye texture set from the Meshy retexture (meshy/retexture_v1, painted from the Codex HD masters).

Writes textures/bh_a_basecolor.png (Meshy base colour, islands padded), bh_normal_1k.png, bh_metal_rough_1k.png
(R 1, G roughness by class, B 0) and bh_region_weights.npz with the sprite package's three recolour regions
(../mm6_bh manifest `regions`): skin (red-brown back of the skull), face (grey face mask, horns, teeth, tendrils on the
face side) and iris (coloured iris inside the eyeball). Pupil, eye highlight and the dark mouth interior stay as
painted. Next: bake AO, grade, then scripts/tier_ramps.py."""
import json
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
info = json.load(open(ROOT / 'work/rig_info.json'))
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
eye_centre = np.array(info['eye'])
near_eye = valid & (np.linalg.norm(xyz - eye_centre, axis=-1) < 0.13)   # eyeball radius ~0.125 m
iris = near_eye & (h > 40) & (h < 170) & (s > 0.35) & (v > 0.18)
mouth = valid & (xyz[..., 1] < info['front_y'] + 0.12) & (np.abs(xyz[..., 2] - info['mouth_z']) < 0.08) \
    & (np.abs(xyz[..., 0]) < 0.11) & (v < 0.35) & (s > 0.35)
pupil = near_eye & ((v < 0.15) | ((s < 0.15) & (v > 0.8)))     # dark pupil and white highlight stay as painted
# Ivory teeth, fangs and tendril tips belong to the face/horn region (sprite mask G), not to the red skin.
ivory = valid & ~near_eye & (v > 0.5) & (s < 0.5) & (h > 15) & (h < 70)
skin = valid & ~iris & ~pupil & ~mouth & ~ivory & ((h < 40) | (h > 330)) & (s > 0.28)
face = valid & ~iris & ~pupil & ~mouth & ~skin & ((s < 0.45) | ivory)
weights = {name: pad(ndimage.gaussian_filter(mask.astype(np.float32), 1.0) * valid)
           for name, mask in (('skin', skin), ('face', face), ('iris', iris))}

save(base, OUT / 'bh_a_basecolor.png')
save(normal, OUT / 'bh_normal_1k.png', 1024)
r = np.clip(rough * 0.3 + 0.6, 0.5, 0.85); r[skin] = 0.62; r[face] = 0.75; r[iris | pupil] = 0.15
save(np.stack([np.ones_like(r), r, np.zeros_like(r)], -1), OUT / 'bh_metal_rough_1k.png', 1024)
np.savez_compressed(OUT / 'bh_region_weights.npz', names=np.array(['skin', 'face', 'iris']), **weights)
print('COMPOSED', {k: int(m.sum()) for k, m in (('skin', skin), ('face', face), ('iris', iris), ('mouth', mouth))})
