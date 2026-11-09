#!/usr/bin/env python3
"""1K head texture set for the grafted head (rework 2026-10-30; CLAUDE_CREATURE_TEXTURES.md "Head detail").

Inputs: meshy/head_retexture_v1 (the Meshy head-only retexture on HeadUV, from the Codex head turnaround; since the
texture quality pass 2026-10-30 read from work/head_relayout, carried into the new HeadUV by resample_head.py),
textures/wmut_head_pin.json (the approved head skin match and head ramps, kept through the body repaint),
work/head_v2.npz (scripts/dump_head.py: head triangles with HeadUV, rest xyz and kind; the body triangles at the neck
ring), the body's graded base colour and region mask, textures/wmut_ramps.json (the body ramps).
- Skin luminance (kind 1) is matched to the body's skin region (5th..95th percentile, linear gain + gamma), so the
  head takes the body's skin ramps unchanged in every tier ("reuse the body's skin ramps for the head").
- Neck seam: the body's neck under the cut is feathered (region G), the head's neck is skin. Texels from the cut up
  to BLEND metres above it blend colour and mask channels toward the body's seam (median colour and mask of the
  body triangles at the ring), so the seam is a soft feather collar in every tier instead of a line.
- Region mask (RGBA as the body: R skin, G feathers, B wing, A hair): skin kinds -> R, hair -> A, eyes and teeth in
  no channel (they keep their own colours in every tier).
- Material classes (1 skin, 2 hair, 5 tooth, 6 eye) -> textures/wmut_head_material_classes.png.
- ORM: R 255 (no AO bake for the head set), G Meshy roughness clamped like the body, B 0.
- Body neck: texels within NECK_FADE below the cut fade into the seam feathers (wmut_basecolor_graded_v2.png,
  wmut_region_mask_v2.png; the old texels there held a pale smear beside the old off-centre face).
Writes textures/wmut_head_basecolor.png (1K), wmut_head_normal_1k.png, wmut_head_metal_rough_1k.png,
wmut_head_region_mask.png, wmut_head_material_classes.png and textures/wmut_ramps_v2.json (the body materials plus
Wmut_Head with the same ramps and the head mask). Usage: compose_head.py"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV

T = HERE / 'textures'
# texture quality pass 2026-10-30: head_retexture_v1's maps carried into the head_uv_texpass.py layout
M = HERE / 'work' / 'head_relayout'
PIN = json.load(open(HERE / 'textures' / 'wmut_head_pin.json'))
S = 1024
BLEND = 0.035
W = np.array([0.2126, 0.7152, 0.0722])
d = np.load(HERE / 'work' / (sys.argv[1] if len(sys.argv) > 1 else 'head_v4.npz'))
U = d['head_joint'] - d['neck']
U /= np.linalg.norm(U)
graft = json.load(open(HERE / 'work' / 'graft_v2.json'))
CUT_U = graft['config']['cut_u']


def raster(uvs, vals, size, nch):
    """per texel: the value (nch floats per triangle corner, barycentric) of the triangle covering it; cover mask"""
    out = np.zeros((size, size, nch), np.float32)
    cov = np.zeros((size, size), bool)
    for t in range(len(uvs)):
        p = uvs[t] * size
        x0, x1 = max(int(np.floor(p[:, 0].min())), 0), min(int(np.ceil(p[:, 0].max())), size - 1)
        y0, y1 = max(int(np.floor(p[:, 1].min())), 0), min(int(np.ceil(p[:, 1].max())), size - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        l3 = 1 - l1 - l2
        inside = (l1 >= -1e-4) & (l2 >= -1e-4) & (l3 >= -1e-4)
        iy, ix = np.nonzero(inside)
        v = vals[t]
        val = l1[iy, ix, None] * v[0] + l2[iy, ix, None] * v[1] + l3[iy, ix, None] * v[2]
        out[size - 1 - (iy + y0), ix + x0] = val
        cov[size - 1 - (iy + y0), ix + x0] = True
    return out, cov


def pad(img, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


# per texel: rest xyz -> height along the neck line above the cut; kind
ukey = ((d['head_xyz'] - d['neck']) @ U)[..., None]                 # (n, 3, 1)
kinds = np.repeat(d['head_kind'][:, None, None], 3, 1).astype(np.float32)
vals = np.concatenate([ukey, kinds], -1)
tex, cov = raster(d['head_uv'], vals, S, 2)
u = tex[..., 0]
kind = np.rint(tex[..., 1]).astype(int)
kind[~cov] = -1
# body reference: graded base colour, mask; skin texels and the seam colour/mask
body = RV.load_srgb(T / 'wmut_basecolor_graded.png', S)
bmask = np.asarray(Image.open(T / 'wmut_region_mask.png').convert('RGBA'), np.float32) / 255
body_lum = RV.srgb_to_linear(body) @ W
skin_ref = body_lum[bmask[..., 0] > 0.9]
sv = np.concatenate([np.zeros((len(d['seam_uv']), 3, 1), np.float32)], -1)
_, scov = raster(d['seam_uv'], np.zeros((len(d['seam_uv']), 3, 1), np.float32), S, 1)
seam_col = np.median(body[scov], 0)
seam_mask = np.median(bmask[scov], 0)
# head maps
base = np.asarray(Image.open(M / 'texture_urls_0_base_color.png').convert('RGB').resize((S, S), Image.LANCZOS),
                  np.float32) / 255
lin = RV.srgb_to_linear(base)
lum = lin @ W
skin = cov & ((kind == 1) | (kind == 0)) & (u > CUT_U + BLEND)
h5, h95 = PIN['skin_lum_head_p5_p95']        # same paint as v1: the v1 texel percentiles
b5, b95 = PIN['skin_lum_body_p5_p95']        # the approved head colours, independent of the body repaint
# lum' = b5 + (b95 - b5) * ((lum - h5) / (h95 - h5)) ** gamma: matched at both percentiles; colour scaled by lum'/lum
x = np.clip((lum - h5) / max(h95 - h5, 1e-4), 0, None)
gamma = 1.0
lum_new = b5 + (b95 - b5) * x ** gamma
gain = np.where(lum > 1e-4, lum_new / np.maximum(lum, 1e-4), 1.0)
skinish = cov & ((kind == 1) | (kind == 0))
lin2 = np.where(skinish[..., None], np.clip(lin * gain[..., None], 0, 1), lin)
# seam blend toward the body's feathered neck
w = np.clip(1 - (u - CUT_U) / BLEND, 0, 1)
w = np.where(skinish, w * w * (3 - 2 * w), 0)
seam_lin = RV.srgb_to_linear(seam_col)
lin3 = lin2 * (1 - w[..., None]) + seam_lin * w[..., None]
out = RV.linear_to_srgb(lin3) if hasattr(RV, 'linear_to_srgb') else np.where(
    lin3 <= 0.0031308, lin3 * 12.92, 1.055 * np.clip(lin3, 0, 1) ** (1 / 2.4) - 0.055)
# mask
mask = np.zeros((S, S, 4), np.float32)
mask[skinish, 0] = 1
mask[cov & (kind == 3), 3] = 1
mask[skinish] = mask[skinish] * (1 - w[skinish, None]) + seam_mask * w[skinish, None]
classes = np.zeros((S, S), np.uint8)
classes[skinish] = 1
classes[cov & (kind == 3)] = 2
classes[cov & (kind == 4)] = 5
classes[cov & (kind == 2)] = 6
# pad everything into the gutters, mask blurred 1 texel after padding (CLAUDE_CREATURE_TEXTURES.md step 5)
out = pad(out, cov)
mask = pad(mask, cov)
mask = np.stack([np.asarray(Image.fromarray((mask[..., k] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)),
                            np.float32) / 255 for k in range(4)], -1)
Image.fromarray((np.clip(out, 0, 1) * 255).round().astype(np.uint8)).save(T / 'wmut_head_basecolor.png')
RV.write_mask([mask[..., k] for k in range(4)], T / 'wmut_head_region_mask.png')
Image.fromarray(classes * 40).save(T / 'wmut_head_material_classes.png')
cov2k = raster(d['head_uv'], np.zeros((len(d['head_uv']), 3, 1), np.float32), 2048, 1)[1]
nrm = np.asarray(Image.open(M / 'texture_urls_0_normal.png').convert('RGB'), np.float32) / 255
Image.fromarray((pad(nrm, cov2k) * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS).save(T / 'wmut_head_normal_1k.png')
rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((S, S), Image.LANCZOS),
                   np.float32) / 255
rough = pad(np.where(kind == 3, np.clip(rough, 0.45, 0.7), np.clip(rough, 0.5, 0.85)), cov)
Image.merge('RGB', [Image.new('L', (S, S), 255), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (S, S), 0)]).save(T / 'wmut_head_metal_rough_1k.png')
# body neck below the cut: the old Meshy neck/face texels (a pale smear left of the off-centre old face) fade into
# the seam's feathers from the cut down to NECK_FADE below it, keeping their luminance detail; the mask follows
NECK_FADE = 0.07
S2 = 2048
bxyz = d['body_xyz'] - d['neck']
btex, bcov = raster(d['body_uv'], bxyz, S2, 3)
bt, bcov1 = raster(d['body_uv'], bxyz, S, 3)
body2k = RV.load_srgb(T / 'wmut_basecolor_graded_wing.png')   # wing_grain.py: the graded body, wing grain reduced


def fade_w(p, cov_):
    uu = p @ U
    rr = np.linalg.norm(p - uu[..., None] * U, axis=-1)          # distance from the neck line (wings stay)
    x = np.clip((uu - (CUT_U - NECK_FADE)) / NECK_FADE, 0, 1) * (uu <= CUT_U + 0.01)
    y = np.clip((0.14 - rr) / 0.04, 0, 1)
    return np.where(cov_, x * x * (3 - 2 * x) * y, 0.0)


wb = fade_w(btex, bcov)
bl = RV.srgb_to_linear(body2k)
blum = bl @ W
zone = wb > 0
ref = np.median(blum[zone]) if zone.any() else 1.0
detail = np.clip((blum / max(ref, 1e-4)) ** 0.5, 0.6, 1.5)
target = seam_lin[None, None, :] * detail[..., None]
bl2 = bl * (1 - wb[..., None]) + target * wb[..., None]
enc = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, 1) ** (1 / 2.4) - 0.055)
Image.fromarray((np.clip(enc(bl2), 0, 1) * 255).round().astype(np.uint8)).save(T / 'wmut_basecolor_graded_v2.png')
wb1 = fade_w(bt, bcov1)
bm2 = bmask * (1 - wb1[..., None]) + seam_mask[None, None, :] * wb1[..., None]
RV.write_mask([bm2[..., k] for k in range(4)], T / 'wmut_region_mask_v2.png')
# ramps: the body's, plus the head material with its own mask
R = json.load(open(T / 'wmut_ramps.json'))
mats = [dict(m, mask='wmut_region_mask_v2.png') for m in R['materials'] if m['base'] != 'Wmut_Head']
mats.append({'base': 'Wmut_Head', 'prefix': 'Wmut_Head', 'mask': 'wmut_head_region_mask.png',
             'ramps': PIN['ramps']})
R['materials'] = mats
R['head'] = {'skin_lum_head_p5_p95': [float(h5), float(h95)], 'skin_lum_body_p5_p95': [float(b5), float(b95)],
             'seam_colour_srgb': seam_col.round(4).tolist(), 'seam_mask': seam_mask.round(3).tolist(),
             'blend_m': BLEND, 'body_neck_fade_m': NECK_FADE, 'body_fade_texels_2k': int(zone.sum()), 'texels': {'skin': int(skinish.sum()), 'hair': int((cov & (kind == 3)).sum()),
                                          'eye': int((cov & (kind == 2)).sum()), 'tooth': int((cov & (kind == 4)).sum())}}
json.dump(R, open(T / 'wmut_ramps_v2.json', 'w'), indent=1)
print('HEADSET', json.dumps(R['head']))
