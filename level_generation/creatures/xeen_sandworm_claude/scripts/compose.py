#!/usr/bin/env python3
"""Sand worm texture set from the Meshy retexture (meshy/retexture_v1: 4K paint on our uv_atlas layout from the four
Codex HD masters). Run after scripts/dump_uv3d.py and scripts/bake_ao.py; grade, ramps and gutter fill follow in
build_runtime.sh.

Writes into textures/:
  worm_basecolor.png          2K base colour (4K Meshy paint downsampled once, Lanczos)
  worm_normal_1k.png          Meshy normal (+y down; tools/prepare_actor_glb.py converts it)
  worm_mr_1k.png              ORM: R baked AO, G roughness (Meshy, clamped per class), B 0
  worm_region_mask.png        1K RGBA: R the body skin (rings and head), G the thorn spikes, B the maw's gums,
                              A the sand mound; padded into the gutters. The fangs, the black gullet and the rock
                              chunks are in no region (they keep their paint in every skin: one luminance ramp would
                              turn the pink-brown rocks the sand's tan)
  worm_material_classes.png   1K labels: 1 skin, 4 spike, 5 fang, 7 gums and gullet, 11 sand and rock (other)
Classes per texel from geometry (mesh part: rings, head, spikes, fangs, mound, rocks; the maw region from the rig's
maw frame) and, inside the maw, the paint (red gums, dark gullet)."""
import json, sys
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
RJ = json.load(open(ROOT / 'work/rig_v1.json'))
mc = np.array(RJ['maw']['centre']); mn = np.array(RJ['maw']['normal']); rim = RJ['maw']['rim']

base = Image.open(f'{SRC}_base_color.png').convert('RGB').resize((N, N), Image.LANCZOS)
rgb = np.asarray(base, np.float32) / 255.0
mx = rgb.max(-1); mnc = rgb.min(-1); d = mx - mnc
sat = np.where(mx > 1e-4, d / np.maximum(mx, 1e-4), 0)
h = np.zeros_like(mx)
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
m = d > 1e-5
hr = m & (mx == r); hg = m & (mx == g) & ~hr; hb = m & ~hr & ~hg
h[hr] = ((g - b)[hr] / d[hr]) % 6; h[hg] = (b - r)[hg] / d[hg] + 2; h[hb] = (r - g)[hb] / d[hb] + 4
hue = h * 60

rel = xyz - mc
hn = rel @ mn
rho = np.linalg.norm(rel - hn[..., None] * mn, axis=-1)
head = valid & (label == 1)
in_maw = head & (rho < 1.12 * rim) & (hn > -0.25) & (hn < 0.05)
red = ((hue < 22) | (hue > 330)) & (sat > 0.35)
dark = mx < 0.13
gullet = in_maw & (dark | (hn < -0.06) & (mx < 0.22))
# gums: red paint inside the rim, smoothed by neighbourhood so the cracks between gum folds stay in
gf = ndimage.gaussian_filter((in_maw & red).astype(np.float32), 2.0) / np.maximum(
    ndimage.gaussian_filter(in_maw.astype(np.float32), 2.0), 1e-3)
gums = in_maw & ~gullet & ((gf > 0.45) | red)
skin = valid & np.isin(label, (0, 1)) & ~gums & ~gullet
spikes = valid & (label == 2)
fangs = valid & (label == 3)
sand = valid & (label == 4)
rocks = valid & (label == 5)
col = rgb.copy()
Image.fromarray((np.clip(col, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT / 'worm_basecolor.png', optimize=True)
print('CLASSES texels', {'skin': int(skin.sum()), 'spikes': int(spikes.sum()), 'gums': int(gums.sum()),
                         'gullet': int(gullet.sum()), 'fangs': int(fangs.sum()), 'sand': int(sand.sum()), 'rocks': int(rocks.sum()),
                         'valid': int(valid.sum())})

chan = [skin, spikes, gums, sand]
_, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
mask = np.zeros((N, N, 4), np.float32)
keep_out = fangs | gullet | rocks
for c, sel in enumerate(chan):
    w = ndimage.gaussian_filter(sel.astype(np.float32), 0.8) * valid
    w[keep_out] = 0.0
    padded = w[iy, ix]; padded[valid] = w[valid]
    mask[..., c] = padded
mask[~valid & keep_out[iy, ix]] = 0.0
total = mask.sum(-1, keepdims=True)
mask = np.where(total > 1.0, mask / np.maximum(total, 1e-6), mask)
chans = [Image.fromarray((mask[..., c] * 255 + 0.5).astype(np.uint8), 'L').resize((1024, 1024), Image.LANCZOS)
         for c in range(4)]
Image.merge('RGBA', chans).save(OUT / 'worm_region_mask.png')

Image.open(f'{SRC}_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS).save(OUT / 'worm_normal_1k.png')
rough = np.asarray(Image.open(f'{SRC}_roughness.png').convert('L').resize((N, N), Image.LANCZOS)) / 255.0
rough = np.where(skin, np.clip(rough, 0.6, 0.92), rough)
rough = np.where(spikes, np.clip(rough, 0.35, 0.6), rough)
rough = np.where(fangs, np.clip(rough, 0.35, 0.55), rough)
rough = np.where(gums | gullet, np.clip(rough, 0.35, 0.6), rough)
rough = np.where(sand | rocks, np.clip(rough, 0.8, 0.98), rough)
ao = np.asarray(Image.open(OUT / 'worm_ao_2k.png').convert('L'), np.float32) / 255.0
orm = np.stack([ao, rough, np.zeros_like(ao)], -1)
Image.fromarray((orm * 255 + 0.5).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(OUT / 'worm_mr_1k.png')

classes = np.zeros((N, N), np.uint8)
classes[skin] = 1; classes[spikes] = 4; classes[fangs] = 5; classes[gums | gullet] = 7; classes[sand | rocks] = 11
Image.fromarray(classes, 'L').resize((1024, 1024), Image.NEAREST).save(OUT / 'worm_material_classes.png')
pv = np.zeros((N, N, 3), np.uint8)
for sel, c in ((skin, (230, 130, 30)), (spikes, (120, 120, 140)), (gums, (220, 20, 40)), (gullet, (20, 20, 20)),
               (fangs, (250, 250, 250)), (sand, (200, 180, 120)), (rocks, (150, 90, 90))):
    pv[sel] = c
Image.fromarray(pv).resize((1024, 1024), Image.NEAREST).save(ROOT / 'review' / 'region_classes.png')
print('COMPOSED')
