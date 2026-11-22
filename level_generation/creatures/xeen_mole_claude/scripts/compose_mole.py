#!/usr/bin/env python3
"""Mole texture set from the Meshy retexture (meshy/retexture_v1: 4K paint on our uv_atlas layout from the four
Codex HD masters). Run after scripts/dump_uv3d.py and scripts/bake_ao.py; grade, ramps and gutter fill follow in
build_runtime.sh.

Writes into textures/:
  mole_basecolor.png          2K base colour (4K Meshy paint downsampled once, Lanczos)
  mole_normal_1k.png          Meshy normal (+y down; tools/prepare_actor_glb.py converts it)
  mole_mr_1k.png              ORM: R baked AO, G roughness (Meshy, clamped per class), B 0
  mole_region_mask.png        1K RGBA: R fur, G naked skin (hands, snout, eye lids), B claws (hand claws and the hind
                              toe claws), A tail; the eyeballs (red irises) are in no region. Padded into the gutters.
  mole_material_classes.png   1K labels: 1 skin, 2 fur, 4 claw, 6 eye
Classes per texel from the paint's hue (teal fur, yellow-olive claws, pale pink-grey skin), limited by geometry:
claws only on hand/claw bones and the hind claw pieces, eyes only on the eyeball pieces and the head, the tail piece
wholly A."""
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
bones = [str(b) for b in data['bones']]
code = data['bone'] * 8 + data['mpart']
label, xyz = C.rasterise(data, values=code)
valid = label >= 0
bone_map = np.where(valid, label // 8, -1); mpart = np.where(valid, label % 8, -1)
bidx = {b: i for i, b in enumerate(bones)}


def on(*names):
    return np.isin(bone_map, [bidx[n] for n in names if n in bidx])


base = Image.open(f'{SRC}_base_color.png').convert('RGB').resize((N, N), Image.LANCZOS)
base.save(OUT / 'mole_basecolor.png', optimize=True)
rgb = np.asarray(base, np.float32) / 255.0
mx = rgb.max(-1); mn = rgb.min(-1); d = mx - mn
sat = np.where(mx > 1e-4, d / np.maximum(mx, 1e-4), 0)
h = np.zeros_like(mx)
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
m = d > 1e-5
hr = m & (mx == r); hg = m & (mx == g) & ~hr; hb = m & ~hr & ~hg
h[hr] = ((g - b)[hr] / d[hr]) % 6; h[hg] = (b - r)[hg] / d[hg] + 2; h[hb] = (r - g)[hb] / d[hb] + 4
hue = h * 60

hand = on('Hand_L', 'Hand_R', 'Claws_L', 'Claws_R', 'ForeArm_L', 'ForeArm_R')
head = on('Head', 'Snout', 'Chest')
fur0 = (hue > 150) & (hue < 235) & (sat > 0.12)
# hair highlights are pale: a texel is fur where most of its neighbourhood is (sigma 3 texels at 2K)
furfrac = ndimage.gaussian_filter(fur0.astype(np.float32), 3.0) / np.maximum(
    ndimage.gaussian_filter(valid.astype(np.float32), 3.0), 1e-3)
fur = fur0 | (furfrac > 0.55)
clawc = (hue > 38) & (hue < 85) & (sat > 0.35) & (mx > 0.18)
redc = ((hue < 18) | (hue > 340)) & (sat > 0.5) & (mx > 0.2)
skin = ~fur & ~clawc & ~redc
claws = valid & ((clawc & hand) | (mpart == 2))
nose = valid & redc & head & (xyz[..., 1] < -0.62)          # the pink snout tip keeps its paint in every tier
eye = valid & ((mpart == 1) | (redc & head & (xyz[..., 1] >= -0.62)))
eye = ndimage.binary_closing(eye, iterations=2) & valid & (head | (mpart == 1))
# dark pupils and lid creases next to the red iris
eye |= valid & ndimage.binary_dilation(eye, iterations=2) & (mx < 0.12) & (head | (mpart == 1))
tail = valid & (mpart == 3)
furm = valid & fur & ~eye & ~tail & ~claws & ~nose
skinm = valid & ~furm & ~eye & ~tail & ~claws & ~nose
# small specks: a hue class on fewer than 40 connected texels takes its surroundings' class
for _ in range(1):
    for cls, other in ((claws, None), (skinm, None)):
        lab, n = ndimage.label(cls)
        sizes = ndimage.sum(cls, lab, range(1, n + 1))
        small = np.isin(lab, [i + 1 for i, a in enumerate(sizes) if a < 40]) & (mpart != 2)
        cls[small] = False
        furm |= small & fur
        skinm |= small & ~fur
print('CLASSES texels', {'fur': int(furm.sum()), 'skin': int(skinm.sum()), 'claws': int(claws.sum()),
                         'tail': int(tail.sum()), 'eye': int(eye.sum()), 'nose': int(nose.sum()), 'valid': int(valid.sum())})

chan = [furm, skinm, claws, tail]
_, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
mask = np.zeros((N, N, 4), np.float32)
for c, sel in enumerate(chan):
    w = ndimage.gaussian_filter(sel.astype(np.float32), 0.8)
    w[eye | nose] = 0.0
    w = w * valid
    padded = w[iy, ix]; padded[valid] = w[valid]
    mask[..., c] = padded
eye_pad = (eye | nose)[iy, ix]
mask[~valid & eye_pad] = 0.0
total = mask.sum(-1, keepdims=True)
mask = np.where(total > 1.0, mask / np.maximum(total, 1e-6), mask)
chans = [Image.fromarray((mask[..., c] * 255 + 0.5).astype(np.uint8), 'L').resize((1024, 1024), Image.LANCZOS)
         for c in range(4)]
Image.merge('RGBA', chans).save(OUT / 'mole_region_mask.png')

Image.open(f'{SRC}_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS).save(OUT / 'mole_normal_1k.png')
rough = np.asarray(Image.open(f'{SRC}_roughness.png').convert('L').resize((N, N), Image.LANCZOS)) / 255.0
rough = np.where(claws, np.clip(rough, 0.40, 0.75), np.where(eye, 0.25, np.clip(rough, 0.6, 0.95)))
ao = np.asarray(Image.open(OUT / 'mole_ao_2k.png').convert('L'), np.float32) / 255.0
orm = np.stack([ao, rough, np.zeros_like(ao)], -1)
Image.fromarray((orm * 255 + 0.5).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(OUT / 'mole_mr_1k.png')

classes = np.zeros((N, N), np.uint8)
classes[valid] = 1
classes[furm] = 2
classes[claws] = 4
classes[eye] = 6
Image.fromarray(classes, 'L').resize((1024, 1024), Image.NEAREST).save(OUT / 'mole_material_classes.png')
# preview of the classes
pv = np.zeros((N, N, 3), np.uint8)
for sel, col in ((furm, (40, 140, 150)), (skinm, (230, 190, 190)), (claws, (220, 210, 0)), (tail, (90, 90, 255)),
                 (eye, (255, 0, 0)), (nose, (255, 120, 200))):
    pv[sel] = col
Image.fromarray(pv).resize((1024, 1024), Image.NEAREST).save(ROOT / 'review' / 'region_classes.png')
print('COMPOSED')
