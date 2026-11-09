#!/usr/bin/env python3
"""Bat A/B/C textures from the Meshy retexture: membrane (Meshy blue) recoloured to the native tier wing colour
(palettes 666 amber / 667 blue / 668 red), body/fur nudged to the native mauve-dark median, eyes/teeth/claws kept.
Meshy's luminance detail is kept in both regions."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'mm6_gob_claude' / 'scripts'))
import compose_textures_v2 as C
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'meshy/retexture_v2/texture_urls_0'          # textured from the Codex HD masters
OUT = ROOT / 'textures'; OUT.mkdir(exist_ok=True)
WING = {'a': (0.471, 0.275, 0.031), 'b': (0.024, 0.176, 0.329), 'c': (0.412, 0.024, 0.063)}
BODY = np.array((0.204, 0.161, 0.208)) * 1.35
WING_GAIN = 1.25
data = np.load(ROOT / 'work/uv3d.npz')
part_map, xyz = C.rasterise(data)
strict, _ = C.rasterise(data, tol=0.0)
interior = ndimage.binary_erosion(strict >= 0, iterations=2)
_, (iy, ix) = ndimage.distance_transform_edt(~interior, return_indices=True)
def pad(a):
    o = a[iy, ix]; o[interior] = a[interior]; return o
base = pad(C.load(str(SRC) + '_base_color.png'))
normal = pad(C.load(str(SRC) + '_normal.png'))
h, s, v = C.hsv(base)
valid = part_map >= 0
lum = base @ np.array([0.2126, 0.7152, 0.0722])
membrane = valid & (h > 170) & (h < 250) & (s > 0.25)
red = valid & ((h < 15) | (h > 340)) & (s > 0.55) & (v > 0.35)             # eyes
light = valid & (v > 0.55) & (s < 0.25)                                    # teeth/claws
body = valid & ~membrane & ~red & ~light
mw = ndimage.gaussian_filter(membrane.astype(np.float32), 1.5) * valid
for tier, wc in WING.items():
    out = base.copy()
    lref = np.median(lum[membrane]); shade = np.clip(lum / lref, 0.3, 2.0)[..., None]
    wing = np.clip(np.array(wc)[None, None] * WING_GAIN * shade, 0, 1)
    bref = np.median(lum[body]); bshade = np.clip(lum / bref, 0.3, 2.2)[..., None]
    bod = np.clip(BODY[None, None] * bshade, 0, 1)
    out = np.where(body[..., None], bod, out)
    out = out * (1 - mw[..., None]) + wing * mw[..., None]
    Image.fromarray(np.clip(pad(out) * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / f'bat_{tier}_basecolor.png', optimize=True)
r = np.full(lum.shape, 0.72, np.float32); r[membrane] = 0.6; r[red] = 0.2; r[light] = 0.35
mr = np.stack([np.ones_like(r), r, np.zeros_like(r)], -1)
Image.fromarray(np.clip(mr * 255 + 0.5, 0, 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(OUT / 'bat_metal_rough_1k.png')
Image.fromarray(np.clip(normal * 255 + 0.5, 0, 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(OUT / 'bat_normal_1k.png')
# Region weights for the shared-skin tiers (claude_shared/fit_tier_regions.py): only the membrane changes per tier.
np.savez_compressed(OUT / 'bat_region_weights.npz', names=np.array(['membrane']), membrane=pad(mw))
# body region for native_tiers.py (fur and skin; eyes, teeth and claws excluded)
bw = ndimage.gaussian_filter((body & ~membrane).astype(np.float32), 1.0) * valid
np.savez_compressed(OUT / 'bat_body_weight.npz', body=pad(bw))
print('COMPOSED', {'membrane': int(membrane.sum()), 'body': int(body.sum()), 'eyes': int(red.sum()), 'light': int(light.sum())})
