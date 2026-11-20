#!/usr/bin/env python3
"""Shared texture set of the hand-built drone (v2; CLAUDE_CREATURE_TEXTURES.md), painted from our own Hesper
materials (design/kreegan_world/art, the same sets the turrets and decorations use) through each face's TileUV
(metres), plus procedural parts. No Meshy texture.

Per texel (2K atlas, work/uv3d.npz from dump_uv3d.py on work/gear_v1.blend):
  casing    `hoterm` ceramic (its gold seam band cut out), panel seams with gold lips and rivets; on the right flank
            behind the front plates and over the back ("overgrowth zone") resin skin `hoaresin` instead
  gold      `hcgold` (collars, plate borders, vent rim, tail band; the strip gear's gold)       -> region A (trim)
  resin     `hoaresin` on the tubes, `hochitin` on the masses                                  -> region G
  glow      the lens dome, vent slots and nozzle, the gear's disc and cells, and the bright orange of the resin
            textures                                                                         -> region B
  ceramic                                                                                     -> region R
  dark metal (lens collar), vent band, bone (ribs, hooks, claws), cables: in no region (the same on every tier)
Writes textures/: hdr_basecolor_2k.png (AO-graded), hdr_normal_1k.png (from the painted height, glTF +Y up),
hdr_metal_rough_1k.png (R AO, G roughness, B 0), hdr_region_mask.png, hdr_material_classes.png, hdr_thrust.png,
hdr_glowmask.png, hdr_ramps.json (same tier palette as v1, compose_hdr.PAL)."""
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
from raster import raster
from hsv import rgb_to_hsv
import region_variants as RV

ROOT = Path(__file__).resolve().parents[1]; T = ROOT / 'textures'
REPO = ROOT.parents[2]
ART = REPO / 'design' / 'kreegan_world' / 'art'
S = 2048
MAT = {'ceramic': 0, 'gold': 1, 'darkmetal': 2, 'lens': 3, 'ventband': 4, 'ventglow': 5, 'resin': 6, 'chitin': 7,
       'bone': 8, 'cable': 9}
SX, AXIS_Z = 0.94, None
rng = np.random.default_rng(5)


def load(path, rows=None):
    a = np.asarray(Image.open(path).convert('RGB'), np.float32) / 255
    if rows:
        a = a[rows[0]:rows[1]]
        a = np.concatenate([a, a[::-1]], 0)            # mirrored so the crop tiles in v
    return a


def sample(tex, u, v, metres_per_tile_u):
    """bilinear, wrapping; u, v in metres; the tile's aspect follows the image"""
    h, w = tex.shape[:2]
    x = (u / metres_per_tile_u) * w; y = (v / (metres_per_tile_u * h / w)) * h
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = (x - x0)[..., None]; fy = (y - y0)[..., None]
    g = lambda yy, xx: tex[yy % h, xx % w]
    return (g(y0, x0) * (1 - fx) + g(y0, x0 + 1) * fx) * (1 - fy) + (g(y0 + 1, x0) * (1 - fx) + g(y0 + 1, x0 + 1) * fx) * fy


CER = load(ART / 'textures_out1' / 'masters' / 'hoterm.png', (250, 800))
RES = load(ART / 'textures_out1' / 'masters' / 'hoaresin.png')
CHI = load(ART / 'textures_out1' / 'masters' / 'hochitin.png')
GOLD = load(REPO / 'level_generation' / 'props' / 'hesper_decorations' / 'work' / 'hard_surface' / 'derived' / 'hcgold.png')

d = np.load(ROOT / 'work' / 'uv3d.npz')
rig = json.load(open(ROOT / 'work' / 'rig_info.json'))
AXIS_Z = rig['lens_base'][2]
vals = np.concatenate([d['tile'], d['co']], -1)            # per vertex: tile u, v, x, y, z
img, tid = raster(d['uv'], vals, S)
inside = tid >= 0
part = np.where(inside, d['part'][np.maximum(tid, 0)], -1)
mat = np.where(inside, d['mat'][np.maximum(tid, 0)], -1)
tu, tv = img[..., 0], img[..., 1]
px, py, pz = img[..., 2], img[..., 3], img[..., 4]
body = inside & (part <= 4)
col = np.zeros((S, S, 3), np.float32) + 0.5
cls = np.zeros((S, S), np.uint8)       # 0 empty 1 casing 2 resin 3 glow 4 trim 5 bone 6 other(no region)
height = np.zeros((S, S), np.float32)

