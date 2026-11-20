#!/usr/bin/env python3
"""Textures, region masks and tier ramps for m442, the MM7 female goblin peasant (CLAUDE_CREATURE_TEXTURES.md). Run
after uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py.

Nine variants (outfits A/B/C x tiers A/B/C = descriptors 430..438 'Peasant Goblin female <o> <t>', palettes 139, 141,
145, 146, 147, 148, 149, 390, 391; the native frames are drawn in 141 = m442_ab, mm7_m442/variants.json) recolour TWO
regions, as the native masks do: R = the purple cloth (vest stripes, trousers; variants.json 'purple_clothing'
indices), G = the hair (variants.json 'hair' indices 118..145). Green skin, the cream blouse/sash, red ribbon, boots,
brass and the sickle stay.
- Classes per texel by piece and colour: cloth = purple hue; linen = cream/white; skin = olive-green; leather = brown
  (boots); brass = saturated yellow; ribbon = red (pieces 6/7/8/45 and red texels); hair = the fringe (P03) and the
  dark texels of the head layout above the eyes (scalp, ponytail); eyes = P04/P05.
- Skin and hair repainted (natm): one albedo x Meshy's fine shading. AO graded; ORM red = per-class specular mask,
  green = roughness. Sickle maps from textures/props/sickle_basecolor.png (steel, wood, brass by colour).
- Ramps per tier from that tier's native pixels of the region's palette indices (stand and walk, all views), rank-
  matched inside a native quantile window (QWIN); masks padded into the gutters. PREVIEW=1 writes class previews.
Writes textures/m442_*."""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
NATIVE = HERE.parent / 'mm7_m442' / 'native'
PALDIR = HERE.parents[2] / 'assets_dev' / 'worlds' / 'mm7' / 'textures'
N = 1024
SKIN_MIX = 0.85
RAMP_GAIN = {'cloth': 1.3, 'hair': 1.25}
# texel luminance (2nd-98th pct) -> native quantile window: the sprite's baked deep shadows (tunic) stretched across
# Meshy's narrow cloth range turned its mottling into dark patches
QWIN = {'cloth': (0.3, 0.97), 'hair': (0.1, 0.99)}
PALS = [139, 141, 145, 146, 147, 148, 149, 390, 391]          # descriptors 430..438
VARIANTS = {f'm442_{o}{t}': PALS[3 * i + j] for i, o in enumerate('abc') for j, t in enumerate('abc')}
REGIONS = ['cloth', 'hair']
_V = {r['name']: r for r in json.load(open(HERE.parent / 'mm7_m442' / 'variants.json'))['regions']}
REGION_IDX = {'cloth': sorted(_V['purple_clothing']['palette_indices']),
              'hair': sorted(_V['hair']['native_palette_spatial_support'])}
CLASS = {'skin': 1, 'hair': 2, 'cloth': 8, 'linen': 8, 'leather': 8, 'ribbon': 8, 'brass': 9, 'eye': 6}
SPEC = {'skin': 0.45, 'hair': 0.3, 'cloth': 0.2, 'ribbon': 0.3, 'linen': 0.2, 'leather': 0.35, 'brass': 1.0, 'eye': 0.9}
ROUGH = {'skin': 0.5, 'hair': 0.6, 'cloth': 0.85, 'ribbon': 0.7, 'linen': 0.85, 'leather': 0.6, 'brass': 0.3, 'eye': 0.2}
PREVIEW_COL = {'skin': (100, 200, 60), 'hair': (150, 90, 20), 'ribbon': (255, 0, 0), 'cloth': (120, 40, 220),
               'linen': (200, 200, 170), 'leather': (90, 50, 20), 'brass': (250, 210, 0), 'eye': (255, 0, 255)}


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
    h, s, v = hsv(base)
    C = {}
    C['eye'] = cov & np.isin(piece, [4, 5])
    C['ribbon'] = cov & (np.isin(piece, [6, 7, 8, 45]) | ((h < 15) | (h > 340)) & (s > 0.55) & (v > 0.3)) & ~C['eye']
    C['brass'] = cov & (gar == 7) & ~C['ribbon'] | cov & (h > 35) & (h < 62) & (s > 0.45) & (v > 0.45) & ~C['eye']
    C['cloth'] = cov & (h > 235) & (h < 310) & (s > 0.2) & ~C['ribbon']
    dark = (v < 0.3) & (s < 0.5)
    hairpos = (pos[..., 2] > EYE_Z + 0.01) | ((pos[..., 1] > HEAD_Y - 0.015) & (pos[..., 2] > EYE_Z - 0.25))   # scalp, ponytail behind
    C['hair'] = cov & ((piece == 3) | ((piece == 0) & dark & hairpos)) & ~C['ribbon'] & ~C['cloth']
    C['skin'] = cov & np.isin(piece, [0, 1, 2]) & (h > 55) & (h < 140) & (s > 0.15) & ~C['hair']
    C['linen'] = cov & (s < 0.25) & (v > 0.45) & ~np.any([C[k] for k in ('eye', 'ribbon', 'brass', 'cloth', 'hair', 'skin')], axis=0)
    taken = np.any([m for m in C.values()], axis=0)
    C['leather'] = cov & ~taken
    return C


