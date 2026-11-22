#!/usr/bin/env python3
"""Scorpion texture set from the Meshy retexture (meshy/retexture_v1: 4K paint on our uv_atlas layout from the four
Codex HD masters). Run after scripts/dump_uv3d.py and scripts/bake_ao.py; grade, ramps and gutter fill follow in
build_runtime.sh.

Writes into textures/:
  scorpion_basecolor.png          2K base colour (4K Meshy paint downsampled once, Lanczos)
  scorpion_normal_1k.png          Meshy normal (+y down; tools/prepare_actor_glb.py converts it)
  scorpion_mr_1k.png              ORM: R baked AO, G roughness (Meshy, clamped per class), B 0
  scorpion_region_mask.png        1K RGBA: R carapace (body, tail segments, chelicerae), G legs and pincers (the eight
                                  walking legs, both pedipalps with their claws), B stinger (the bulb and the sting:
                                  the Stinger bone's triangles), A eyes (the two eye pieces). Padded into the gutters.
  scorpion_material_classes.png   1K labels: 4 chitin (carapace, legs, claws, sting), 6 eye
Classes per texel from the Smart Topology piece (face attribute `piece`, prep.py numbering) and the dominant bone of
each triangle (work/uv3d.npz from dump_uv3d.py)."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'mm6_gob_claude' / 'scripts'))
import compose_textures_v2 as C   # noqa: E402  (rasterise: 2048 label/xyz maps; main() runs only as a script)

SRC = ROOT / 'meshy/retexture_v1/texture_urls_0'
OUT = ROOT / 'textures'
N = 2048
LIMBS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
EYES = [14, 15]

data = np.load(ROOT / 'work/uv3d.npz')
bones = [str(b) for b in data['bones']]
STING = bones.index('Stinger')
code = data['mpart'] * 100 + data['bone']
label, xyz = C.rasterise(data, values=code)
valid = label >= 0
piece = np.where(valid, label // 100, -1)
bone = np.where(valid, label % 100, -1)


def on(ps):
    return valid & np.isin(piece, ps)


base = Image.open(f'{SRC}_base_color.png').convert('RGB').resize((N, N), Image.LANCZOS)
base.save(OUT / 'scorpion_basecolor.png', optimize=True)

eye = on(EYES)
limbs = on(LIMBS)
sting = on([0]) & (bone == STING)
carapace = valid & ~eye & ~limbs & ~sting
print('CLASSES texels', {'carapace': int(carapace.sum()), 'limbs': int(limbs.sum()), 'sting': int(sting.sum()),
                         'eye': int(eye.sum()), 'valid': int(valid.sum())})

chan = [carapace, limbs, sting, eye]
_, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
mask = np.zeros((N, N, 4), np.float32)
for c, sel in enumerate(chan):
    w = ndimage.gaussian_filter(sel.astype(np.float32), 0.8) * valid
    padded = w[iy, ix]; padded[valid] = w[valid]
    mask[..., c] = padded
total = mask.sum(-1, keepdims=True)
mask = np.where(total > 1e-6, mask / np.maximum(total, 1e-6), mask)
chans = [Image.fromarray((mask[..., c] * 255 + 0.5).astype(np.uint8), 'L').resize((1024, 1024), Image.LANCZOS)
         for c in range(4)]
Image.merge('RGBA', chans).save(OUT / 'scorpion_region_mask.png')

Image.open(f'{SRC}_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS).save(OUT / 'scorpion_normal_1k.png')
rough = np.asarray(Image.open(f'{SRC}_roughness.png').convert('L').resize((N, N), Image.LANCZOS)) / 255.0
rough = np.where(eye, 0.15, np.clip(rough, 0.3, 0.75))       # glossy chitin, wet eyes
ao = np.asarray(Image.open(OUT / 'scorpion_ao_2k.png').convert('L'), np.float32) / 255.0
orm = np.stack([ao, rough, np.zeros_like(ao)], -1)
Image.fromarray((orm * 255 + 0.5).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(OUT / 'scorpion_mr_1k.png')

classes = np.zeros((N, N), np.uint8)
classes[valid] = 4
classes[eye] = 6
Image.fromarray(classes, 'L').resize((1024, 1024), Image.NEAREST).save(OUT / 'scorpion_material_classes.png')
pv = np.zeros((N, N, 3), np.uint8)
for sel, col in ((carapace, (150, 90, 40)), (limbs, (60, 160, 60)), (sting, (255, 170, 0)), (eye, (0, 200, 255))):
    pv[sel] = col
Image.fromarray(pv).resize((1024, 1024), Image.NEAREST).save(ROOT / 'review' / 'region_classes.png')
print('COMPOSED')
