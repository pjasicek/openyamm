#!/usr/bin/env python3
"""Electrapede texture set from the Meshy retexture (meshy/retexture_v1: 4K paint on our uv_atlas layout from the four
Codex HD masters). Run after scripts/dump_uv3d.py and scripts/bake_ao.py; grade, ramps and gutter fill follow in
build_runtime.sh.

Writes into textures/:
  pede_basecolor.png          2K base colour (4K Meshy paint downsampled once, Lanczos); the procedural legs get dark
                              joint bands (hip, knee) and a dark foot tip in luminance, as the native legs have
  pede_normal_1k.png          Meshy normal (+y down; tools/prepare_actor_glb.py converts it)
  pede_mr_1k.png              ORM: R baked AO, G roughness (Meshy, clamped per class), B 0
  pede_region_mask.png        1K RGBA: R the green plates and head, G legs, antennae and the leg sockets
                              (magenta-violet), B the compound eyes, A the dark slate underside; padded into the gutters
  pede_material_classes.png   1K labels: 1 chitin (plates, head, legs), 6 eye, 7 mouth interior
Classes per texel from geometry (mesh part: eyes, legs, antennae) and, on the plates and head, the paint's hue (slate
underside vs green; magenta socket rings)."""
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

legs = valid & np.isin(label, (3, 4))
eyes = valid & (label == 2)
shell = valid & np.isin(label, (0, 1, 5, 6))
magenta = (hue > 265) & (hue < 345) & (sat > 0.3)
slate = (hue > 135) & (hue < 250) & (mx < 0.45) & (sat < 0.85)      # the belly paint: dark teal-slate, hue ~157
sock = shell & magenta & (label == 5)
under = shell & slate & ~sock
# slate specks on the plates' tops and green specks on the belly: smooth the class by its neighbourhood
uf = ndimage.gaussian_filter(under.astype(np.float32), 2.0) / np.maximum(ndimage.gaussian_filter(shell.astype(np.float32), 2.0), 1e-3)
under = shell & (uf > 0.5) & ~sock
green = shell & ~under & ~sock
# mouth interior: dark texels on the jaw / mouth front (kept out of every region: they keep their paint)
mouth = shell & (label == 1) & (mx < 0.10) & (xyz[..., 1] < -1.08)
green &= ~mouth; under &= ~mouth

# leg joint bands in luminance (native legs: magenta with dark purple joints)
col = rgb.copy()
LI = np.nonzero(legs); PL = xyz[LI]
bl = np.zeros(len(PL), np.float32)
for l in RJ['legs']:
    for p, rad, k in ((l['hip'], 0.022, 0.55), (l['knee'], 0.020, 0.50), (l['foot'], 0.045, 0.45)):
        dd = np.linalg.norm(PL - np.array(p, np.float32), axis=-1)
        bl = np.maximum(bl, k * np.clip(1 - dd / rad, 0, 1))
band = np.zeros((N, N), np.float32); band[LI] = bl
col *= (1 - band)[..., None]
Image.fromarray((np.clip(col, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT / 'pede_basecolor.png', optimize=True)
print('CLASSES texels', {'green': int(green.sum()), 'under': int(under.sum()), 'legs': int(legs.sum()),
                         'sockets': int(sock.sum()), 'eyes': int(eyes.sum()), 'mouth': int(mouth.sum()), 'valid': int(valid.sum())})

chan = [green, legs | sock, eyes, under]
_, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
mask = np.zeros((N, N, 4), np.float32)
for c, sel in enumerate(chan):
    w = ndimage.gaussian_filter(sel.astype(np.float32), 0.8) * valid
    w[mouth] = 0.0
    padded = w[iy, ix]; padded[valid] = w[valid]
    mask[..., c] = padded
mask[~valid & mouth[iy, ix]] = 0.0
total = mask.sum(-1, keepdims=True)
mask = np.where(total > 1.0, mask / np.maximum(total, 1e-6), mask)
chans = [Image.fromarray((mask[..., c] * 255 + 0.5).astype(np.uint8), 'L').resize((1024, 1024), Image.LANCZOS)
         for c in range(4)]
Image.merge('RGBA', chans).save(OUT / 'pede_region_mask.png')

Image.open(f'{SRC}_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS).save(OUT / 'pede_normal_1k.png')
rough = np.asarray(Image.open(f'{SRC}_roughness.png').convert('L').resize((N, N), Image.LANCZOS)) / 255.0
rough = np.where(eyes, 0.22, np.clip(rough, 0.35, 0.75))            # glossy chitin, glassy compound eyes
ao = np.asarray(Image.open(OUT / 'pede_ao_2k.png').convert('L'), np.float32) / 255.0
orm = np.stack([ao, rough, np.zeros_like(ao)], -1)
Image.fromarray((orm * 255 + 0.5).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(OUT / 'pede_mr_1k.png')

classes = np.zeros((N, N), np.uint8)
classes[valid] = 1
classes[eyes] = 6
classes[mouth] = 7
Image.fromarray(classes, 'L').resize((1024, 1024), Image.NEAREST).save(OUT / 'pede_material_classes.png')
pv = np.zeros((N, N, 3), np.uint8)
for sel, c in ((green, (40, 200, 40)), (under, (40, 80, 90)), (legs, (160, 0, 160)), (sock, (255, 120, 255)),
               (eyes, (255, 0, 255)), (mouth, (255, 255, 0))):
    pv[sel] = c
Image.fromarray(pv).resize((1024, 1024), Image.NEAREST).save(ROOT / 'review' / 'region_classes.png')
print('COMPOSED')
