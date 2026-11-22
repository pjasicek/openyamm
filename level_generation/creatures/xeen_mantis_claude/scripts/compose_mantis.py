#!/usr/bin/env python3
"""Mantis texture set from the Meshy retexture (meshy/retexture_v1: 4K paint on our uv_atlas layout from the four
Codex HD masters). Run after scripts/dump_uv3d.py and scripts/bake_ao.py; grade, ramps and gutter fill follow in
build_runtime.sh.

Writes into textures/:
  mantis_basecolor.png          2K base colour (4K Meshy paint downsampled once, Lanczos)
  mantis_normal_1k.png          Meshy normal (+y down; tools/prepare_actor_glb.py converts it)
  mantis_mr_1k.png              ORM: R baked AO, G roughness (Meshy, clamped per class), B 0
  mantis_region_mask.png        1K RGBA: R chitin, G ball joints (hips, knees, shoulders, elbows), B eyes,
                                A underside (charcoal abdomen front) and the radial mouth (yellow petals). The red
                                abdomen tip and the dark mouth centre are in no region (they keep the paint in every
                                skin). Padded into the gutters.
  mantis_material_classes.png   1K labels: 4 chitin / joints / underside, 5 mouth petals, 6 eye
Classes per texel from the Smart Topology piece (face attribute `piece`, prep.py numbering) and the paint's hue:
joints are whole ball pieces; eyes are the teal texels of the four eye pieces; the mouth is the yellow-orange texels
of the mouth disc and its ten beads; the underside is the grey-black texels (abdomen front and hip ring), the red tip the red ones; everything else is
chitin, so stray teal or yellow specks Meshy painted elsewhere take the chitin ramp."""
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
JOINTS = [27, 29, 30, 31, 32, 33, 34, 35, 38, 42, 52, 53, 48]
EYES = [10, 21, 12, 23]
MOUTH = [15, 39, 40, 43, 44, 45, 46, 47, 49, 50, 51]
ABDOMEN = [6]

data = np.load(ROOT / 'work/uv3d.npz')
label, xyz = C.rasterise(data, values=data['mpart'])
valid = label >= 0
piece = np.where(valid, label, -1)


def on(ps):
    return valid & np.isin(piece, ps)


base = Image.open(f'{SRC}_base_color.png').convert('RGB').resize((N, N), Image.LANCZOS)
base.save(OUT / 'mantis_basecolor.png', optimize=True)
rgb = np.asarray(base, np.float32) / 255.0
mx = rgb.max(-1); mn = rgb.min(-1); d = mx - mn
sat = np.where(mx > 1e-4, d / np.maximum(mx, 1e-4), 0)
h = np.zeros_like(mx)
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
m = d > 1e-5
hr = m & (mx == r); hg = m & (mx == g) & ~hr; hb = m & ~hr & ~hg
h[hr] = ((g - b)[hr] / d[hr]) % 6; h[hg] = (b - r)[hg] / d[hg] + 2; h[hb] = (r - g)[hb] / d[hb] + 4
hue = h * 60

teal = (hue > 140) & (hue < 215) & (sat > 0.22)
yellow = (hue > 22) & (hue < 72) & (sat > 0.35) & (mx > 0.22)
red = ((hue < 22) | (hue > 345)) & (sat > 0.45) & (mx > 0.18)
purple = (hue > 245) & (hue < 335) & (sat > 0.25)
greyblack = (sat < 0.32) | (mx < 0.16)

eye = on(EYES) & teal
eye = ndimage.binary_closing(eye, iterations=2) & on(EYES)
mouth = on(MOUTH) & yellow
mouth = ndimage.binary_closing(mouth, iterations=1) & on(MOUTH)
body = valid & ~on(EYES) & ~on(MOUTH) & ~on(JOINTS)
tip = body & red & ~purple
tip = ndimage.binary_closing(tip, iterations=2) & body
under = body & greyblack & ~purple & ~tip
under = ndimage.binary_opening(under, iterations=1)
mouth_dark = on(MOUTH) & ~mouth & ~purple            # the dark centre of the radial mouth
joints = on(JOINTS)
chitin = valid & ~eye & ~mouth & ~tip & ~under & ~mouth_dark & ~joints


