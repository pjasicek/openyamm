#!/usr/bin/env python3
"""Textures and rank tiers of the Landfall Guard (CLAUDE_CREATURE_TEXTURES.md). Run after uv_raster.py (UVMap,
HeadUV at 1024) and bake_ao_natm.py.
- Classes per texel (Meshy's paint + the piece raster): eye (pieces 17, 19), skin (warm texels of the head piece),
  hair (dark texels of the head piece under the helmet), metal (gold: hue 35-62, saturated, bright), other = the white
  Ancient ceramic of the plates, helmet and emitter housing (low saturation, bright; class 11, glazed: specular 0.5,
  roughness 0.4), cloth (the coat, trousers, tabard, gloves, belt and pouches).
- AO multiplied into the base colour (strength 0.4, floor 0.45). ORM: R per-class specular mask, G roughness, B 0.
- Region mask (one shared texture, per-tier ramps; the head set has no regions and is shared by all ranks):
  R the slate-blue coat and trousers (blue cloth), G the red tabard (red cloth), B the gold trim outside the tabard
  (helmet band, plate edging, buckle, rivets) - gold within TAB_GAP texels of the tabard (its glyph and hem border)
  stays out, so both read on every rank; the ceramic, gloves, belt, emitter and skin are in no region. Each channel is
  feathered by a 1.5-texel blur and padded into the gutters like the colour (no tier-A lines along the seams).
- Ramps (claude_shared/region_variants.fit_ramps): guard_a fitted to the texture itself; guard_b / guard_c to the
  texture recoloured per region by RANKS (the region's colour scaled by each texel's luminance against the region's
  median, so the shading and wear are kept).
Writes textures/hgd_* (body and head 1K sets, material classes, region mask, hgd_ramps.json, tier previews)."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as rv
T = HERE / 'textures'; T.mkdir(exist_ok=True)
N = 1024
SPEC = {'skin': 0.3, 'hair': 0.25, 'cloth': 0.25, 'metal': 0.85, 'eye': 0.9, 'ceramic': 0.5}
ROUGH = {'skin': 0.6, 'hair': 0.55, 'cloth': 0.75, 'metal': 0.3, 'eye': 0.2, 'ceramic': 0.4}
CLASS = {'skin': 1, 'hair': 2, 'cloth': 8, 'metal': 9, 'eye': 6, 'ceramic': 11}
EYE_PIECES, HEAD_PIECE = {17, 19}, 4
TAB_GAP = 7
# rank colours (sRGB) per region: R coat, G tabard, B gold trim; guard_a is the texture itself
RANKS = {'guard_b': {'R': (0.25, 0.31, 0.29), 'G': None, 'B': None},            # Guard Sergeant: dark slate grey-green coat
         'guard_c': {'R': (0.06, 0.08, 0.19), 'G': (0.90, 0.88, 0.82), 'B': (0.98, 0.80, 0.30)}}   # Warden's Guard
VARIANTS = ['guard_a', 'guard_b', 'guard_c']


def load(path, mode='RGB', n=N):
    im = Image.open(path).convert(mode)
    return np.asarray(im.resize((n, n), Image.LANCZOS) if im.size != (n, n) else im, np.float64) / 255


def save(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, optimize=True)


def pad(img, cov):
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    out = img[iy, ix]; out[cov] = img[cov]; return out


def hsv(rgb):
    h = np.asarray(Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    return h[..., 0] * 360, h[..., 1], h[..., 2]


def compose(job, raster, ao_png):
    Rz = np.load(HERE / 'work' / raster); pc = Rz['piece']; cov = pc >= 0
    base = load(HERE / 'meshy' / job / 'texture_urls_0_base_color.png')
    rough_m = load(HERE / 'meshy' / job / 'texture_urls_0_roughness.png', 'L')
    h, s, v = hsv(base)
    C = {}
    C['eye'] = cov & np.isin(pc, list(EYE_PIECES))
    head = cov & (pc == HEAD_PIECE)
    C['skin'] = head & (h < 35) & (s > 0.18) & (s < 0.7) & (v > 0.3)
    C['hair'] = head & ~C['skin'] & (v < 0.45)
    rest = cov & ~C['eye'] & ~C['skin'] & ~C['hair']
    C['metal'] = rest & (h >= 35) & (h <= 62) & (s > 0.4) & (v > 0.4)
    C['ceramic'] = rest & ~C['metal'] & (s < 0.22) & (v > 0.62)
    C['cloth'] = rest & ~C['metal'] & ~C['ceramic']
    ao = load(HERE / 'work' / ao_png, 'L')
    f = np.clip(1 - 0.4 + 0.4 * np.maximum(ao, 0.45), 0, 1)
    g = base.copy(); g[cov] = base[cov] * f[cov][:, None]
    cls = np.zeros((N, N), np.uint8); spec = np.zeros((N, N)); rgh = np.full((N, N), 0.7)
    for name, m in C.items():
        if m.any():
            cls[m] = CLASS[name]; spec[m] = SPEC[name]
            rgh[m] = np.clip(ROUGH[name] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
    print('CLASSES', job, {n: int(m.sum()) for n, m in C.items()}, 'covered', int(cov.sum()))
    return g, cls, spec, rgh, cov, C, pc


out = {}
for job, raster, ao, pre in (('body_texture_v1', 'uvraster_UVMap.npz', 'ao_UVMap.png', 'hgd'),
                             ('head_texture_v1', 'uvraster_HeadUV.npz', 'ao_HeadUV.png', 'hgd_head')):
    out[pre] = compose(job, raster, ao)
for job, pre in (('body_texture_v1', 'hgd'), ('head_texture_v1', 'hgd_head')):
    g, cls, spec, rgh, cov, C, pc = out[pre]
    save(pad(g, cov), T / f'{pre}_basecolor_1k.png')
    save(pad(load(HERE / 'meshy' / job / 'texture_urls_0_normal.png'), cov), T / f'{pre}_normal_1k.png')
    save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / f'{pre}_metal_rough_1k.png')
    Image.fromarray(cls).save(T / f'{pre}_material_classes.png')

# ---------------------------------------------------------------- rank regions on the body set
g, cls, spec, rgh, cov, C, pc = out['hgd']
base = load(T / 'hgd_basecolor_1k.png'); h, s, v = hsv(base)
cloth = C['cloth'] & ~np.isin(pc, (5, 7, 26))                  # not the helmet's lens or the emitter's
blue = cloth & (h >= 195) & (h <= 260) & (s > 0.28) & (v < 0.85)
red = cloth & ((h < 16) | (h > 340)) & (s > 0.42) & (v > 0.18)
red = ndimage.binary_opening(red, iterations=1)
near_tab = ndimage.binary_dilation(red, iterations=TAB_GAP)
gold = C['metal'] & ~near_tab
regions = {}
for key, m in (('R', blue), ('G', red), ('B', gold)):
    w = ndimage.gaussian_filter(m.astype(np.float64), 1.5)
    w = np.where(cov, np.maximum(w, m), 0.0)
    regions[key] = pad(w, cov)                                  # gutters take the nearest island's weight
lum = rv.luminance(base)
tiers = {'guard_a': base}
for t, cols in RANKS.items():
    img = base.copy()
    for key, col in cols.items():
        if col is None:
            continue
        core = regions[key] > 0.9
        rel = lum / max(float(np.median(lum[core])), 1e-4)
        target = rv.srgb_to_linear(np.array(col))[None, None, :] * np.clip(rel, 0.25, 2.2)[..., None]
        enc = np.where(target <= 0.0031308, target * 12.92, 1.055 * np.maximum(target, 0) ** (1 / 2.4) - 0.055)
        img = np.where(core[..., None], np.clip(enc, 0, 1), img)
    tiers[t] = img
# a rank whose colour for a region is None keeps the texture there; a trailing region without a ramp is ignored by the
# loader, so ranks A and B carry no gold ramp (gold's hue varies with its shading: a luminance ramp misses it by p95
# 18 levels) and keep Meshy's gold exactly; R and G always carry a ramp (the channel order needs them)
NEEDS = {'guard_a': ('R', 'G'), 'guard_b': ('R', 'G'), 'guard_c': ('R', 'G', 'B')}
ramps = {vname: [] for vname in VARIANTS}; report = {}
for key in ('R', 'G', 'B'):
    r, rep = rv.fit_ramps(base, tiers, regions[key])
    for vname in VARIANTS:
        if key in NEEDS[vname]:
            ramps[vname].append(r[vname])
    report[key] = rep
rv.write_mask([regions['R'], regions['G'], regions['B']], T / 'hgd_region_mask.png', N)
json.dump({'variants': VARIANTS,
           'materials': [{'base': 'HGD_A', 'prefix': 'HGD', 'mask': 'hgd_region_mask.png', 'ramps': ramps}],
           'ranks': {'guard_a': '10067 Landfall Guard', 'guard_b': '10068 Guard Sergeant', 'guard_c': "10069 Warden's Guard"},
           'regions': {'R': 'coat and trousers', 'G': 'tabard', 'B': 'gold trim outside the tabard'},
           'fit_report': report}, open(T / 'hgd_ramps.json', 'w'), indent=1)
print('REGIONS texels', {k: int((w > 0.9).sum()) for k, w in regions.items()})
print('RAMPFIT', json.dumps(report))
# previews: the shader's mix per tier
lin = rv.srgb_to_linear(base)
for vname in VARIANTS:
    col = lin.copy()
    for k, key in enumerate(('R', 'G', 'B')[:len(ramps[vname])]):
        rp = ramps[vname][k]; lo, hi = rp['range']; stops = np.array(rp['colors'])
        tt = np.clip((rv.luminance(base) - lo) / (hi - lo), 0, 1) * 15
        i0 = np.minimum(np.floor(tt).astype(int), 14); fr = (tt - i0)[..., None]
        rc = stops[i0] * (1 - fr) + stops[i0 + 1] * fr
        col = col * (1 - regions[key][..., None]) + rc * regions[key][..., None]
    enc = np.where(col <= 0.0031308, col * 12.92, 1.055 * np.maximum(col, 0) ** (1 / 2.4) - 0.055)
    save(enc, HERE / 'work' / f'tierprev_{vname}.png')
