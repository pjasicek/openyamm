#!/usr/bin/env python3
"""Octopod texture set from the Meshy retexture (meshy/retexture_v1: 4K paint on our uv_atlas layout from the four
Codex HD masters). Run after scripts/dump_uv3d.py and scripts/bake_ao.py; grade, gutter fill and ramps follow in
build_runtime.sh.

Writes into textures/:
  octopod_basecolor.png          2K base colour (4K Meshy paint downsampled once, Lanczos)
  octopod_normal_1k.png          Meshy normal (+y down; tools/prepare_actor_glb.py converts it)
  octopod_mr_1k.png              ORM: R baked AO, G roughness (Meshy, clamped per class), B 0
  octopod_region_mask.png        1K RGBA: R the skin (head, tentacles, the flesh round the eyes), G the suckers (the
                                 sucker pieces and the yellow sucker rings Meshy painted on the tentacles' undersides),
                                 B the irises; A unused. The pupils stay out (black in every skin). Padded into the
                                 gutters.
  octopod_material_classes.png   1K labels: 1 skin, 4 sucker, 6 eye
Classes per texel from geometry (face attribute part: 0 body, 1 sucker piece, 2 eyeball) and, within the body and
the eyeballs, from the paint (yellow rings; blue irises; dark pupils)."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'mm6_gob_claude' / 'scripts'))
import compose_textures_v2 as C   # noqa: E402  (rasterise: 2048 label/xyz maps)

SRC = ROOT / 'meshy/retexture_v1/texture_urls_0'
OUT = ROOT / 'textures'
N = 2048
data = np.load(ROOT / 'work/uv3d.npz')
label, xyz = C.rasterise(data, values=data['mpart'])
valid = label >= 0

base = Image.open(f'{SRC}_base_color.png').convert('RGB').resize((N, N), Image.LANCZOS)
rgb = np.asarray(base, np.float32) / 255.0
mx = rgb.max(-1); mn = rgb.min(-1); d = mx - mn
sat = np.where(mx > 1e-4, d / np.maximum(mx, 1e-4), 0)
h = np.zeros_like(mx)
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
m = d > 1e-5
hr = m & (mx == r); hg = m & (mx == g) & ~hr; hb = m & ~hr & ~hg
h[hr] = ((g - b)[hr] / d[hr]) % 6; h[hg] = (b - r)[hg] / d[hg] + 2; h[hb] = (r - g)[hb] / d[hb] + 4
hue = h * 60

yellow = (hue > 35) & (hue < 85) & (sat > 0.35) & (mx > 0.3)
blue = (hue > 170) & (hue < 260) & (sat > 0.25)
dark = mx < 0.12
body = valid & (label == 0)
# painted sucker rings on the body: yellow by neighbourhood (their dark centres and rims stay with them)
yf = ndimage.gaussian_filter((body & yellow).astype(np.float32), 1.5) / np.maximum(
    ndimage.gaussian_filter(body.astype(np.float32), 1.5), 1e-3)
painted = body & ((yf > 0.45) | yellow)
suckers = (valid & (label == 1)) | painted
eye = valid & (label == 2)
iris = eye & blue
pupil = eye & dark & ~iris
skin = valid & ~suckers & ~iris & ~pupil
col = rgb.copy()
Image.fromarray((np.clip(col, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT / 'octopod_basecolor.png', optimize=True)
print('CLASSES texels', {'skin': int(skin.sum()), 'suckers': int(suckers.sum()), 'painted_rings': int(painted.sum()),
                         'iris': int(iris.sum()), 'pupil': int(pupil.sum()), 'valid': int(valid.sum())})

chan = [skin, suckers, iris]
_, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
mask = np.zeros((N, N, 4), np.float32)
for c, sel in enumerate(chan):
    w = ndimage.gaussian_filter(sel.astype(np.float32), 0.8) * valid
    w[pupil] = 0.0
    padded = w[iy, ix]; padded[valid] = w[valid]
    mask[..., c] = padded
mask[~valid & pupil[iy, ix]] = 0.0
total = mask.sum(-1, keepdims=True)
mask = np.where(total > 1.0, mask / np.maximum(total, 1e-6), mask)
chans = [Image.fromarray((mask[..., c] * 255 + 0.5).astype(np.uint8), 'L').resize((1024, 1024), Image.LANCZOS)
         for c in range(4)]
Image.merge('RGBA', chans).save(OUT / 'octopod_region_mask.png')

Image.open(f'{SRC}_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS).save(OUT / 'octopod_normal_1k.png')
rough = np.asarray(Image.open(f'{SRC}_roughness.png').convert('L').resize((N, N), Image.LANCZOS)) / 255.0
rough = np.where(skin, np.clip(rough, 0.35, 0.62), rough)       # wet glossy skin (the sprite's bright highlights)
rough = np.where(suckers, np.clip(rough, 0.4, 0.65), rough)
rough = np.where(eye, np.clip(rough, 0.1, 0.25), rough)
ao = np.asarray(Image.open(OUT / 'octopod_ao_2k.png').convert('L'), np.float32) / 255.0
orm = np.stack([ao, rough, np.zeros_like(ao)], -1)
Image.fromarray((orm * 255 + 0.5).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(OUT / 'octopod_mr_1k.png')

classes = np.zeros((N, N), np.uint8)
classes[skin] = 1; classes[suckers] = 4; classes[eye] = 6
Image.fromarray(classes, 'L').resize((1024, 1024), Image.NEAREST).save(OUT / 'octopod_material_classes.png')
pv = np.zeros((N, N, 3), np.uint8)
for sel, c in ((skin, (200, 40, 40)), (suckers, (220, 200, 40)), (iris, (40, 90, 230)), (pupil, (10, 10, 10))):
    pv[sel] = c
Image.fromarray(pv).resize((1024, 1024), Image.NEAREST).save(ROOT / 'review' / 'region_classes.png')
print('COMPOSED')