# ---------------------------------------------------------------- native region colours per tier
def pal(i):
    return np.frombuffer(open(PALDIR / f'pal{i:03d}.act', 'rb').read()[:768], np.uint8).reshape(256, 3).astype(np.float64) / 255


BASEP = (pal(141) * 255).astype(int)                     # the native frames are drawn in palette 141
LUT = {tuple(c): i for i, c in enumerate(BASEP)}
IDX = []
for f in sorted(p for p in NATIVE.glob('m442*.png') if p.name[4] in 'sw'):
    a = np.asarray(Image.open(f).convert('RGBA')); m = a[..., 3] > 0
    IDX.append(np.array([LUT.get(tuple(c), -1) for c in a[m][:, :3].astype(int)]))
IDX = np.concatenate(IDX)
native = {}
for reg, ids in REGION_IDX.items():
    sel = IDX[np.isin(IDX, ids)]
    for k, p in VARIANTS.items():
        X = pal(p)[sel]; L = R.luminance(X)
        o = np.argsort(L); native[(reg, k)] = X[o]
    print('NATIVE', reg, 'pixels', len(sel), {k: np.round(np.median(native[(reg, k)], 0) * 255).astype(int).tolist() for k in VARIANTS})


def ramps_for(reg, texel_lum):
    lo, hi = np.percentile(texel_lum, [2, 98]); srt = np.sort(texel_lum)
    out = {}
    for k in VARIANTS:
        X = native[(reg, k)]; cols = []
        for i in range(16):
            Li = lo + (hi - lo) * i / 15
            q = np.searchsorted(srt, Li) / len(srt); q = QWIN[reg][0] + (QWIN[reg][1] - QWIN[reg][0]) * q
            c = X[min(len(X) - 1, int(q * (len(X) - 1)))]
            cols.append([round(float(v), 6) for v in np.clip(lin(np.clip(c * RAMP_GAIN[reg], 0, 1)), 0, 1)])
        out[k] = {'range': [round(float(lo), 5), round(float(max(hi, lo + 1e-3)), 5)], 'colors': cols}
    return out


