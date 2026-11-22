#!/usr/bin/env python3
"""Giant Toad texture set from the Meshy retexture (meshy/retexture_v1: 4K paint on our uv_atlas layout from the four
Codex HD masters). Run after scripts/dump_uv3d.py and scripts/bake_ao.py; grade and gutter fill follow in
build_textures.sh.

Writes into textures/:
  toad_basecolor.png          2K base colour (4K Meshy paint downsampled once, Lanczos)
  toad_normal_1k.png          Meshy normal (+y down; tools/prepare_actor_glb.py converts it)
  toad_mr_1k.png              ORM: R baked AO, G Meshy roughness, B 0
  toad_region_mask.png        1K RGBA: R = hide (everything but the eye domes), soft edge, padded into the gutters
  toad_material_classes.png   1K labels: 1 skin, 6 eye
  toad_tongue.png             256 px tongue colour (own material): glossy turquoise, darker at the root
Eyes: the two eye-dome pieces (small pieces above 0.6 m at the front) keep Meshy's paint and no ramp."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'mm6_gob_claude' / 'scripts'))
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import compose_textures_v2 as C   # noqa: E402  (rasterise: 2048 part/xyz maps)

SRC = ROOT / 'meshy/retexture_v1/texture_urls_0'
OUT = ROOT / 'textures'
data = np.load(ROOT / 'work/uv3d.npz')
part_map, xyz = C.rasterise(data)
valid = part_map >= 0

# eye pieces: small parts whose centre is high at the front of the head
eyes = []
for p in np.unique(data['part']):
    sel = data['part'] == p
    c = data['xyz'][sel].reshape(-1, 3).mean(0)
    if sel.sum() < 700 and c[2] > 0.62 and c[1] < -0.45 and abs(c[0]) > 0.05:
        eyes.append(int(p))
print('EYE pieces', eyes)
eye_piece = np.isin(part_map, eyes)
_raw = np.asarray(Image.open(f'{SRC}_base_color.png').convert('L').resize((2048, 2048), Image.LANCZOS)) / 255.0
# the eyeball: the dark glossy part of the eye pieces (the lids around it are skin and take the ramp)
dark = ndimage.binary_closing(eye_piece & (_raw < 0.16), iterations=4)
lab, n = ndimage.label(dark)
sizes = ndimage.sum(dark, lab, range(1, n + 1))
eye = np.isin(lab, [i + 1 for i, a in enumerate(sizes) if a > 3000])   # the eyeballs, not the lid creases
eye = ndimage.binary_fill_holes(ndimage.binary_dilation(eye, iterations=2)) & eye_piece
print('EYEBALL blobs', sorted(int(a) for a in sizes if a > 3000))


def save(array, path, size=None, mode=None):
    image = Image.fromarray(np.clip(array * 255 + 0.5, 0, 255).astype(np.uint8), mode)
    if size:
        image = image.resize((size, size), Image.LANCZOS)
    image.save(path, optimize=True)


base = Image.open(f'{SRC}_base_color.png').convert('RGB').resize((2048, 2048), Image.LANCZOS)
base.save(OUT / 'toad_basecolor.png', optimize=True)
Image.open(f'{SRC}_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS).save(OUT / 'toad_normal_1k.png')
rough = np.asarray(Image.open(f'{SRC}_roughness.png').convert('L').resize((1024, 1024), Image.LANCZOS)) / 255.0
ao = np.asarray(Image.open(OUT / 'toad_ao_2k.png').convert('L').resize((1024, 1024), Image.LANCZOS)) / 255.0
rough = np.clip(rough, 0.55, 0.95)
orm = np.stack([ao, rough, np.zeros_like(ao)], -1)
save(orm, OUT / 'toad_mr_1k.png')

# region mask: skin = every island texel but the eyes, feathered 2 texels, then padded into the gutters
skin = (1.0 - ndimage.gaussian_filter(eye.astype(np.float32), 1.0)) * valid   # feathered only at the eyeballs
skin[eye] = 0.0
interior = valid
_, (iy, ix) = ndimage.distance_transform_edt(~interior, return_indices=True)
padded = skin[iy, ix]
padded[interior] = skin[interior]
# the gutter next to an eye island must not take the ramp either
eye_pad = eye[iy, ix]
padded[~interior & eye_pad] = 0.0
mask = np.zeros((2048, 2048, 4), np.float32)
mask[..., 0] = padded
chans = [Image.fromarray((mask[..., c] * 255 + 0.5).astype(np.uint8), 'L').resize((1024, 1024), Image.LANCZOS)
         for c in range(4)]                                # per channel: an RGBA resize premultiplies by alpha 0
Image.merge('RGBA', chans).save(OUT / 'toad_region_mask.png')
np.save(ROOT / 'work/skin_weight_2k.npy', padded)

classes = np.zeros((2048, 2048), np.uint8)
classes[valid] = 1
classes[eye] = 6
Image.fromarray(classes, 'L').resize((1024, 1024), Image.NEAREST).save(OUT / 'toad_material_classes.png')

# tongue: v along the tongue (0 root .. 1 tip), u around
v = np.linspace(0, 1, 256)[:, None]
u = np.linspace(0, 1, 256)[None, :]
root = np.array([0.30, 0.55, 0.58]); tip = np.array([0.42, 0.86, 0.84])
col = root + (tip - root) * v[..., None]
col = col * (0.88 + 0.12 * np.cos(2 * np.pi * u[..., None] * 3)) * (0.9 + 0.1 * np.cos(2 * np.pi * u[..., None]))
save(col[::-1], OUT / 'toad_tongue.png')
print('COMPOSED skin texels', int((padded > 0.5).sum()), 'eye texels', int(eye.sum()))