# angle round the casing (0 top, + toward the right flank) and a low-frequency noise for organic borders
ang = np.arctan2(-px / SX, pz - AXIS_Z)
noise = lambda f, ph: np.sin(py * f + ph) * np.cos(ang * f * 0.21 + ph * 1.7)
zone = ((ang > 0.45 + 0.12 * noise(31, 1.0)) & (py > -0.13 + 0.04 * noise(23, 2.0))) | \
       (py > 0.135 + 0.035 * noise(27, 0.4) + 0.02 * np.cos(2 * ang))

# ---------------------------------------------------------------- casing ceramic, seams, rivets, resin skin
# the tail cap closes in a pole, where the lathe's TileUV pinches the texture into a star: towards the tip the
# casing textures are sampled planar across the axis instead (blended over 2 cm)
tail_w = np.clip((py - 0.345) / 0.02, 0, 1)[..., None]


def sample_casing(tex, metres_per_tile_u):
    lathe_c = sample(tex, tu, tv, metres_per_tile_u)
    planar = sample(tex, px + 5.0, pz - AXIS_Z + 5.0, metres_per_tile_u)
    return lathe_c * (1 - tail_w) + planar * tail_w


m = body & (mat == MAT['ceramic'])
c = sample_casing(CER, 0.45)
col[m] = c[m]; cls[m] = 1; height[m] = (c[m] @ RV.LUMA.astype(np.float32)) * 0.6
# seams on the bare casing (not on the raised plates: they sit above the casing radius)
r_here = np.hypot(px / SX, pz - AXIS_Z)
r_case = np.interp(py, [-0.29, -0.262, -0.215, -0.15, -0.07, 0.01, 0.09, 0.16, 0.22, 0.268, 0.30],
                   [0.150, 0.170, 0.186, 0.196, 0.201, 0.200, 0.194, 0.181, 0.162, 0.137, 0.112])
on_plate = r_here > r_case + 0.004
seam_d = np.minimum.reduce([np.abs(py - 0.12) * 1.0, np.abs(py + 0.20) * 1.0,
                            np.abs(np.abs(ang) - 2.95) * r_case, np.abs(ang - 0.0) * r_case + (py < 0.12) * 9])
groove = m & ~on_plate & (seam_d < 0.0018)
lip = m & ~on_plate & (seam_d >= 0.0018) & (seam_d < 0.0055)
col[lip] = sample(GOLD, tu, tv, 0.3)[lip]; cls[lip] = 4; height[lip] += 0.25
col[groove] = col[groove] * 0.35; height[groove] -= 0.5
# rivets: gold dots 9 mm inside the seams every 5 cm
riv_y = (np.abs(((py + 0.2) % 0.05) - 0.025) < 0.0035) & (np.abs(np.abs(ang) - 2.95) * r_case - 0.009 < 0.0035) & \
        (np.abs(np.abs(ang) - 2.95) * r_case > 0.0055)
riv = m & ~on_plate & riv_y
col[riv] = (0.86, 0.68, 0.32); cls[riv] = 4; height[riv] += 0.6
skin = m & zone & ~on_plate
cs = sample_casing(RES, 0.25)
col[skin] = cs[skin]; cls[skin] = 2; height[skin] = (cs[skin] @ RV.LUMA.astype(np.float32)) * 1.2

