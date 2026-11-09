#!/usr/bin/env python3
"""Shared texture set, region mask, material classes and tier ramps of the drone (CLAUDE_CREATURE_TEXTURES.md).

Inputs: Meshy retexture maps (meshy/texture_v1/, painted on our UVs), work/uv3d.npz (dump_uv3d.py), work/tri_comp.npy
(mesh components), textures/hdr_ao_2k.png (bake_ao.py).
Texel classes (Meshy hue/saturation/value + geometry):
  bone    rib spurs (small components above z RIB_Z that are mostly light ceramic) and the tendon claws: recoloured to
          bone ivory in the base, in no region (bone-white on every tier, as the concept's tier views show)
  casing  warm ceramic (hue 12-55, value >= 0.25) except the front assembly's gold     -> region R
  resin   violet / maroon (hue >= 300 or < 12)                                       -> region G
  cable   the tendon cables: repainted near-black, in no region
  glow    bright saturated orange, the lens dome, the emitter disc, the ring cells    -> region B
  trim    gold of the lens collars (warm, saturation >= 0.6, value >= 0.45, y < -0.24), the gear's gold -> A
  other   dark warm crevices: no region (kept as painted)
The reserved strip (v < 0.125) is painted procedurally: the lens dome (radial glow), the B twin emitter (ceramic
barrel with gold collars, glowing disc), the C shield ring (gold rims, dark cell housings, glowing cells).
Outputs in textures/: hdr_basecolor_2k.png (graded with AO), hdr_normal_1k.png, hdr_metal_rough_1k.png (R AO,
G roughness, B metallic 0), hdr_region_mask.png (1K RGBA), hdr_material_classes.png (1K L), hdr_thrust.png (RGBA
gradient), hdr_glowmask.png (all-white mask of the glow and thrust materials), hdr_ramps.json."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
from raster import raster
from hsv import rgb_to_hsv
import region_variants as RV

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / 'textures'; M = ROOT / 'meshy' / 'texture_v1'
S = 2048
RIB_Z, RIB_MAX_TRIS = 0.35, 80
rng = np.random.default_rng(7)

d = np.load(ROOT / 'work' / 'uv3d.npz'); tri_comp = np.load(ROOT / 'work' / 'tri_comp.npy')
pos, tid = raster(d['uv'], d['co'], S)
inside = tid >= 0
part = np.where(inside, d['part'][np.maximum(tid, 0)], -1)
comp = np.where(inside, tri_comp[np.maximum(tid, 0)], -1)
base = np.asarray(Image.open(M / 'texture_urls_0_base_color.png').convert('RGB'), np.float32) / 255
hsv = rgb_to_hsv(base); H, Sa, V = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
warm = (H >= 12) & (H < 55)
# Meshy painted the ceramic plates a saturated tan (hue 20-35 like its gold), so gold is only taken where the
# masters have it: the lens collars and plates of the front assembly (y < FRONT_Y); elsewhere warm = casing.
FRONT_Y = -0.24
front = pos[..., 1] < FRONT_Y
ceramic = warm & (V >= 0.25) & ~(front & (Sa >= 0.6) & (V >= 0.45))
gold = warm & front & (Sa >= 0.6) & (V >= 0.45)
purple = (H >= 300) | (H < 12)
hot = (H < 30) & (Sa > 0.8) & (V > 0.8)

# rib components: small, high, mostly ceramic
rib_comps = set()
for c in np.unique(tri_comp[d['part'] == 0]):
    tris = np.nonzero(tri_comp == c)[0]
    if len(tris) > RIB_MAX_TRIS or d['co'][tris].reshape(-1, 3)[:, 2].min() < RIB_Z:
        continue
    m = comp == c
    if m.sum() and ceramic[m].mean() > 0.35:
        rib_comps.add(int(c))
body = part == 0; tend = (part >= 1) & (part <= 3)
bone = (body & np.isin(comp, list(rib_comps)) & (ceramic | gold)) | (tend & (ceramic | gold))
cls = np.zeros((S, S), np.uint8)              # 0 empty 1 casing 2 resin 3 glow 4 trim 5 bone 6 other
geo = body | tend
cls[geo] = 6
cls[geo & purple] = 2
cls[tend & ~bone] = 2
cls[geo & gold] = 4
cls[geo & ceramic] = 1
cls[geo & hot] = 3
cls[bone] = 5
print('RIB components', len(rib_comps), 'class texels', {k: int((cls == k).sum()) for k in range(7)})

col = base.copy()
# tendon cables: near-black segmented cable on every tier (the concept's cables), in no region
cable = tend & ~bone
col[cable] = np.clip((0.04 + 0.55 * (base[cable] @ RV.LUMA.astype(np.float32)))[:, None] * np.array([1.0, 0.97, 1.02]), 0, 1)
cls[cable] = 6
# bone: ivory with the painted luminance
lum = base @ RV.LUMA.astype(np.float32)
ivory = np.array([0.93, 0.87, 0.76], np.float32)
col[bone] = np.clip((0.35 + 0.85 * lum[bone])[:, None] * ivory, 0, 1)


# ---------------------------------------------------------------- reserved strip (UV v < 0.125 = image rows >= 1792)
def strip_box(u0, v0, u1, v1):
    """strip pixel box (u right, v up from the atlas bottom, 2048 atlas) -> image rows/cols slices"""
    return slice(S - int(v1), S - int(v0)), slice(int(u0), int(u1))


def radial(rows, cols, cu, cv, r, stops):
    yy, xx = np.mgrid[rows, cols]
    t = np.hypot(xx + 0.5 - cu, (S - (yy + 0.5)) - cv) / r
    out = np.zeros(t.shape + (3,), np.float32)
    ts = np.array([s[0] for s in stops]); cs = np.array([s[1] for s in stops], np.float32) / 255
    for k in range(3):
        out[..., k] = np.interp(t, ts, cs[:, k])
    return out, t


GLOW = [(0.0, (255, 246, 205)), (0.22, (255, 214, 120)), (0.5, (255, 140, 35)), (0.8, (225, 80, 12)),
        (0.95, (150, 45, 10)), (1.05, (70, 30, 12)), (9, (70, 30, 12))]
strip = np.zeros((S, S), bool); strip[S - 256:, :] = True
# lens dome: planar front projection into u, v 0.008..0.117 (16..240 px)
rows, cols = strip_box(0, 0, 256, 256)
lens_rgb, t = radial(rows, cols, 128, 128, 112, GLOW)
col[rows, cols] = lens_rgb; cls[rows, cols] = 3
# twin emitter barrel (u 260..900 around, v 8..120 along 11 profile rings) and its disc (260..380, 130..250)
PROFILE_V = np.linspace(8, 120, 11)
rows, cols = strip_box(256, 0, 904, 128)
yy, xx = np.mgrid[rows, cols]; vv = S - (yy + 0.5)
ring_i = np.interp(vv, PROFILE_V, np.arange(11))
collar = ((ring_i >= 2) & (ring_i < 4)) | ((ring_i >= 7) & (ring_i < 9)) | (ring_i < 1)
noise = ndimage.gaussian_filter(rng.normal(0, 1, vv.shape), 2.0) * 0.05
cer = np.array([0.86, 0.80, 0.70]) * (0.92 + noise[..., None] + 0.06 * np.cos(xx / 640 * 2 * np.pi * 2)[..., None])
gld = np.array([0.80, 0.60, 0.25]) * (0.9 + 1.5 * noise[..., None])
seam = (np.abs(((xx - 256) / 640 * 12) % 1 - 0.5) < 0.04) & ~collar
cer = np.where(seam[..., None], cer * 0.6, cer)
col[rows, cols] = np.where(collar[..., None], gld, cer).clip(0, 1)
cls[rows, cols] = np.where(collar, 4, 1)
rows, cols = strip_box(256, 128, 384, 256)
disc, t = radial(rows, cols, 320, 190, 60, GLOW)
col[rows, cols] = disc; cls[rows, cols] = 3
# shield ring: outer band v 8..60 (gold rims 8..17 and 51..60, dark housings between), top 64..80, inner 84..110,
# bottom 112..126 (gold, darker), cells 930..990 x 134..166 (glow)
rows, cols = strip_box(904, 0, 2048, 128)
yy, xx = np.mgrid[rows, cols]; vv = S - (yy + 0.5)
noise = ndimage.gaussian_filter(rng.normal(0, 1, vv.shape), 1.5) * 0.06
rim = ((vv >= 8) & (vv < 17)) | ((vv >= 51) & (vv < 61)) | (vv >= 61)
seg = (((xx - 920) / 1120 * 40) % 4) < 0.35                    # gold clamps every fourth segment
g = np.array([0.82, 0.62, 0.26]); dark = np.array([0.10, 0.09, 0.10])
ringcol = np.where((rim | seg)[..., None], g * (0.9 + noise[..., None] + np.where(vv >= 84, -0.25, 0)[..., None]),
                   dark * (1 + 2 * noise[..., None]))
col[rows, cols] = ringcol.clip(0, 1)
cls[rows, cols] = np.where(rim | seg, 4, 6)
rows, cols = strip_box(920, 130, 1000, 170)
yy, xx = np.mgrid[rows, cols]
cell, t = radial(rows, cols, 960, 150, 34, [(0, (255, 246, 215)), (0.6, (255, 190, 90)), (1.0, (240, 110, 30)), (9, (240, 110, 30))])
col[rows, cols] = cell; cls[rows, cols] = 3
print('STRIP painted')

# ---------------------------------------------------------------- AO grade (body only), padding
ao = np.asarray(Image.open(T / 'hdr_ao_2k.png').convert('L'), np.float32) / 255
empty_ao = ao <= 0.003
_, (iy, ix) = ndimage.distance_transform_edt(empty_ao, return_indices=True); ao = ndimage.gaussian_filter(ao[iy, ix], 2.0)
shade = np.where(strip, 1.0, 1 - 0.65 * (1 - ao))
col = np.clip(col * shade[..., None], 0, 1)
used = cls > 0
_, (iy, ix) = ndimage.distance_transform_edt(~used, return_indices=True)
col = col[iy, ix]; cls_pad = cls[iy, ix]
Image.fromarray((col * 255 + 0.5).astype(np.uint8)).save(T / 'hdr_basecolor_2k.png')
lin_lum = RV.luminance(col)

# ---------------------------------------------------------------- region mask (1K), padded then feathered
weights = []
for k in (1, 2, 3, 4):
    w = (cls_pad == k).astype(np.float32)
    w = ndimage.gaussian_filter(w, 1.5)
    weights.append(w)
RV.write_mask(weights, T / 'hdr_region_mask.png', 1024)
# material classes (1K, nearest): 11 glazed ceramic, 4 chitin/resin and cables, 6 glow lens, 9 gold, 5 bone, 11 other
lab = np.zeros((S, S), np.uint8)
for k, v in ((1, 11), (2, 4), (3, 6), (4, 9), (5, 5), (6, 11)):
    lab[cls == k] = v
Image.fromarray(lab[::2, ::2]).save(T / 'hdr_material_classes.png')

# ---------------------------------------------------------------- normal, ORM
nrm = Image.open(M / 'texture_urls_0_normal.png').convert('RGB')
na = np.asarray(nrm, np.uint8).copy(); na[strip] = (128, 128, 255)
Image.fromarray(na).resize((1024, 1024), Image.LANCZOS).save(T / 'hdr_normal_1k.png')
rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L'), np.float32) / 255
rough = np.where(cls == 3, 0.3, np.where(cls == 4, 0.45, np.clip(rough, 0.45, 0.85)))
rough = rough[iy, ix]
orm = np.stack([ao[::2, ::2], rough[::2, ::2], np.zeros((1024, 1024))], -1)
Image.fromarray((orm * 255 + 0.5).astype(np.uint8)).save(T / 'hdr_metal_rough_1k.png')
# thrust gradient (u around, v 0 at the vent ring -> 1 at the tip in image rows top -> bottom) and the glow masks
g = np.linspace(0, 1, 128)[:, None]
thr = np.zeros((128, 32, 4), np.float32)
thr[..., 0] = 1.0; thr[..., 1] = (0.62 - 0.40 * g); thr[..., 2] = (0.22 - 0.2 * g)
thr[..., 3] = (0.5 * (1 - g) ** 2.0)
Image.fromarray((thr * 255 + 0.5).astype(np.uint8), 'RGBA').save(T / 'hdr_thrust.png')
Image.new('RGBA', (16, 16), (255, 0, 0, 0)).save(T / 'hdr_glowmask.png')

# ---------------------------------------------------------------- ramps from the tier palette (sRGB stops at 0, .5, 1)
PAL = {
    'casing': {'hdr_a': [(118, 100, 82), (214, 200, 176), (247, 240, 225)],      # bone-white Ancient ceramic
               'hdr_b': [(62, 45, 32), (160, 128, 94), (214, 188, 150)],         # darker scorched ivory
               'hdr_c': [(20, 18, 20), (58, 54, 56), (118, 108, 102)]},          # blackened
    'resin': {'hdr_a': [(18, 8, 22), (58, 28, 68), (112, 72, 124)],            # violet resin
              'hdr_b': [(9, 7, 9), (34, 27, 33), (84, 70, 80)],                  # black resin
              'hdr_c': [(16, 4, 28), (52, 14, 84), (104, 48, 140)]},            # deep violet
    'glow': {'hdr_a': [(80, 30, 10), (255, 140, 35), (255, 246, 205)],           # orange
             'hdr_b': [(80, 12, 4), (250, 72, 14), (255, 200, 150)],             # hotter orange-red
             'hdr_c': [(110, 55, 20), (255, 196, 110), (255, 252, 240)]},        # orange-white
    'trim': {'hdr_a': [(70, 45, 15), (190, 140, 58), (248, 214, 135)],           # gold
             'hdr_b': [(42, 24, 8), (128, 80, 32), (200, 142, 72)],              # darker bronze
             'hdr_c': [(92, 62, 16), (222, 172, 62), (255, 236, 160)]},          # bright gold
}


def ramp(stops, lo, hi):
    x = np.linspace(0, 1, 16); c = RV.srgb_to_linear(np.array(stops, np.float64) / 255)
    return {'range': [round(lo, 6), round(hi, 6)],
            'colors': np.round(np.stack([np.interp(x, [0, 0.5, 1], c[:, k]) for k in range(3)], -1), 6).tolist()}


ranges = {}
for name, k in (('casing', 1), ('resin', 2), ('glow', 3), ('trim', 4)):
    core = cls == k
    ranges[name] = [float(np.percentile(lin_lum[core], 2)), float(np.percentile(lin_lum[core], 98))]
glow_lo, glow_hi = ranges['glow']
variants = ['hdr_a', 'hdr_b', 'hdr_c']
out = {'variants': variants, 'materials': [
    {'base': 'Casing_A', 'prefix': 'Casing', 'mask': 'hdr_region_mask.png',
     'ramps': {v: [ramp(PAL[r][v], *ranges[r]) for r in ('casing', 'resin', 'glow', 'trim')] for v in variants}},
    {'base': 'Glow_A', 'prefix': 'Glow', 'mask': 'hdr_region_mask.png',
     'ramps': {v: [ramp(PAL[r][v], *ranges[r]) for r in ('casing', 'resin', 'glow', 'trim')] for v in variants}},
    {'base': 'Thrust_A', 'prefix': 'Thrust', 'mask': 'hdr_glowmask.png',
     'ramps': {v: [ramp(PAL['glow'][v], 0.25, 1.0)] for v in variants}},
], 'ranges': ranges, 'palette_srgb_stops': PAL}
json.dump(out, open(T / 'hdr_ramps.json', 'w'), indent=1)
print('RAMPS ranges', {k: [round(a, 3), round(b, 3)] for k, (a, b) in ranges.items()})
