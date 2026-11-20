#!/usr/bin/env python3
"""Textures, region masks and tier ramps for m154 (CLAUDE_CREATURE_TEXTURES.md). Run after uv_raster.py (UVMap,
HeadUV at 1024) and bake_ao_natm.py. Head set only when meshy/head_texture_v1 exists.

Tiers (dsft palettes, mm7_m154/variants.json: 202 palette 155 (base), 203 palette 156, 204 palette 157) recolour ONE
region, as the native mask does (mm7_m154/manifest.json 'regions'): R = the green tunic. The white emblem, skin, mail,
steel, brass, horns, leather, bow and arrows stay.
- Classes per texel by colour within garments (uv_raster.py): cloth = green hue; skin = warm texels of the head piece;
  gold = saturated yellow; leather = gloves, boots, belt, strap, quiver; navy = dark low saturation; steel = low
  saturation.
- Skin repainted (natm): one albedo (the median of Meshy's skin) x Meshy's fine shading, removing patch-level blotches.
- AO graded into the base colour; ORM red = per-class specular mask (openyamm_specular_mask), green = roughness.
- Ramps per tier from that tier's native pixels of the region's palette indices (stand, walk, attack, all views),
  rank-matched to the region's texel luminance (2nd-98th percentile), gain RAMP_GAIN; mask padded into the gutters.
PREVIEW=1 also writes work/classes_body.png / classes_head.png (class colours in the UV layouts) for render_tex.py.
Writes textures/m154_*."""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
NATIVE = HERE.parent / 'mm7_m154' / 'native'
PALDIR = HERE.parents[2] / 'assets_dev' / 'worlds' / 'mm7' / 'textures'
N = 1024
SKIN_MIX = 0.85; RAMP_GAIN = {'cloth': 1.3}   # blonde tier C clipped at 1.3
PALS = {'m154_a': 155, 'm154_b': 156, 'm154_c': 157}
REGION_IDX = None   # m154: the palette entries that differ between the three tiers (green cloth only)
CLASS = {'skin': 1, 'hair': 2, 'cloth': 8, 'leather': 8, 'navy': 8, 'gold': 9, 'steel': 9, 'eye': 6}
SPEC = {'skin': 0.45, 'hair': 0.3, 'cloth': 0.25, 'leather': 0.35, 'navy': 0.5, 'gold': 1.0, 'steel': 0.8, 'eye': 0.9}
ROUGH = {'skin': 0.5, 'hair': 0.6, 'cloth': 0.85, 'leather': 0.6, 'navy': 0.4, 'gold': 0.3, 'steel': 0.35, 'eye': 0.2}
PREVIEW_COL = {'skin': (230, 170, 140), 'hair': (150, 90, 20), 'cloth': (20, 200, 40), 'leather': (90, 50, 20),
               'navy': (30, 30, 160), 'gold': (250, 210, 0), 'steel': (180, 180, 190), 'eye': (255, 0, 255)}


def load(path, mode='RGB', n=N):
    im = Image.open(path).convert(mode)
    return np.asarray(im.resize((n, n), Image.LANCZOS) if im.size != (n, n) else im, np.float64) / 255


def save(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, optimize=True)


def hsv(rgb):
    h = np.asarray(Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    return h[..., 0] * 360, h[..., 1], h[..., 2]


def pad(img, cov):
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    out = img[iy, ix]; out[cov] = img[cov]; return out


def lin(x): return R.srgb_to_linear(x)
def srgb(x):
    x = np.asarray(x, np.float64); return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(np.maximum(x, 0), 1 / 2.4) - 0.055)


def repaint_skin(img, m, albedo, sigma=6.0):
    L = R.luminance(img)
    num = ndimage.gaussian_filter(np.where(m, L, 0.0), sigma); den = ndimage.gaussian_filter(m.astype(float), sigma)
    Lb = num / np.maximum(den, 1e-4)
    detail = np.clip((L / np.maximum(Lb, 1e-4)) ** 1.15, 0.5, 1.5)
    new = srgb(np.clip(lin(albedo)[None, :] * detail[m][:, None], 0, 1))
    out = img.copy(); out[m] = img[m] * (1 - SKIN_MIX) + new * SKIN_MIX
    return out


def ao_grade(img, ao, cov, strength=0.4, floor=0.45):
    f = np.clip(1 - strength + strength * np.maximum(ao, floor), 0, 1)
    out = img.copy(); out[cov] = img[cov] * f[cov][:, None]; return out