# ---------------------------------------------------------------- other materials
m = body & (mat == MAT['gold']); g = sample(GOLD, tu, tv, 0.3); col[m] = g[m]; cls[m] = 4
height[m] = (g[m] @ RV.LUMA.astype(np.float32)) * 0.4
m = body & (mat == MAT['resin']); r_ = sample(RES, tu, tv, 0.17); col[m] = r_[m]; cls[m] = 2
height[m] = (r_[m] @ RV.LUMA.astype(np.float32)) * 1.4
m = body & (mat == MAT['chitin']); ch = sample(CHI, tu, tv, 0.2); col[m] = ch[m]; cls[m] = 2
height[m] = (ch[m] @ RV.LUMA.astype(np.float32)) * 1.4
m = body & (mat == MAT['darkmetal'])
seg = (np.abs(((tu / (2 * math.pi * 0.13)) * 16) % 1 - 0.5) > 0.44)
col[m] = 0.11; col[m & seg] = 0.04; col[m & ~seg] *= (1 + 0.15 * np.sin(tv[m & ~seg] * 900))[:, None]
cls[m] = 6; height[m & seg] = -0.5
m = body & (mat == MAT['ventband']); col[m] = (0.09, 0.085, 0.09); cls[m] = 6
col[m] *= (1 + 0.25 * (np.abs((tv[m] * 400) % 1 - 0.5) < 0.1))[:, None]
GLOW = [(0.0, (255, 246, 205)), (0.22, (255, 214, 120)), (0.5, (255, 140, 35)), (0.8, (225, 80, 12)),
        (0.95, (150, 45, 10)), (1.05, (70, 30, 12)), (9, (70, 30, 12))]
gts = np.array([s_[0] for s_ in GLOW]); gcs = np.array([s_[1] for s_ in GLOW], np.float32) / 255
glow_of = lambda t: np.stack([np.interp(t, gts, gcs[:, k]) for k in range(3)], -1)
m = body & (mat == MAT['ventglow'])
slot = m & (np.abs(tu) < 0.031) & (np.abs(tv) < 0.016) & (np.abs(px) > 0.0)
tsl = np.hypot((tu - 0.015) / 0.015, (tv - 0.0075) / 0.0075) * 0.75
tnz = np.hypot(px, py - (-0.03)) / 0.05
r_drum = np.hypot(px, py + 0.03)
tt = np.where(r_drum > 0.07, tsl, tnz)                     # slots on the drum's band, the nozzle in its bottom
col[m] = glow_of(np.clip(tt[m], 0, 0.9)); cls[m] = 3
m = body & (mat == MAT['bone'])
tb = np.clip(tv / 0.13, 0, 1)
streak = 0.06 * np.sin(tu * 700 + np.sin(tv * 90) * 2)
bone = np.array([0.90, 0.84, 0.72]) * (0.78 + 0.22 * tb)[..., None] + streak[..., None]
bone = bone * (1 - 0.25 * (1 - tb) ** 3)[..., None] + np.array([-0.05, -0.07, -0.08]) * ((1 - tb) ** 3)[..., None]
col[m] = np.clip(bone[m], 0, 1); cls[m] = 5; height[m] = streak[m] * 3
m = body & (mat == MAT['cable'])
ring = np.abs((tv * 50) % 1 - 0.5)
col[m] = (0.07 + 0.1 * (ring[m] < 0.18))[:, None] * np.array([1.0, 0.97, 1.04]); cls[m] = 6
height[m] = (ring[m] < 0.18) * 0.6
# the lens dome (part 4, planar in the strip's first square)
lm = inside & (part == 4)
yy, xx = np.nonzero(lm)
tl = np.hypot(xx + 0.5 - 128, (S - (yy + 0.5)) - 128) / 112
col[yy, xx] = glow_of(tl); cls[yy, xx] = 3
# bright orange of the resin textures glows (region B)
hsv = rgb_to_hsv(np.clip(col, 0, 1))
hot = (cls == 2) & (hsv[..., 0] * 360 < 40) & (hsv[..., 1] > 0.55) & (hsv[..., 2] > 0.55)
cls[hot] = 3
print('CLASSES', {k: int((cls == k).sum()) for k in range(7)}, 'resin glow texels', int(hot.sum()))

# ---------------------------------------------------------------- the reserved strip: tier gear (as compose_hdr.py)
def strip_box(u0, v0, u1, v1):
    return slice(S - int(v1), S - int(v0)), slice(int(u0), int(u1))


def radial(rows, cols, cu, cv, r, stops):
    yy, xx = np.mgrid[rows, cols]
    t = np.hypot(xx + 0.5 - cu, (S - (yy + 0.5)) - cv) / r
    ts = np.array([s_[0] for s_ in stops]); cs_ = np.array([s_[1] for s_ in stops], np.float32) / 255
    return np.stack([np.interp(t, ts, cs_[:, k]) for k in range(3)], -1)


