#!/usr/bin/env python3
"""Bloodsucker A/B/C textures from the Meshy retexture. Texels are classed by hue (teal body, tan membrane,
salmon/red maw and belly, low-saturation ivory bone); body, membrane and maw are recoloured to the native tier medians
(palettes 162 / 672 / 673, measured with the restored region masks), keeping Meshy's luminance detail; bone and
claws stay ivory. A baked short-range AO (bake_ao.py) is multiplied in so crevices read like the sprites' painted
shading. The UV layout is the Meshy one shrunk to 90% toward the top-left (add_maw.py); the freed bottom-right
square holds the maw disc, painted with the native attack-frame maw (bldattb0, per tier palette). Writes
textures/bld_{a,b,c}_basecolor.png, normal and metal-rough maps, and a class preview."""
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
TIERS = {'a': {'body': (0.267, 0.204, 0.176), 'wing': (0.255, 0.188, 0.298), 'maw': (0.239, 0.157, 0.192)},
         'b': {'body': (0.188, 0.251, 0.224), 'wing': (0.298, 0.255, 0.188), 'maw': (0.239, 0.204, 0.161)},
         'c': {'body': (0.251, 0.165, 0.169), 'wing': (0.349, 0.137, 0.153), 'maw': (0.29, 0.114, 0.122)}}
GAIN = {'body': 1.1, 'wing': 1.3, 'maw': 1.5}      # sprites carry baked shading; the model is lit at runtime
PALETTE = {'a': '162', 'b': '672', 'c': '673'}
AO_STRENGTH = 0.75
MAW_CENTRE, MAW_RADIUS = (149.0, 121.0), 66.0      # native bldattb0 disc without the claws (px)
UV_SCALE, MAW_UV = 0.9, (0.95, 0.05, 0.048)          # must match add_maw.py
data = np.load(ROOT / 'work/uv3d.npz')
part_map, xyz = C.rasterise(data)
strict, _ = C.rasterise(data, tol=0.0)
interior = ndimage.binary_erosion(strict >= 0, iterations=2)
_, (iy, ix) = ndimage.distance_transform_edt(~interior, return_indices=True)


def pad(a):
    o = a[iy, ix]; o[interior] = a[interior]; return o




def shrunk(path):
    """Meshy texture moved into the 90% layout (top-left corner)."""
    img = C.load(path); hgt, wid = img.shape[:2]
    small = np.asarray(Image.fromarray(np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)).resize(
        (round(wid * UV_SCALE), round(hgt * UV_SCALE)), Image.LANCZOS), np.float32) / 255
    out = np.zeros_like(img); out[:small.shape[0], :small.shape[1]] = small
    return out


base = pad(shrunk(str(SRC) + '_base_color.png'))
normal = pad(shrunk(str(SRC) + '_normal.png'))
h, s, v = C.hsv(base)
valid = part_map >= 0
lum = base @ np.array([0.2126, 0.7152, 0.0722])
bone = valid & (s < 0.22) & (v > 0.42)
maw = valid & ~bone & ((h < 16) | (h > 330)) & (s > 0.25)
wing = valid & ~bone & ~maw & (h >= 16) & (h < 60)
body = valid & ~bone & ~maw & ~wing
masks = {'body': body, 'wing': wing, 'maw': maw}
ao = np.asarray(Image.open(ROOT / 'textures/bld_ao_2k.png').convert('L').resize(lum.shape[::-1], Image.BILINEAR),
                np.float32) / 255
shade_ao = 1.0 - AO_STRENGTH * (1.0 - ao)
# Maw disc square (bottom-right): texel UV -> native maw disc.
hgt, wid = lum.shape
uu = (np.arange(wid) + 0.5) / wid; vv = 1.0 - (np.arange(hgt) + 0.5) / hgt
uu, vv = np.meshgrid(uu, vv)
disc = (uu >= UV_SCALE) & (vv <= 1.0 - UV_SCALE)
u_spr = MAW_CENTRE[0] + (uu - MAW_UV[0]) / MAW_UV[2] * MAW_RADIUS
v_spr = MAW_CENTRE[1] - (vv - MAW_UV[1]) / MAW_UV[2] * MAW_RADIUS
normal[disc] = (0.5, 0.5, 1.0)
for m in (body, wing, maw, bone):
    m &= ~disc
soft = {k: ndimage.gaussian_filter(m.astype(np.float32), 1.0) for k, m in masks.items()}
total = np.maximum(sum(soft.values()) + ndimage.gaussian_filter(bone.astype(np.float32), 1.0), 1e-6)
for tier, colours in TIERS.items():
    out = base.copy() * (ndimage.gaussian_filter(bone.astype(np.float32), 1.0) / total)[..., None]
    for k, m in masks.items():
        ref = np.median(lum[m]); shade = np.clip(lum / ref, 0.3, 2.2)[..., None]
        col = np.clip(np.array(colours[k])[None, None] * GAIN[k] * shade, 0, 1)
        out += col * (soft[k] / total)[..., None]
    out *= shade_ao[..., None]
    sprite = Image.open(ROOT.parent / 'mm6_bld' / 'native_variants' / f'bldattb0_{PALETTE[tier]}.png').convert('RGBA')
    sprite = np.asarray(sprite.resize((sprite.width * 4, sprite.height * 4), Image.LANCZOS), np.float32) / 255
    sx = np.clip(u_spr * 4, 0, sprite.shape[1] - 1).astype(int)
    sy = np.clip(v_spr * 4, 0, sprite.shape[0] - 1).astype(int)
    out = np.where(valid[..., None], out, base)
    out[disc] = np.clip(sprite[sy, sx, :3] * GAIN['maw'] * 0.85, 0, 1)[disc]
    out = pad(out); out[disc] = np.clip(sprite[sy, sx, :3] * GAIN['maw'] * 0.85, 0, 1)[disc]
    Image.fromarray(np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / f'bld_{tier}_basecolor.png',
                                                                           optimize=True)
preview = np.zeros(base.shape, np.float32)
for m, c in ((body, (0, 0.6, 0.5)), (wing, (0.8, 0.6, 0.2)), (maw, (0.9, 0.2, 0.3)), (bone, (1, 1, 1))):
    preview[m] = c
Image.fromarray((preview * 255).astype(np.uint8)).resize((1024, 1024), Image.NEAREST).save(ROOT / 'review' /
                                                                                        'texture_classes.png')
r = np.full(lum.shape, 0.7, np.float32); r[wing] = 0.62; r[maw] = 0.4; r[bone] = 0.45
mr = np.stack([np.ones_like(r), r, np.zeros_like(r)], -1)
Image.fromarray(np.clip(mr * 255 + 0.5, 0, 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(
    OUT / 'bld_metal_rough_1k.png')
Image.fromarray(np.clip(normal * 255 + 0.5, 0, 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(
    OUT / 'bld_normal_1k.png')
# Region weights for the shared-skin tiers (claude_shared/fit_tier_regions.py): body, wing, maw, maw disc square.
weights = {}
for k in masks:
    w = pad(soft[k] / total * valid)
    w[disc] = 0
    weights[k] = w
weights['disc'] = disc.astype(np.float32)
np.savez_compressed(OUT / 'bld_region_weights.npz', names=np.array(['body', 'wing', 'maw', 'disc']), **weights)
print('COMPOSED', {k: int(m.sum()) for k, m in dict(masks, bone=bone, disc=disc).items()})
