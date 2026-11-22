#!/usr/bin/env python3
"""Armadillo texture set from the Meshy retexture (meshy/retexture_v1: 4K paint on our uv_atlas layout from the four
Codex HD masters). Run after scripts/dump_uv3d.py and scripts/bake_ao.py; grade, ramps and gutter fill follow in
build_runtime.sh.

Writes into textures/:
  dillo_basecolor.png          2K base colour (4K Meshy paint downsampled once, Lanczos); the tail-ball spikes and the
                               forked tongue are painted here procedurally (Meshy painted them as pale specks)
  dillo_normal_1k.png          Meshy normal (+y down; tools/prepare_actor_glb.py converts it); flat on spikes/tongue
  dillo_mr_1k.png              ORM: R baked AO, G roughness (Meshy, clamped per class), B 0
  dillo_region_mask.png        1K RGBA: R red armour and hide (shell, head, legs, tail, ball and spikes), G pale skin
                               (belly bands and the pale plate undersides), B claws, A eyes + tongue. The dark mouth and
                               nostrils are in no region. Padded into the gutters.
  dillo_material_classes.png   1K labels: 1 hide (armour and skin), 4 claw/spike, 6 eye, 7 tongue
Classes per texel from the paint (pale pink = low saturation in the red hues, grey claws = low saturation) limited by
geometry: claws only on the Hand/HindFoot bones, eyes only the orange-yellow texels on the Head, spikes = part 2,
tongue = part 3."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'mm6_gob_claude' / 'scripts'))
import compose_textures_v2 as C   # noqa: E402  (rasterise: 2048 label/xyz maps)
import json

SRC = ROOT / 'meshy/retexture_v1/texture_urls_0'
OUT = ROOT / 'textures'
N = 2048
data = np.load(ROOT / 'work/uv3d.npz')
parts = json.load(open(ROOT / 'work/parts.json'))
bones = [str(b) for b in data['bones']]
label, xyz = C.rasterise(data, values=data['bone'] * 8 + data['mpart'])
valid = label >= 0
bone_map = np.where(valid, label // 8, -1); mpart = np.where(valid, label % 8, -1)
bidx = {b: i for i, b in enumerate(bones)}


def on(*names):
    return np.isin(bone_map, [bidx[n] for n in names if n in bidx])


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
rng = np.random.default_rng(5)

feet = on('Hand_L', 'Hand_R', 'HindFoot_L', 'HindFoot_R')
head = on('Head', 'Neck')
spikes = valid & (mpart == 2)
tongue = valid & (mpart == 3)
reddish = (hue < 30) | (hue > 330)
pale0 = valid & reddish & (sat < 0.45) & (mx > 0.55) & ~spikes & ~tongue
palefrac = ndimage.gaussian_filter(pale0.astype(np.float32), 4.0) / np.maximum(
    ndimage.gaussian_filter(valid.astype(np.float32), 4.0), 1e-3)
pale = valid & (palefrac > 0.45) & ~spikes & ~tongue      # whole pale bands, not the paint's pale speckles
grey = valid & (sat < 0.2) & (mx > 0.28)
claws = valid & feet & ndimage.binary_closing(grey, iterations=1)
eye = valid & head & (hue > 25) & (hue < 70) & (sat > 0.4) & (mx > 0.45)
eye = ndimage.binary_closing(eye, iterations=2) & valid & head
eye |= valid & head & ndimage.binary_dilation(eye, iterations=2) & (mx < 0.2)     # pupils and lid creases
dark = valid & head & (mx < 0.15) & ~eye                                          # mouth and nostrils: no region

# ---- procedural paint: spikes (the ball's own red, darker toward the tip) and the green forked tongue
ball = valid & on('TailBall') & ~pale
ball_col = np.median(rgb[ball], 0)
bc = np.array(parts['ball_centre'], np.float32); br = parts['ball_radius']
t = np.clip((np.linalg.norm(xyz - bc, axis=-1) / br - 0.85) / 1.45, 0, 1)
noise = ndimage.gaussian_filter(rng.normal(0, 1, (N, N)).astype(np.float32), 1.2) * 0.06
spike_col = ball_col[None, None, :] * (1.0 - 0.45 * t[..., None] + noise[..., None])
rgb = np.where(spikes[..., None], np.clip(spike_col, 0, 1), rgb)
tr = np.array(parts['tongue_root'], np.float32)
tt = np.clip(np.linalg.norm(xyz - tr, axis=-1) / parts['tongue_length'], 0, 1)
tongue_col = np.array([0.14, 0.52, 0.10], np.float32)   # darker than the iris: channel A ramps black pupil -> green -> orange[None, None, :] * (1.0 - 0.25 * tt[..., None] + noise[..., None])
rgb = np.where(tongue[..., None], np.clip(tongue_col, 0, 1), rgb)
Image.fromarray((rgb * 255 + 0.5).astype(np.uint8)).save(OUT / 'dillo_basecolor.png', optimize=True)

paleskin = pale & ~claws & ~eye & ~dark
armour = valid & ~paleskin & ~claws & ~eye & ~dark & ~tongue
# small specks: a class on fewer than 30 connected texels takes its surroundings' class
for cls in (claws, paleskin):
    lab, n = ndimage.label(cls)
    sizes = ndimage.sum(cls, lab, range(1, n + 1))
    small = np.isin(lab, [i + 1 for i, a in enumerate(sizes) if a < 30])
    cls[small] = False
    armour |= small
eyetongue = eye | tongue
print('CLASSES texels', {'armour': int(armour.sum()), 'pale': int(paleskin.sum()), 'claws': int(claws.sum()),
                         'eye': int(eye.sum()), 'tongue': int(tongue.sum()), 'spikes': int(spikes.sum()),
                         'dark': int(dark.sum()), 'valid': int(valid.sum())})

chan = [armour, paleskin, claws, eyetongue]
_, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
mask = np.zeros((N, N, 4), np.float32)
for c, sel in enumerate(chan):
    w = ndimage.gaussian_filter(sel.astype(np.float32), 0.8)
    w[dark] = 0.0
    w = w * valid
    padded = w[iy, ix]; padded[valid] = w[valid]
    mask[..., c] = padded
mask[~valid & dark[iy, ix]] = 0.0
total = mask.sum(-1, keepdims=True)
mask = np.where(total > 1.0, mask / np.maximum(total, 1e-6), mask)
chans = [Image.fromarray((mask[..., c] * 255 + 0.5).astype(np.uint8), 'L').resize((1024, 1024), Image.LANCZOS)
         for c in range(4)]
Image.merge('RGBA', chans).save(OUT / 'dillo_region_mask.png')

normal = np.asarray(Image.open(f'{SRC}_normal.png').convert('RGB').resize((N, N), Image.LANCZOS), np.float32)
flat = np.array([128, 128, 255], np.float32)
normal = np.where((spikes | tongue)[..., None], flat, normal)
Image.fromarray(normal.astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(OUT / 'dillo_normal_1k.png')
rough = np.asarray(Image.open(f'{SRC}_roughness.png').convert('L').resize((N, N), Image.LANCZOS)) / 255.0
rough = np.where(claws | spikes, np.clip(rough, 0.35, 0.7),
                 np.where(eye, 0.25, np.where(tongue, 0.35, np.clip(rough, 0.55, 0.92))))
ao = np.asarray(Image.open(OUT / 'dillo_ao_2k.png').convert('L'), np.float32) / 255.0
orm = np.stack([ao, rough, np.zeros_like(ao)], -1)
Image.fromarray((orm * 255 + 0.5).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(OUT / 'dillo_mr_1k.png')

classes = np.zeros((N, N), np.uint8)
classes[valid] = 1
classes[claws | spikes] = 4
classes[eye] = 6
classes[tongue] = 7
Image.fromarray(classes, 'L').resize((1024, 1024), Image.NEAREST).save(OUT / 'dillo_material_classes.png')
pv = np.zeros((N, N, 3), np.uint8)
for sel, col in ((armour, (200, 40, 40)), (paleskin, (240, 170, 170)), (claws, (150, 150, 150)), (spikes, (120, 0, 0)),
                 (eye, (255, 200, 0)), (tongue, (0, 200, 0)), (dark, (0, 0, 0))):
    pv[sel] = col
Image.fromarray(pv).resize((1024, 1024), Image.NEAREST).save(ROOT / 'review' / 'region_classes.png')
print('COMPOSED')