def drop_specks(cls, into, minimum=60):
    lab, n = ndimage.label(cls)
    if n == 0:
        return
    sizes = ndimage.sum(cls, lab, range(1, n + 1))
    small = np.isin(lab, [i + 1 for i, a in enumerate(sizes) if a < minimum])
    cls[small] = False
    into |= small


drop_specks(under, chitin, 200)
drop_specks(tip, chitin, 40)
print('CLASSES texels', {'chitin': int(chitin.sum()), 'joints': int(joints.sum()), 'eye': int(eye.sum()),
                         'mouth': int(mouth.sum()), 'under': int(under.sum()), 'tip': int(tip.sum()),
                         'mouth_dark': int(mouth_dark.sum()), 'valid': int(valid.sum())})

chan = [chitin, joints, eye, under | mouth]
none = tip | mouth_dark
_, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
mask = np.zeros((N, N, 4), np.float32)
for c, sel in enumerate(chan):
    w = ndimage.gaussian_filter(sel.astype(np.float32), 0.8)
    w[none] = 0.0
    w = w * valid
    padded = w[iy, ix]; padded[valid] = w[valid]
    mask[..., c] = padded
none_pad = none[iy, ix]
mask[~valid & none_pad] = 0.0
total = mask.sum(-1, keepdims=True)
mask = np.where(total > 1.0, mask / np.maximum(total, 1e-6), mask)
chans = [Image.fromarray((mask[..., c] * 255 + 0.5).astype(np.uint8), 'L').resize((1024, 1024), Image.LANCZOS)
         for c in range(4)]
Image.merge('RGBA', chans).save(OUT / 'mantis_region_mask.png')

Image.open(f'{SRC}_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS).save(OUT / 'mantis_normal_1k.png')
rough = np.asarray(Image.open(f'{SRC}_roughness.png').convert('L').resize((N, N), Image.LANCZOS)) / 255.0
rough = np.where(eye, 0.2, np.where(mouth, np.clip(rough, 0.45, 0.8), np.clip(rough, 0.35, 0.8)))
ao = np.asarray(Image.open(OUT / 'mantis_ao_2k.png').convert('L'), np.float32) / 255.0
orm = np.stack([ao, rough, np.zeros_like(ao)], -1)
Image.fromarray((orm * 255 + 0.5).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(OUT / 'mantis_mr_1k.png')

classes = np.zeros((N, N), np.uint8)
classes[valid] = 4
classes[mouth | mouth_dark] = 5
classes[eye] = 6
Image.fromarray(classes, 'L').resize((1024, 1024), Image.NEAREST).save(OUT / 'mantis_material_classes.png')
pv = np.zeros((N, N, 3), np.uint8)
for sel, col in ((chitin, (150, 40, 200)), (joints, (255, 140, 0)), (eye, (0, 220, 220)), (mouth, (255, 230, 0)),
                 (under, (60, 60, 60)), (tip, (220, 0, 0)), (mouth_dark, (255, 255, 255))):
    pv[sel] = col
Image.fromarray(pv).resize((1024, 1024), Image.NEAREST).save(ROOT / 'review' / 'region_classes.png')
# Lava Roach glow (emission mask; the colour is per skin, only mantis_lava emits: build_runtime.sh): the ball joints
# glow brightest in their crevices where they meet the limbs, the eyes, and the cracks of the thorax front (the
# sprite's burning chest).
lum = rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)
local = ndimage.gaussian_filter(lum, 6.0)
crack = np.clip(((local - lum) / np.maximum(local, 0.05) - 0.08) / 0.25, 0, 1)
chest = on([0]) & (xyz[..., 1] < -0.2) & (xyz[..., 2] < 0.74)
aoc = np.clip((0.92 - np.asarray(Image.open(OUT / 'mantis_ao_2k.png').convert('L'), np.float32) / 255.0) / 0.35, 0, 1)
glow = np.maximum.reduce([joints * (0.30 + 0.70 * np.maximum(aoc, crack)), eye * 0.9, chest * crack * 0.85])
glow = ndimage.gaussian_filter(glow.astype(np.float32), 0.8) * valid
gp = glow[iy, ix]; gp[valid] = glow[valid]
Image.fromarray((np.clip(gp, 0, 1) * 255 + 0.5).astype(np.uint8), 'L').resize((1024, 1024), Image.LANCZOS).save(
    OUT / 'mantis_emission_mask.png')
print('GLOW share of the surface', round(float(glow[valid].mean()), 4))
print('COMPOSED')
