#!/usr/bin/env python3
"""Textures, region mask and tier ramps for the goblin (CLAUDE_CREATURE_TEXTURES.md).

Tiers (palettes 745 Goblin / 746 Goblin Shaman / 747 Goblin King) recolour the SKIN only: one region (R), shared by
the body and the head set, so neck and face take the same colours in every tier.
- Body set (retexture_v1, Meshy's own layout, 2K -> 1K) with texel classes from the UV raster (piece, rest position)
  and colour: skin = pieces 0-2 (body skin and the foot/shin shells) in olive hues; claws = light yellow texels on
  those pieces (kept, like the native gold claws); leather, iron and gold are left as Meshy painted them, with a mild
  saturation lift on leather (Meshy desaturates).
- Head set (head_retexture_v1, HeadUV): skin = piece 0 in olive or brown (ears) hues, minus the painted eyes (near the
  removed eye shells) and light yellow texels (teeth, hoops are their own pieces and stay out); its luminance is
  matched to the body skin at the neck with one gain (a per-channel match overcorrected the first goblin's ears).
- Ramps per tier: native standing frames (gobsta0-4, palette 745) are mapped back to palette indices; the skin
  entries are those that differ between 745 and 747 (747 changes only the skin). Each tier's 16 stops are rank-matched
  to the luminance distribution of the skin texels (body + head) and scaled by RAMP_GAIN (sprites carry baked shading).
- Sword swatches (blade, edge, gold, gold_dark, grip, gem) are painted into free body-atlas texels.
Writes textures/gob2_* (base colour, normal, ORM with R=255, region masks, material classes, ramps json).
Args: none"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R

T = HERE / 'textures'; T.mkdir(exist_ok=True)
FRAMES = HERE.parent / 'mm6_goblin' / 'stage1_20261006' / 'source' / 'frames'
PALDIR = HERE.parents[2] / 'assets_dev' / 'worlds' / 'mm6' / 'textures'
N = 1024
RAMP_GAIN = 1.2
PALS = {'gob2_a': 745, 'gob2_b': 746, 'gob2_c': 747}
EYES = [np.array([0.044, -0.12, 1.508]), np.array([-0.059, -0.119, 1.508])]   # removed eye shells P25/P26 (rest pos)


def load(path, mode='RGB'):
    im = Image.open(path).convert(mode)
    return np.asarray(im.resize((N, N), Image.LANCZOS) if im.size != (N, N) else im, np.float64) / 255


def save(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, optimize=True)


def hsv(rgb):
    h = np.asarray(Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    return h[..., 0] * 360, h[..., 1], h[..., 2]


def palette(n):
    return np.frombuffer((PALDIR / f'pal{n}.act').read_bytes()[:768], np.uint8).reshape(256, 3).astype(np.float64) / 255


def linear_to_srgb(x):
    x = np.asarray(x, np.float64)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(np.maximum(x, 0), 1 / 2.4) - 0.055)


def pad(img, cov):
    """Texels outside the islands take the nearest island colour (mips must not bleed Meshy's padding)."""
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    out = img[iy, ix]; out[cov] = img[cov]
    return out


# ---------------------------------------------------------------- body set
M = HERE / 'meshy' / 'retexture_v1'
base = load(M / 'texture_urls_0_base_color.png')
rough = load(M / 'texture_urls_0_roughness.png', 'L')
normal = load(M / 'texture_urls_0_normal.png')
Rz = np.load(HERE / 'work' / 'uvraster_UVMap.npz'); piece = Rz['piece']
cov = piece >= 0
hue, sat, val = hsv(base)
skinp = np.isin(piece, [0, 1, 2])
# claws by position (a colour rule alone took 75k skin highlights): within 4 cm of a fingertip (finger_joints.json
# tips) or on the toes (foot shells below 6 cm, front half), and light yellow
FJ = json.load(open(HERE / 'work' / 'finger_joints.json'))
tips = [np.array(v) for sd in FJ.values() for n, v in sd.items() if n.endswith('_tip')]
pos = Rz['pos']
near_tip = np.zeros_like(cov)
for t_ in tips:
    near_tip |= np.linalg.norm(pos - t_, axis=-1) < 0.04
toes = np.isin(piece, [1, 2]) & (pos[..., 2] < 0.06) & (pos[..., 1] < -0.05)
claw = skinp & (near_tip | toes) & (hue > 20) & (hue < 62) & (val > 0.5) & (sat > 0.25)
# the belly skin right behind the belt buckle carries a sliver of the buckle's yellow (retexture projection): kept as
# painted, or tiers B/C turn it into a bright red/blue rim on the buckle
box = (np.abs(pos[..., 0]) < 0.1) & (pos[..., 1] < -0.08) & (pos[..., 2] > 0.85) & (pos[..., 2] < 1.0)
buckle = skinp & box & (hue > 35) & (hue < 58) & (val > 0.6) & (sat > 0.3)
buckle = ndimage.binary_dilation(buckle, iterations=2) & skinp & box
skin = skinp & ~claw & ~buckle                   # pieces 0-2 carry only skin, claws and the buckle sliver
leather = cov & (hue > 10) & (hue < 40) & (sat > 0.4) & (val < 0.55) & ~skinp
graded = base.copy()
# leather: Meshy desaturated the native's saturated brown (first goblin: H25 S0.69); lift saturation 1.2x
lum = graded[leather].mean(1, keepdims=True)
graded[leather] = np.clip(lum + (graded[leather] - lum) * 1.2, 0, 1)
print('CLASSES texels', {'skin': int(skin.sum()), 'claw': int(claw.sum()), 'buckle': int(buckle.sum()), 'leather': int(leather.sum()), 'covered': int(cov.sum())})

# ---------------------------------------------------------------- head set
HM = HERE / 'meshy' / 'head_retexture_v1'
hb = load(HM / 'texture_urls_0_base_color.png'); Rh = np.load(HERE / 'work' / 'uvraster_HeadUV.npz')
hp, hpos = Rh['piece'], Rh['pos']; hcov = hp >= 0
hh, hs_, hv = hsv(hb)
eye = np.zeros_like(hcov)
for e in EYES:
    eye |= np.linalg.norm(hpos - e, axis=-1) < 0.03
hyellow = (hh > 25) & (hh < 60) & (hv > 0.58) & (hs_ > 0.35)
hskin = (hp == 0) & ~eye & ~hyellow            # all of it: pale/grey skin left out stayed as grey streaks in B/C
# one luminance gain over the head skin so the face meets the body skin at the neck (ramps then colour both alike)
Rb = Rz['pos']
neck_b = skin & (Rb[..., 2] > 1.25) & (Rb[..., 2] < 1.40)
neck_h = hskin & (hpos[..., 2] < 1.40)
lb, lh = np.median(R.luminance((base[neck_b]))), np.median(R.luminance((hb[neck_h])))
hgain = float((lb / max(lh, 1e-4)) ** (1 / 2.2))
hg = hb.copy(); hg[hp == 0] = np.clip(hb[hp == 0] * hgain, 0, 1)
print('HEAD skin texels', int(hskin.sum()), 'eye', int(eye.sum()), 'neck luminance body/head', round(float(lb), 4),
      round(float(lh), 4), '-> gain', round(hgain, 3))

# ---------------------------------------------------------------- ramps
# Tier A keeps Meshy's own skin colour per luminance (graded toward the native olive); B and C are the palette
# transfer of A (least-squares affine map from the 745 skin entries to 746 / 747), as on the accepted first goblin.
# Rank-matching the native pixels instead copied the sprites' baked near-black shadows into the ramp (black cheeks,
# mottled skin).
pals = {k: palette(n) for k, n in PALS.items()}
_h, _s, _ = hsv(pals['gob2_a'][None])
skin_idx = np.where((np.abs(pals['gob2_a'] - pals['gob2_c']).sum(1) > 0.06) & (_h[0] > 40) & (_h[0] < 110) & (_s[0] > 0.15))[0]
src = pals['gob2_a'][skin_idx]
MAPS = {k: np.linalg.lstsq(np.c_[src, np.ones(len(src))], pals[k][skin_idx], rcond=None)[0] for k in PALS}
lut = {tuple((pals['gob2_a'][i] * 255).round().astype(int)): i for i in range(256)}
idx = []
for v in range(5):
    im = np.asarray(Image.open(FRAMES / f'gobsta{v}.png').convert('RGBA'))
    idx += [lut.get(tuple(int(c) for c in p), -1) for p in im[im[..., 3] > 128][:, :3]]
idx = np.array(idx); sel = idx[np.isin(idx, skin_idx)]
nh, ns, nv = hsv(np.median(pals['gob2_a'][sel], 0)[None, None])
print('SKIN palette entries', len(skin_idx), 'native skin median HSV', round(float(nh[0, 0])), round(float(ns[0, 0]), 2),
      round(float(nv[0, 0]), 2))
# log-luminance store (spreads the heavy-tailed skin luminance over the 16 stops; hue kept for the soft mask edge)
LO, HI = 0.01, 0.30
lb_ = R.luminance(graded[skin]); lh_ = R.luminance(hg[hskin])
allL = np.sort(np.r_[lb_, lh_]); allC = np.r_[graded[skin], hg[hskin]]
l1, l99 = np.log(np.percentile(allL, [1, 99]))
tof = lambda L: np.clip((np.log(np.maximum(L, 1e-5)) - l1) / (l99 - l1), 0, 1)
allT = tof(np.r_[lb_, lh_])


def store(img, m, L):
    tgt = LO + tof(L) * (HI - LO)
    lin = R.srgb_to_linear(img[m]) * (tgt / np.maximum(L, 1e-5))[:, None]
    img[m] = np.clip(linear_to_srgb(np.clip(lin, 0, 1)), 0, 1)


th, ts_, _ = hsv(np.median(allC, 0)[None, None]); th, ts_ = float(th[0, 0]), float(ts_[0, 0])
# in game a 60 % grade read dull olive against the grass (first goblin, revision 8: as flat as the grass): full hue and
# saturation shift to the native skin median, and the stops' value spread around the median raised 1.4x (form contrast)
HUE_SHIFT = float(nh[0, 0]) - th; SAT_GAIN = float(ns[0, 0]) / ts_; CONTRAST = 1.4
v_med = float(hsv(np.median(allC, 0)[None, None])[2][0, 0])
a_stops = []
for i in range(16):
    m = np.abs(allT - i / 15) < 0.5 / 15
    c = np.median(allC[m], 0) if m.sum() > 20 else (a_stops[-1] if a_stops else np.median(allC, 0))
    h_, s2, v_ = (x[0, 0] for x in hsv(c[None, None]))
    v_ = v_med * (max(v_, 1e-3) / v_med) ** CONTRAST
    rgb = np.asarray(Image.fromarray(np.uint8(np.clip([[[(h_ + HUE_SHIFT) % 360 / 360, min(s2 * SAT_GAIN, 1), v_]]], 0, 1) * 255),
                                     'HSV').convert('RGB'), np.float64)[0, 0] / 255
    a_stops.append(rgb)
store(graded, skin, lb_); store(hg, hskin, lh_)
lo, hi = LO, HI
ramps = {}
for k in PALS:
    cols = [np.clip(np.r_[c, 1] @ MAPS[k], 0, 1) for c in a_stops]
    ramps[k] = [{'range': [lo, hi], 'colors': [[round(float(x), 6) for x in R.srgb_to_linear(c)] for c in cols]}]
print('GRADE A skin: texture median hue', round(th), 'sat', round(ts_, 2), '-> hue shift', round(HUE_SHIFT, 1), 'sat gain', round(SAT_GAIN, 2))
RAMP_GAIN = 1.0
report = {'native_skin_pixels': int(len(sel)), 'skin_texels_body': int(skin.sum()), 'skin_texels_head': int(hskin.sum()),
          'range': [float(lo), float(hi)], 'ramp_gain': RAMP_GAIN}
print('RAMPS', report)

# ---------------------------------------------------------------- sword swatches in free body texels (6 px clear)
occ = ndimage.binary_dilation(cov, iterations=6)
SW = {'blade': (196, 186, 190), 'edge': (236, 232, 234), 'gold': (214, 160, 40), 'gold_dark': (150, 100, 20),
      'grip': (78, 44, 24), 'gem': (150, 14, 16)}         # native gobsta2: pale pinkish steel, gold hilt, red jewels
swatches, r_px = {}, 5
swatch_px = np.zeros((N, N), bool)                # kept out of the padded skin mask
y, x = N - 10, N - 10
graded = pad(graded, cov); normal = pad(normal, cov); rough = pad(rough, cov)
for name, rgb in SW.items():
    while occ[y - r_px:y + r_px, x - r_px:x + r_px].any():
        x -= 4
        if x < 12:
            x, y = N - 10, y - 4
    graded[y - r_px:y + r_px, x - r_px:x + r_px] = np.array(rgb) / 255
    rough[y - r_px:y + r_px, x - r_px:x + r_px] = 0.35 if name != 'grip' else 0.8
    normal[y - r_px:y + r_px, x - r_px:x + r_px] = (0.5, 0.5, 1.0)
    occ[y - r_px - 3:y + r_px + 3, x - r_px - 3:x + r_px + 3] = True
    swatch_px[y - r_px - 3:y + r_px + 3, x - r_px - 3:x + r_px + 3] = True
    swatches[name] = [(x + 0.5) / N, 1 - (y + 0.5) / N, (r_px - 2) / N]
(T / 'gob2_sword_swatches.json').write_text(json.dumps(swatches, indent=1) + '\n')

# ---------------------------------------------------------------- write
save(graded, T / 'gob2_basecolor_1k.png'); save(normal, T / 'gob2_normal_1k.png')
save(np.stack([np.ones_like(rough), rough, np.zeros_like(rough)], -1), T / 'gob2_metal_rough_1k.png')
# the mask is padded like the colour: a mask that stopped at the island edges left the gutters (and the cracks between
# carried UV faces) unrecoloured, and filtering drew them as olive lines along every seam on tiers B/C
skin_m = pad(skin.astype(float), cov); skin_m[swatch_px] = 0
R.write_mask([ndimage.gaussian_filter(skin_m, 0.7)], T / 'gob2_region_mask.png', size=N)
cmap = np.zeros((N, N), np.uint8); cmap[cov] = 11
cmap[cov & (sat < 0.15)] = 9; cmap[leather] = 8; cmap[skin] = 1; cmap[claw] = 4
Image.fromarray(cmap).save(T / 'gob2_material_classes.png')
hg = pad(hg, hcov)
save(hg, T / 'gob2_head_basecolor_1k.png')
save(pad(load(HM / 'texture_urls_0_normal.png'), hcov), T / 'gob2_head_normal_1k.png')
hr = pad(load(HM / 'texture_urls_0_roughness.png', 'L'), hcov)
save(np.stack([np.ones_like(hr), hr, np.zeros_like(hr)], -1), T / 'gob2_head_metal_rough_1k.png')
R.write_mask([ndimage.gaussian_filter(pad(hskin.astype(float), hcov), 0.7)], T / 'gob2_head_region_mask.png', size=N)
hc = np.zeros((N, N), np.uint8); hc[hcov] = 11; hc[hskin] = 1; hc[eye & hcov] = 6
hc[np.isin(hp, [5, 6, 12, 13])] = 9; hc[np.isin(hp, list(range(60, 79)))] = 5
Image.fromarray(hc).save(T / 'gob2_head_material_classes.png')
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Goblin_A', 'prefix': 'Goblin', 'mask': 'gob2_region_mask.png', 'regions': ['skin'],
                      'palettes': PALS, 'ramps': ramps, 'report': report},
                     {'base': 'GoblinHead_A', 'prefix': 'GoblinHead', 'mask': 'gob2_head_region_mask.png',
                      'regions': ['skin'], 'palettes': PALS, 'ramps': ramps}]}
(T / 'gob2_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
