#!/usr/bin/env python3
"""Textures, region masks and tier ramps for the barbarian (CLAUDE_CREATURE_TEXTURES.md).

Body set (Meshy retexture_v1, its own UV layout, 2K -> 1K): texel classes from the UV raster (piece, rest position)
and the texture's colour:
- skin: pieces 0 and 2 (the leggings shell is the legs' skin), not gauntlet; leather: gauntlets (piece 0, forearm/hand
  region, dark), boots (3, 4, dark), belt and flap (6, dark), choker/straps leather; armour: cups (5, not gold trim),
  scale panel (7), fur cuffs (3, 4: light and unsaturated); gold: pauldrons (8, 9), armlets (10, 12), choker (11),
  buckle (13), trim and studs (yellow hue); hair: piece 1.
- grading (unchanged classes): each class's colour is scaled per channel so its median matches the native tier-A
  class colour x ALBEDO (sprites carry baked shading); the texture's own detail (ratio to the class median) stays.
- regions (recoloured per tier): R = armour, G = leather; ramps from the native pixels that change between palettes,
  split by their tier-B colour (armour turns blue, leather burgundy), sorted by tier-A luminance, 16 quantiles x ALBEDO.
Head set (head_retexture_v1, HeadUV, 2K -> 1K) when present: graded like the skin; no recoloured regions (all-zero
mask, the body's ramps, as merge_head_material.py requires).
Skin read as clay (user, 2026-10-10): an even albedo with no specular. Now the rest-pose AO (work/ao_body.png,
scripts/bake_ao.py) darkens creases in the body base colour (AO_STRENGTH), and the ORM carries a per-class specular
mask in R (the material uses "openyamm_specular_mask") and per-class roughness in G (Meshy's roughness detail kept
around the class value); B (metallic) stays 0, so metal keeps its base colour. Also writes the material class map.
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
NAT = HERE.parent / 'mm6_bar1' / 'native_variants'
N = 1024
ALBEDO = 1.15
AO_STRENGTH, AO_FLOOR = 0.5, 0.3
# per class: (specular mask, roughness); skin gets a soft sheen like the sprites' oiled skin, metal a tight glint
SURFACE = {'skin': (0.45, 0.5), 'hair': (0.3, 0.55), 'leather': (0.35, 0.6), 'armour': (0.8, 0.35),
           'gold': (1.0, 0.3), 'fur': (0.1, 0.9), 'other': (0.3, 0.6)}
RAMP_GAIN = 1.3                     # playbook: 1.3-1.45 x native (sprites carry baked shading)
PALS = {'bar1_a': 663, 'bar1_b': 664, 'bar1_c': 665}
TARGET = {'skin': (156, 100, 61), 'hair': (82, 16, 4), 'gold': (190, 145, 62)}   # native tier-A medians (hair lifted,
# gold less saturated: the sprite median (205, 153, 30) turned the metal lemon-yellow)


def load(path, mode='RGB'):
    im = Image.open(path).convert(mode)
    return np.asarray(im.resize((N, N), Image.LANCZOS) if im.size != (N, N) else im, np.float64) / 255


def save(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, optimize=True)


def hsv(rgb):
    return np.asarray(Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255


M = HERE / 'meshy' / 'retexture_v1'
base = load(M / 'texture_urls_0_base_color.png')
rough = load(M / 'texture_urls_0_roughness.png', 'L')
normal = load(M / 'texture_urls_0_normal.png')
Rz = np.load(HERE / 'work' / 'uvraster_UVMap.npz')
piece, pos = Rz['piece'], Rz['pos']
H = hsv(base); hue, sat, val = H[..., 0] * 360, H[..., 1], H[..., 2]
cov = piece >= 0
arm_zone = (np.abs(pos[..., 0]) > 0.22) & (pos[..., 2] < 1.27)                 # forearms and hands (A-pose)
dark = val < 0.33
yellow = (hue > 36) & (hue < 62) & (sat > 0.3) & (val > 0.55)
cls = {}
# the cups' gold rim (piece 5) and the scale panel cannot be told apart from the pale-gold metal by colour: the
# whole of pieces 5 and 7 is armour (known fault: the thin rim follows the tier colour)
cls['gold'] = cov & (np.isin(piece, [8, 9, 10, 11, 12, 13]) | (np.isin(piece, [3, 4, 6]) & yellow))
cls['fur'] = cov & np.isin(piece, [3, 4]) & (sat < 0.25) & (val > 0.42) & (pos[..., 2] > 0.38)
cls['leather'] = cov & ~cls['gold'] & ((np.isin(piece, [3, 4, 6]) & ~cls['fur']) | ((piece == 0) & arm_zone & dark))
cls['armour'] = cov & ~cls['gold'] & np.isin(piece, [5, 7]) | cls['fur']
cls['hair'] = cov & (piece == 1)
cls['skin'] = cov & np.isin(piece, [0, 2]) & ~cls['leather'] & ~cls['gold']
cls['other'] = cov & ~np.any([cls[k] for k in ('gold', 'fur', 'leather', 'armour', 'hair', 'skin')], axis=0)
print('CLASSES texels', {k: int(v.sum()) for k, v in cls.items()})

graded = base.copy()
for k, tgt in TARGET.items():
    m = cls[k]
    med = np.median(base[m], 0)
    gain = np.array(tgt) / 255 * ALBEDO / np.maximum(med, 1e-3)
    graded[m] = base[m] * gain
    print('GRADE', k, 'median', np.round(med * 255).astype(int), '-> gain', np.round(gain, 2))
ao = load(HERE / 'work' / 'ao_body.png', 'L')
graded *= (1 - AO_STRENGTH * (1 - np.maximum(ao, AO_FLOOR)))[..., None]
graded = np.clip(graded, 0, 1)


def surface_maps(classes, meshy_rough, shape):
    """R specular mask and G roughness per class (Meshy's roughness detail kept around the class value); texels
    outside every class take the nearest class's values so mips do not blend in other values."""
    spec, rgh, known = np.zeros(shape), np.zeros(shape), np.zeros(shape, bool)
    for k, m in classes.items():
        if not m.any():
            continue
        sm, rv = SURFACE[k]
        spec[m] = sm
        rgh[m] = np.clip(rv + 0.5 * (meshy_rough[m] - np.median(meshy_rough[m])), 0.2, 1.0)
        known |= m
    idx = ndimage.distance_transform_edt(~known, return_distances=False, return_indices=True)
    return spec[tuple(idx)], rgh[tuple(idx)]

# ---------------------------------------------------------------- regions and ramps
w_arm = ndimage.gaussian_filter(cls['armour'].astype(float), 0.7)
w_lea = ndimage.gaussian_filter(cls['leather'].astype(float), 0.7)
R.write_mask([w_arm, w_lea], T / 'bar1_region_mask.png', size=N)
cols = {k: [] for k in PALS}; groups = []
for v in range(5):
    ims = {k: np.asarray(Image.open(NAT / f'bar1sta{v}_{p}.png').convert('RGBA'), np.float64) / 255 for k, p in PALS.items()}
    a = ims['bar1_a']; al = a[..., 3] > 0.5
    d = np.maximum(np.abs(ims['bar1_b'][..., :3] - a[..., :3]).max(-1), np.abs(ims['bar1_c'][..., :3] - a[..., :3]).max(-1))
    ch = al & (d > 8 / 255)
    b = ims['bar1_b'][..., :3]
    g = np.where(b[..., 2] > b[..., 0], 0, 1)[ch]                              # tier B: blue = armour, red = leather
    sharp = (ims['bar1_b'][..., :3][ch].max(-1) > 0.85) & (np.abs(b[ch][:, 0] - b[ch][:, 2]) < 0.05)
    g[sharp] = -1                                                               # the bright blade (keeps its colour)
    groups.append(g)
    for k in PALS:
        cols[k].append(ims[k][..., :3][ch])
groups = np.concatenate(groups); cols = {k: np.concatenate(v) for k, v in cols.items()}
LUMA = np.array([0.2126, 0.7152, 0.0722])
qs = np.linspace(0.03, 0.97, 16)
ramps = {k: [] for k in PALS}
report = {}
for ri, (name, m_tex) in enumerate((('armour', cls['armour']), ('leather', cls['leather']))):
    # native pixels of this region, without the sprite's near-black outline/antialias pixels
    sel = (groups == ri) & (cols['bar1_a'].max(1) > 0.06)
    lin_a = R.srgb_to_linear(cols['bar1_a'][sel]); order = np.argsort(lin_a @ LUMA)
    lum = np.sort(R.luminance(graded)[m_tex])
    lo, hi = np.percentile(lum, [2, 98])
    for k in PALS:
        lin = R.srgb_to_linear(cols[k][sel])[order]
        stops = []
        for i in range(16):
            # rank matching: the stop at luminance lo + t (hi - lo) takes the native colour at the same quantile that
            # luminance has among the region's texels (a linear t-to-quantile map left most texels on the dark stops)
            q = np.searchsorted(lum, lo + i / 15 * (hi - lo)) / len(lum)
            q = min(max(q, 0.02), 0.98)
            c = int(q * (len(lin) - 1)); w = max(4, len(lin) // 40)
            stops.append(np.clip(np.median(lin[max(0, c - w):c + w], 0) * RAMP_GAIN, 0, 1))
        ramps[k].append({'range': [round(float(lo), 6), round(float(hi), 6)], 'colors': [[round(float(x), 6) for x in s] for s in stops]})
    report[name] = {'native_pixels': int(sel.sum()), 'texels': int(m_tex.sum()), 'range': [float(lo), float(hi)]}
print('RAMPS', report)

# ---------------------------------------------------------------- sword swatches in free texels (6 px clear)
occ = ndimage.binary_dilation(cov, iterations=6)
SW = {'blade': (205, 212, 220), 'edge': (240, 244, 248), 'gold': (214, 160, 40), 'gold_dark': (150, 100, 20),
      'grip': (70, 40, 26), 'gem': (30, 20, 40)}
swatches, r_px, swatch_rects = {}, 5, []
y, x = N - 10, N - 10
for name, rgb in SW.items():
    while occ[y - r_px:y + r_px, x - r_px:x + r_px].any():
        x -= 4
        if x < 12:
            x, y = N - 10, y - 4
    graded[y - r_px:y + r_px, x - r_px:x + r_px] = np.array(rgb) / 255
    metal = name in ('blade', 'edge', 'gold', 'gold_dark', 'gem')
    rough[y - r_px:y + r_px, x - r_px:x + r_px] = 0.35 if metal else 0.8
    swatch_rects.append((slice(y - r_px, y + r_px), slice(x - r_px, x + r_px), 1.0 if metal else 0.3))
    normal[y - r_px:y + r_px, x - r_px:x + r_px] = (0.5, 0.5, 1.0)
    occ[y - r_px - 3:y + r_px + 3, x - r_px - 3:x + r_px + 3] = True
    swatches[name] = [(x + 0.5) / N, 1 - (y + 0.5) / N, (r_px - 2) / N]
(T / 'bar1_sword_swatches.json').write_text(json.dumps(swatches, indent=1) + '\n')
# ---------------------------------------------------------------- write the body set
save(graded, T / 'bar1_basecolor_1k.png'); save(normal, T / 'bar1_normal_1k.png')
spec_r, rough_g = surface_maps({k: cls[k] for k in SURFACE}, rough, (N, N))
for ys, xs, sm in swatch_rects:                                     # the sword's swatches keep their own surface
    spec_r[ys, xs] = sm; rough_g[ys, xs] = rough[ys, xs]
save(np.stack([spec_r, rough_g, np.zeros_like(rough)], -1), T / 'bar1_metal_rough_1k.png')
cmap = np.zeros((N, N), np.uint8)
for k, lab in (('skin', 1), ('hair', 2), ('leather', 8), ('armour', 9), ('gold', 9), ('fur', 2), ('other', 11)):
    cmap[cls[k]] = lab
Image.fromarray(cmap).save(T / 'bar1_material_classes.png')
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Barbarian_A', 'prefix': 'Barbarian', 'mask': 'bar1_region_mask.png', 'regions': ['armour', 'leather'],
                      'palettes': PALS, 'ramps': ramps, 'report': report}]}