# head geometry for the beard/scalp split (rest pose, from the head layout raster)
_H = np.load(HERE / 'work' / 'uvraster_HeadUV.npz')
EYE_Z = float(np.median(_H['pos'][np.isin(_H['piece'], [4, 5])][:, 2]))
HEAD_Y = float(np.median(_H['pos'][_H['piece'] == 0][:, 1]))
print('HEAD eye z', round(EYE_Z, 3), 'head centre y', round(HEAD_Y, 3))


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
    if C['hair'].sum() > 100:                              # one hair albedo x Meshy's fine shading
        g = repaint_skin(g, C['hair'], np.median(base[C['hair']], 0))
    g = ao_grade(g, load(HERE / 'work' / ao_png, 'L'), cov)
    print('CLASSES', tag, {k: int(m.sum()) for k, m in C.items()}, 'covered', int(cov.sum()),
          'skin albedo', np.round(albedo * 255).tolist())
    cls = np.zeros((N, N), np.uint8); spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8)
    for k, m in C.items():
        if m.any():
            cls[m] = CLASS[k]; spec[m] = SPEC[k]; rgh[m] = np.clip(ROUGH[k] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
    return g, normal, spec, rgh, cls, C, cov, albedo


lums = {r: [] for r in REGIONS}
g, normal, spec, rgh, cls, C, cov, ALB = build(HERE / 'meshy' / 'body_texture_v1', 'uvraster_UVMap.npz', 'ao_UVMap.png', False, 'body')
lum = R.luminance(g)
for r in REGIONS:
    if C[r].sum() > 50:
        lums[r].append(lum[C[r]])
save(pad(g, cov), T / 'm442_basecolor_1k.png'); save(pad(normal, cov), T / 'm442_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'm442_metal_rough_1k.png')
mask = lambda m, cv: ndimage.gaussian_filter(pad(m.astype(float), cv), 0.7)
R.write_mask([mask(C[r], cov) for r in REGIONS], T / 'm442_region_mask.png', size=N)
Image.fromarray(cls).save(T / 'm442_material_classes.png')
hg, hn, hspec, hrgh, hcls, HC, hcov, _ = build(HERE / 'meshy' / 'head_texture_v1', 'uvraster_HeadUV.npz', 'ao_HeadUV.png', True, 'head', ALB)
hl = R.luminance(hg)
for r in REGIONS:
    if HC[r].sum() > 50:
        lums[r].append(hl[HC[r]])
save(pad(hg, hcov), T / 'm442_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'm442_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm442_head_metal_rough_1k.png')
R.write_mask([mask(HC[r], hcov) for r in REGIONS], T / 'm442_head_region_mask.png', size=N)
Image.fromarray(hcls).save(T / 'm442_head_material_classes.png')
RR = {r: ramps_for(r, np.concatenate(lums[r])) for r in REGIONS}
ramps = {k: [RR[r][k] for r in REGIONS] for k in VARIANTS}
mats = [{'base': 'M442_A', 'prefix': 'M442', 'mask': 'm442_region_mask.png', 'regions': REGIONS, 'palettes': VARIANTS, 'ramps': ramps},
        {'base': 'M442Head_A', 'prefix': 'M442Head', 'mask': 'm442_head_region_mask.png', 'regions': REGIONS,
         'palettes': VARIANTS, 'ramps': ramps}]
(T / 'm442_ramps.json').write_text(json.dumps({'variants': list(VARIANTS), 'materials': mats}, indent=1) + '\n')
for k in VARIANTS:
    print('RAMP', k, {r: [round(x * 255) for x in RR[r][k]['colors'][8]] for r in REGIONS})
# ---------------------------------------------------------------- sickle surface maps (its own material, no tier region)
sb = np.asarray(Image.open(T / 'props' / 'sickle_basecolor.png').convert('RGB'), np.float64) / 255
sh_, ss_, sv_ = hsv(sb)
s_brass = (sh_ > 30) & (sh_ < 65) & (ss_ > 0.35) & (sv_ > 0.35)
s_wood = ~s_brass & (ss_ > 0.25) & (sh_ < 45)
sspec = np.where(s_brass, 1.0, np.where(s_wood, 0.3, 0.85)); srgh = np.where(s_brass, 0.3, np.where(s_wood, 0.7, 0.3))
save(np.stack([sspec, srgh, np.zeros_like(srgh)], -1), T / 'm442_sickle_metal_rough.png')
save(np.dstack([np.full(sb.shape[:2], 0.5), np.full(sb.shape[:2], 0.5), np.ones(sb.shape[:2])]), T / 'm442_sickle_normal.png')
Image.fromarray((sb * 255 + 0.5).astype(np.uint8)).save(T / 'm442_sickle_basecolor.png')
print('SICKLE maps: brass texels', int(s_brass.sum()), 'wood', int(s_wood.sum()))