gear = inside & (part >= 5)
PROFILE_V = np.linspace(8, 120, 11)
rows, cols = strip_box(256, 0, 904, 128)
yy, xx = np.mgrid[rows, cols]; vv = S - (yy + 0.5)
ring_i = np.interp(vv, PROFILE_V, np.arange(11))
collar = ((ring_i >= 2) & (ring_i < 4)) | ((ring_i >= 7) & (ring_i < 9)) | (ring_i < 1)
cer = sample(CER, xx / 640 * 0.25, vv / 112 * 0.15, 0.45)
gld = sample(GOLD, xx / 640 * 0.25, vv / 112 * 0.15, 0.3)
col[rows, cols] = np.where(collar[..., None], gld, cer); cls[rows, cols] = np.where(collar, 4, 1)
rows, cols = strip_box(256, 128, 384, 256); col[rows, cols] = radial(rows, cols, 320, 190, 60, GLOW); cls[rows, cols] = 3
rows, cols = strip_box(904, 0, 2048, 128)
yy, xx = np.mgrid[rows, cols]; vv = S - (yy + 0.5)
rim = ((vv >= 8) & (vv < 17)) | ((vv >= 51) & (vv < 61)) | (vv >= 61)
seg = (((xx - 920) / 1120 * 40) % 4) < 0.35
gld = sample(GOLD, (xx - 904) / 1120 * 1.6, vv / 128 * 0.06, 0.3)
dark = np.array([0.10, 0.09, 0.10]) * (1 + 0.3 * np.sin(xx * 0.7))[..., None]
col[rows, cols] = np.where((rim | seg)[..., None], gld * np.where(vv >= 84, 0.75, 1.0)[..., None], dark)
cls[rows, cols] = np.where(rim | seg, 4, 6)
rows, cols = strip_box(920, 130, 1000, 170)
col[rows, cols] = radial(rows, cols, 960, 150, 34, [(0, (255, 246, 215)), (0.6, (255, 190, 90)), (1.0, (240, 110, 30)),
                                                    (9, (240, 110, 30))]); cls[rows, cols] = 3
# keep only the strip texels the gear and lens use
strip_used = np.zeros((S, S), bool); strip_used[S - 256:] = True
cls[strip_used & ~inside] = 0

# ---------------------------------------------------------------- AO grade, padding
ao = np.asarray(Image.open(T / 'hdr_ao_2k.png').convert('L'), np.float32) / 255
_, (iy, ix) = ndimage.distance_transform_edt(ao <= 0.003, return_indices=True); ao = ndimage.gaussian_filter(ao[iy, ix], 2.0)
shade = np.where((cls == 3) | strip_used, 1.0, 1 - 0.6 * (1 - ao))
col = np.clip(col * shade[..., None], 0, 1)
used = cls > 0
_, (iy, ix) = ndimage.distance_transform_edt(~used, return_indices=True)
col = col[iy, ix]; cls_pad = cls[iy, ix]; height = height[iy, ix]
Image.fromarray((col * 255 + 0.5).astype(np.uint8)).save(T / 'hdr_basecolor_2k.png')
lin_lum = RV.luminance(col)

# region mask (1K), feathered after padding
RV.write_mask([ndimage.gaussian_filter((cls_pad == k).astype(np.float32), 1.5) for k in (1, 2, 3, 4)],
              T / 'hdr_region_mask.png', 1024)
classes = np.zeros((S, S), np.uint8)
mc = {MAT['ceramic']: 11, MAT['gold']: 9, MAT['darkmetal']: 9, MAT['lens']: 6, MAT['ventband']: 9, MAT['ventglow']: 6,
      MAT['resin']: 4, MAT['chitin']: 4, MAT['bone']: 5, MAT['cable']: 11}
for k, v in mc.items():
    classes[inside & (mat == k)] = v
classes[lm] = 6
classes[inside & (part >= 5)] = np.where(cls[inside & (part >= 5)] == 4, 9, np.where(cls[inside & (part >= 5)] == 3, 6, 11))
Image.fromarray(classes[::2, ::2]).save(T / 'hdr_material_classes.png')