# ---------------------------------------------------------------- head set (optional)
HM = HERE / 'meshy' / 'head_retexture_v1'
if (HM / 'texture_urls_0_base_color.png').exists():
    hb = load(HM / 'texture_urls_0_base_color.png'); Rh = np.load(HERE / 'work' / 'uvraster_HeadUV.npz')
    hp = Rh['piece']; HH = hsv(hb)
    hh, hs_, hv = HH[..., 0] * 360, HH[..., 1], HH[..., 2]
    # skin tones only: Meshy also painted hair onto the scalp (hidden under the hair shell; very saturated dark red)
    hskin = (hp == 0) & (hh > 8) & (hh < 40) & (hs_ > 0.15) & (hs_ < 0.7) & (hv > 0.3)
    print('HEAD skin median', np.round(np.median(hb[hskin], 0) * 255).astype(int))
    hgold = (hp >= 0) & ~hskin & (HH[..., 0] * 360 > 36) & (HH[..., 1] > 0.3)
    hg = hb.copy()
    # the head skin is matched to the GRADED body skin at the neck seam (same ramps-free class, one gain)
    body_neck = cls['skin'] & (pos[..., 2] > 1.36)
    tgt = np.median(graded[body_neck], 0) if body_neck.any() else np.array(TARGET['skin']) / 255 * ALBEDO
    gain = tgt / np.maximum(np.median(hb[hskin], 0), 1e-3)
    face = (hp == 0)                                               # one gain over the whole face/scalp shell (no seams)
    hg[face] = hb[face] * gain
    print('HEAD gain', np.round(gain, 2), 'target', np.round(tgt * 255).astype(int))
    if hgold.any():
        hg[hgold] = hb[hgold] * (np.array(TARGET['gold']) / 255 * ALBEDO / np.maximum(np.median(hb[hgold], 0), 1e-3))
    save(np.clip(hg, 0, 1), T / 'bar1_head_basecolor_1k.png')
    save(load(HM / 'texture_urls_0_normal.png'), T / 'bar1_head_normal_1k.png')
    hr = load(HM / 'texture_urls_0_roughness.png', 'L')
    hother = (hp >= 0) & ~hskin & ~hgold
    hspec, hrough = surface_maps({'skin': hskin, 'gold': hgold, 'other': hother}, hr, (N, N))
    save(np.stack([hspec, hrough, np.zeros_like(hr)], -1), T / 'bar1_head_metal_rough_1k.png')
    R.write_mask([np.zeros((N, N)), np.zeros((N, N))], T / 'bar1_head_region_mask.png', size=N)
    cfg['materials'].append({'base': 'BarbarianHead_A', 'prefix': 'BarbarianHead', 'mask': 'bar1_head_region_mask.png',
                             'regions': ['armour', 'leather'], 'palettes': PALS, 'ramps': ramps})
    print('HEAD graded: skin texels', int(hskin.sum()), 'gold', int(hgold.sum()))
(T / 'bar1_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