def classify(base, gar, pos, cov, head_layout, piece):
    """m154: cloth = the green tunic (the recolour region); gold = gorget and buckle; steel = low saturation (mail,
    helmet, the white tree); skin = warm texels of the head (piece 2); eyes = pieces 11/12;
    navy = dark low-saturation; leather = belt, beard, stains and the rest."""
    h, s, v = hsv(base)
    C = {}
    C['cloth'] = cov & (h > 85) & (h < 190) & (s > 0.3) & (v > 0.06)
    C['gold'] = cov & (h > 33) & (h < 62) & (s > 0.45) & (v > 0.42) & ~C['cloth']
    yellow = C['gold'].copy()
    C['gold'] &= np.isin(piece, [0, 6, 15, 17])   # m154: gorget, pauldron trim, helmet band/spike, buckle (not the olive leather)
    C['steel'] = cov & (s < 0.18) & (v > 0.35) & ~C['cloth']
    C['navy'] = cov & (s < 0.3) & (v <= 0.35) & ~C['cloth'] & ~C['steel']
    C['hair'] = np.zeros_like(cov)
    C['eye'] = cov & np.isin(piece, [11, 12])
    warm = cov & ((h < 50) | (h > 330)) & ~yellow & ~C['cloth'] & ~C['steel'] & ~C['navy'] & ~C['eye']
    C['skin'] = warm & np.isin(piece, [2]) & (s > 0.1) & (s < 0.8) & (v > 0.12)   # m154: dark skin, head only (gloves)
    for k in ('cloth', 'gold', 'steel', 'navy'):
        C[k] &= ~C['eye']
    C['leather'] = cov & ~np.any([m for m in C.values()], axis=0)
    return C


# ---------------------------------------------------------------- native region colours per tier
def pal(i):
    return np.frombuffer(open(PALDIR / f'pal{i:03d}.act', 'rb').read()[:768], np.uint8).reshape(256, 3).astype(np.float64) / 255


BASEP = (pal(155) * 255).astype(int)
LUT = {tuple(c): i for i, c in enumerate(BASEP)}
frames = sorted(p for p in NATIVE.glob('m154*.png') if p.name[4] in 'saw')
idx_pixels = []
for f in frames:
    a = np.asarray(Image.open(f).convert('RGBA'))
    m = a[..., 3] > 0
    idx_pixels.append(np.array([LUT.get(tuple(c), -1) for c in a[m][:, :3]]))
IDX = np.concatenate(idx_pixels)
import colorsys
_h = np.array([colorsys.rgb_to_hsv(*c) for c in pal(155)])
# m154: the green tunic entries: palette 155 entries that differ in 156/157 and are green
dif = np.where(((np.abs(pal(155) - pal(156)).sum(1) > 0.02) | (np.abs(pal(155) - pal(157)).sum(1) > 0.02))
               & (_h[:, 0] * 360 > 70) & (_h[:, 0] * 360 < 185) & (_h[:, 1] > 0.15))[0]
REGION_IDX = {'cloth': dif.tolist()}
print('REGION cloth palette indices', len(dif), dif.min(), dif.max())
native = {}
for reg, ids in REGION_IDX.items():
    sel = IDX[np.isin(IDX, ids)]
    for k, p in PALS.items():
        X = pal(p)[sel]; L = R.luminance(X); keep = L > 0.035
        o = np.argsort(L[keep]); native[(reg, k)] = X[keep][o]
    print('NATIVE', reg, 'pixels', len(sel), {k: np.round(np.median(native[(reg, k)], 0) * 255).tolist() for k in PALS})