# normal from the painted height (glTF +Y up: green grows with height toward the image top)
h1 = ndimage.gaussian_filter(height, 1.0)
k = 2.5
dx = ndimage.sobel(h1, axis=1) / 8; dyu = -ndimage.sobel(h1, axis=0) / 8
n = np.stack([-dx * k, -dyu * k, np.ones_like(h1)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
Image.fromarray(((n * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(T / 'hdr_normal_1k.png')
rough = np.full((S, S), 0.6, np.float32)
for k_, v_ in ((1, 0.5), (2, 0.38), (3, 0.25), (4, 0.35), (5, 0.6), (6, 0.5)):
    rough[cls_pad == k_] = v_
orm = np.stack([ao[::2, ::2], rough[::2, ::2], np.zeros((1024, 1024))], -1)
Image.fromarray((orm * 255 + 0.5).astype(np.uint8)).save(T / 'hdr_metal_rough_1k.png')
g_ = np.linspace(0, 1, 128)[:, None]
thr = np.zeros((128, 32, 4), np.float32)
thr[..., 0] = 1.0; thr[..., 1] = (0.62 - 0.40 * g_); thr[..., 2] = (0.22 - 0.2 * g_); thr[..., 3] = 0.5 * (1 - g_) ** 2.0
Image.fromarray((thr * 255 + 0.5).astype(np.uint8), 'RGBA').save(T / 'hdr_thrust.png')
Image.new('RGBA', (16, 16), (255, 0, 0, 0)).save(T / 'hdr_glowmask.png')

# ramps: the v1 tier palette (compose_hdr.PAL), over this texture's region ranges
src = open(Path(__file__).with_name('compose_hdr.py')).read()
PAL = eval(src[src.index('PAL = {') + 6:src.index('\n}\n', src.index('PAL = {')) + 2])


def ramp(stops, lo, hi, values=None):
    """16 stops over the luminance range lo..hi; with `values` (the region's texel luminances) each stop takes the
    palette colour at its luminance's quantile, so a dark-skewed texture (the resin) spreads over the whole palette"""
    x = np.linspace(0, 1, 16); c_ = RV.srgb_to_linear(np.array(stops, np.float64) / 255)
    if values is not None:
        srt = np.sort(values); x = np.searchsorted(srt, lo + (hi - lo) * x) / len(srt)
    return {'range': [round(lo, 6), round(hi, 6)],
            'colors': np.round(np.stack([np.interp(x, [0, 0.5, 1], c_[:, j]) for j in range(3)], -1), 6).tolist()}


ranges, lums = {}, {}
for name, kk in (('casing', 1), ('resin', 2), ('glow', 3), ('trim', 4)):
    core = cls == kk
    lums[name] = lin_lum[core][::7]
    ranges[name] = [float(np.percentile(lin_lum[core], 2)), float(np.percentile(lin_lum[core], 98))]
variants = ['hdr_a', 'hdr_b', 'hdr_c']
QUANTILE = {'casing', 'resin', 'trim'}       # the glow keeps its painted gradient (linear)
body_ramps = {v: [ramp(PAL[r][v], *ranges[r], lums[r] if r in QUANTILE else None)
                  for r in ('casing', 'resin', 'glow', 'trim')] for v in variants}
out = {'variants': variants, 'materials': [
    {'base': 'Casing_A', 'prefix': 'Casing', 'mask': 'hdr_region_mask.png', 'ramps': body_ramps},
    {'base': 'Glow_A', 'prefix': 'Glow', 'mask': 'hdr_region_mask.png', 'ramps': body_ramps},
    {'base': 'Thrust_A', 'prefix': 'Thrust', 'mask': 'hdr_glowmask.png',
     'ramps': {v: [ramp(PAL['glow'][v], 0.25, 1.0)] for v in variants}},
], 'ranges': ranges, 'palette_srgb_stops': PAL, 'source': 'compose_v2.py (hand-built body)'}
json.dump(out, open(T / 'hdr_ramps.json', 'w'), indent=1)
print('RAMPS ranges', {k_: [round(a, 3), round(b, 3)] for k_, (a, b) in ranges.items()})