def ramps_for(reg, texel_lum):
    lo, hi = np.percentile(texel_lum, [2, 98]); srt = np.sort(texel_lum)
    out = {}
    for k in PALS:
        X = native[(reg, k)]; cols = []
        for i in range(16):
            Li = lo + (hi - lo) * i / 15
            q = np.searchsorted(srt, Li) / len(srt)
            c = X[min(len(X) - 1, int(q * (len(X) - 1)))]
            cols.append([round(float(v), 6) for v in np.clip(lin(np.clip(c * RAMP_GAIN[reg], 0, 1)), 0, 1)])
        out[k] = {'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols}
    return out


def build(meshy_dir, raster, ao_png, head_layout, tag, albedo=None):
    base = load(meshy_dir / 'texture_urls_0_base_color.png'); normal = load(meshy_dir / 'texture_urls_0_normal.png')
    rough_m = load(meshy_dir / 'texture_urls_0_roughness.png', 'L')
    Rz = np.load(HERE / 'work' / raster); gar, pos = Rz['garment'], Rz['pos']; cov = gar >= 0
    C = classify(base, gar, pos, cov, head_layout, Rz['piece'])
    if os.environ.get('PREVIEW'):
        pv = np.zeros((N, N, 3), np.uint8)
        for k, m in C.items():
            pv[m] = PREVIEW_COL[k]
        Image.fromarray(pv).save(HERE / 'work' / f'classes_{tag}.png')
    if albedo is None:                                     # the head reuses the body's albedo: no neck seam
        albedo = np.median(base[C['skin']], 0) if C['skin'].sum() > 100 else np.array([0.85, 0.65, 0.55])
    g = repaint_skin(base, C['skin'], albedo)
    g = ao_grade(g, load(HERE / 'work' / ao_png, 'L'), cov)
    print('CLASSES', tag, {k: int(m.sum()) for k, m in C.items()}, 'covered', int(cov.sum()),
          'skin albedo', np.round(albedo * 255).tolist())
    cls = np.zeros((N, N), np.uint8); spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8)
    for k, m in C.items():
        if m.any():
            cls[m] = CLASS[k]; spec[m] = SPEC[k]; rgh[m] = np.clip(ROUGH[k] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
    return g, normal, spec, rgh, cls, C, cov, albedo


cfg_ramps = {}
g, normal, spec, rgh, cls, C, cov, ALB = build(HERE / 'meshy' / 'body_texture_v1', 'uvraster_UVMap.npz', 'ao_UVMap.png', False, 'body')
lum = R.luminance(g)
cloth_l = [lum[C['cloth']]]
# bowstring swatch (m214's rule): a 5x5 block of linen colour in the free texel farthest from any island; the string
# tube in the body mesh samples its centre (export_runtime.py), outside the tier region
dist = ndimage.distance_transform_edt(~cov); sy, sx = np.unravel_index(int(np.argmax(dist)), dist.shape)
blk = np.zeros_like(cov); blk[max(sy - 2, 0):sy + 3, max(sx - 2, 0):sx + 3] = True
g[blk] = np.array([218, 205, 170]) / 255; spec[blk] = 0.3; rgh[blk] = 0.7; normal[blk] = (0.5, 0.5, 1.0); cov = cov | blk
(T / 'm154_swatches.json').write_text(json.dumps({'string_uv': [(sx + 0.5) / N, 1 - (sy + 0.5) / N]}, indent=1) + '\n')
print('SWATCH string at texel', int(sx), int(sy), 'free distance', round(float(dist[sy, sx]), 1))
save(pad(g, cov), T / 'm154_basecolor_1k.png'); save(pad(normal, cov), T / 'm154_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'm154_metal_rough_1k.png')
mask = lambda m: ndimage.gaussian_filter(pad(m.astype(float), cov), 0.7)
R.write_mask([mask(C['cloth'])], T / 'm154_region_mask.png', size=N)
Image.fromarray(cls).save(T / 'm154_material_classes.png')
HM = HERE / 'meshy' / 'head_texture_v1'
if HM.exists():
    hg, hn, hspec, hrgh, hcls, HC, hcov, _ = build(HM, 'uvraster_HeadUV.npz', 'ao_HeadUV.png', True, 'head', ALB)
    hl = R.luminance(hg); cloth_l.append(hl[HC['cloth']])
    save(pad(hg, hcov), T / 'm154_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'm154_head_normal_1k.png')
    save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm154_head_metal_rough_1k.png')
    hmask = lambda m: ndimage.gaussian_filter(pad(m.astype(float), hcov), 0.7)
    R.write_mask([hmask(HC['cloth'])], T / 'm154_head_region_mask.png', size=N)
    Image.fromarray(hcls).save(T / 'm154_head_material_classes.png')
cr = ramps_for('cloth', np.concatenate(cloth_l))
ramps = {k: [cr[k]] for k in PALS}
mats = [{'base': 'M154_A', 'prefix': 'M154', 'mask': 'm154_region_mask.png', 'regions': ['cloth'], 'palettes': PALS, 'ramps': ramps}]
if HM.exists():
    mats.append({'base': 'M154Head_A', 'prefix': 'M154Head', 'mask': 'm154_head_region_mask.png', 'regions': ['cloth'],
                 'palettes': PALS, 'ramps': ramps})
(T / 'm154_ramps.json').write_text(json.dumps({'variants': list(PALS), 'materials': mats}, indent=1) + '\n')
for k in PALS:
    print('RAMP', k, 'cloth mid', [round(x, 3) for x in cr[k]['colors'][8]])
# ---------------------------------------------------------------- bow and arrow surface maps (own materials, no tier region)
for name in ('bow', 'arrow'):
    sb = np.asarray(Image.open(T / 'props' / f'{name}_basecolor.png').convert('RGB'), np.float64) / 255
    sh_, ss_, sv_ = hsv(sb)
    metal = (ss_ < 0.2) & (sv_ > 0.3)                       # arrowhead / string highlights
    spec = np.where(metal, 0.8, 0.3); rgh = np.where(metal, 0.35, 0.7)
    save(np.stack([spec, rgh, np.zeros_like(rgh)], -1), T / f'm154_{name}_metal_rough.png')
    save(np.dstack([np.full(sb.shape[:2], 0.5), np.full(sb.shape[:2], 0.5), np.ones(sb.shape[:2])]), T / f'm154_{name}_normal.png')
    Image.fromarray((sb * 255 + 0.5).astype(np.uint8)).save(T / f'm154_{name}_basecolor.png')
    print('PROP maps', name, 'metal texels', int(metal.sum()))
