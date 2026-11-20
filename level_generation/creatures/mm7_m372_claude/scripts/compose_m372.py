#!/usr/bin/env python3
"""Textures, region masks and tier ramps for m372, the MM7 female human peasant 2 (CLAUDE_CREATURE_TEXTURES.md).
Run after uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py.

Six skins for nine descriptors: 376..378 'Peasant Human2 FemaleA A/B/C' = palettes 373..375 (m372_aa/ab/ac);
379..381 FemaleB and 382..384 FemaleC both use palettes 376..378 (dsft; m372_ba/bb/bc). THREE regions as the native
masks (mm7_m372/manifest.json regions): R = the gown (emerald gown indices + its shades 86..117, 163..181, 198..208),
G = the veil and the sleeve lining (sage indices 52..85 + 37..51 and the pale gown highlights), B = the hair
(13..27). Skin, eyes, the gold cord and circlet, the dark beads and the shoes stay.
- Classes per texel by garment/piece and colour: gown = piece 0 saturated green; veil = the veil shell and the pale
  sage lining of the sleeves (piece 0, low saturation, light); hair = the fringe (piece 9) and the crown of the head
  piece above the brows (Meshy painted it as a translucent green cap: repainted with the native tier-A hair colour);
  brass = saturated yellow (cord, circlet, clasp); leather = shoes, beads and the rest of the ornaments; eyes; skin.
- Skin repainted (natm): one albedo x Meshy's fine shading, the face's fine shading clamped (a dark cheek blotch).
- Ramps per tier from the tier's native pixels of the region's palette indices (stand and walk, all views), sorted by
  luminance, rank-matched to the region's texel luminance inside a native quantile window (QWIN); masks padded into
  the gutters. PREVIEW=1 also writes work/classes_body.png / classes_head.png.
Writes textures/m372_*."""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
NATIVE = HERE.parent / 'mm7_m372' / 'native'
PALDIR = HERE.parents[2] / 'assets_dev' / 'worlds' / 'mm7' / 'textures'
N = 1024
SKIN_MIX = 0.85
DETAIL_LO, DETAIL_HI = 0.75, 1.2     # m372: Meshy's dark cheek blotch and light streak under the eye survived 0.5..1.5
RAMP_GAIN = {'gown': 1.3, 'veil': 1.2, 'hair': 1.25}
# texel luminance (2nd-98th pct) -> native quantile window: the sprite's baked deep shadows (tunic) stretched across
# Meshy's narrow cloth range turned its mottling into dark patches
QWIN = {'gown': (0.35, 0.97), 'veil': (0.45, 0.97), 'hair': (0.1, 0.99)}
VARIANTS = {f'm372_{o}{t}': 373 + 3 * i + j for i, o in enumerate('ab') for j, t in enumerate('abc')}   # C = B palettes
REGIONS = ['gown', 'veil', 'hair']
_M = {r['name']: r['palette_indices'] for r in json.load(open(HERE.parent / 'mm7_m372' / 'manifest.json'))['regions']}
REGION_IDX = {'gown': sorted(set(_M['emerald_gown']) | set(range(86, 100)) | {101, 102, 103} | set(range(105, 113))
                             | set(range(114, 118)) | set(range(163, 182)) | {198} | set(range(200, 209))),
              'veil': sorted(set(_M['sage_veil_and_lining']) | set(range(37, 52)) | {100, 104, 113, 197, 199}),
              'hair': sorted(set(_M['brown_hair']) | set(range(23, 28)))}
CLASS = {'skin': 1, 'hair': 2, 'gown': 8, 'veil': 8, 'linen': 8, 'leather': 8, 'brass': 9, 'eye': 6}
SPEC = {'skin': 0.45, 'hair': 0.3, 'gown': 0.2, 'veil': 0.2, 'linen': 0.2, 'leather': 0.35, 'brass': 1.0, 'eye': 0.9}
ROUGH = {'skin': 0.5, 'hair': 0.6, 'gown': 0.88, 'veil': 0.85, 'linen': 0.85, 'leather': 0.6, 'brass': 0.3, 'eye': 0.2}
PREVIEW_COL = {'skin': (230, 170, 140), 'hair': (150, 90, 20), 'gown': (20, 200, 40), 'veil': (160, 230, 190),
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
    detail = np.clip((L / np.maximum(Lb, 1e-4)) ** 1.15, DETAIL_LO, DETAIL_HI)
    new = srgb(np.clip(lin(albedo)[None, :] * detail[m][:, None], 0, 1))
    out = img.copy(); out[m] = img[m] * (1 - SKIN_MIX) + new * SKIN_MIX
    return out


def ao_grade(img, ao, cov, strength=0.4, floor=0.45):
    f = np.clip(1 - strength + strength * np.maximum(ao, floor), 0, 1)
    out = img.copy(); out[cov] = img[cov] * f[cov][:, None]; return out


def classify(base, gar, pos, cov, head_layout, piece):
    h, s, v = hsv(base)
    C = {}
    C['eye'] = cov & (gar == 4)
    C['brass'] = cov & ~np.isin(piece, [0, 1, 2, 3, 4, 5, 6]) & (h > 30) & (h < 66) & (s > 0.35) & (v > 0.35)
    C['brass'] |= cov & (piece == 8)                                                    # the hanging gold cord
    C['hair'] = cov & ((piece == 9) | ((piece == 1) & (pos[..., 2] > EYE_Z + 0.04) & (pos[..., 1] < HEAD_Y + 0.02)))
    C['veil'] = cov & ((piece == 4) | ((piece == 0) & (s < 0.32) & (v > 0.42)))
    C['gown'] = cov & (piece == 0) & ~C['veil']
    C['leather'] = cov & ~np.isin(piece, [0, 1, 2, 3, 4, 9]) & ~C['brass'] & ~C['eye']
    taken = np.any([m for m in C.values()], axis=0)
    C['skin'] = cov & ~taken
    return C


# ---------------------------------------------------------------- native region colours per tier
def pal(i):
    return np.frombuffer(open(PALDIR / f'pal{i:03d}.act', 'rb').read()[:768], np.uint8).reshape(256, 3).astype(np.float64) / 255


BASEP = (pal(373) * 255).astype(int)
LUT = {tuple(c): i for i, c in enumerate(BASEP)}
IDX = []
for f in sorted(p for p in NATIVE.glob('m372*.png') if p.name[4] in 'sw'):
    a = np.asarray(Image.open(f).convert('RGBA')); m = a[..., 3] > 0
    IDX.append(np.array([LUT.get(tuple(c), -1) for c in a[m][:, :3].astype(int)]))
IDX = np.concatenate(IDX)
native = {}
for reg, ids in REGION_IDX.items():
    sel = IDX[np.isin(IDX, ids)]
    for k, p in VARIANTS.items():
        X = pal(p)[sel]; L = R.luminance(X); keep = L > 0.0
        o = np.argsort(L[keep]); native[(reg, k)] = X[keep][o]
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


_H = np.load(HERE / 'work' / 'uvraster_HeadUV.npz')
EYE_Z = float(np.median(_H['pos'][_H['garment'] == 4][:, 2]))
HEAD_Y = float(np.median(_H['pos'][_H['piece'] == 1][:, 1]))
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
    if C['hair'].sum() > 100:                              # the native tier-A auburn x Meshy's fine shading (green cap)
        g = repaint_skin(g, C['hair'], np.clip(np.median(native[('hair', 'm372_aa')], 0) * RAMP_GAIN['hair'], 0, 1))
    if C['veil'].sum() > 100:                              # m372: Meshy's knit speckle, amplified by the veil ramp
        vm = C['veil'].astype(float); bl = np.stack([ndimage.gaussian_filter(g[..., c] * vm, 2.0) for c in range(3)], -1)
        bl /= np.maximum(ndimage.gaussian_filter(vm, 2.0), 1e-4)[..., None]
        g[C['veil']] = g[C['veil']] * 0.35 + bl[C['veil']] * 0.65
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
save(pad(g, cov), T / 'm372_basecolor_1k.png'); save(pad(normal, cov), T / 'm372_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'm372_metal_rough_1k.png')
mask = lambda m, cv: ndimage.gaussian_filter(pad(m.astype(float), cv), 0.7)
R.write_mask([mask(C[r], cov) for r in REGIONS], T / 'm372_region_mask.png', size=N)
Image.fromarray(cls).save(T / 'm372_material_classes.png')
hg, hn, hspec, hrgh, hcls, HC, hcov, _ = build(HERE / 'meshy' / 'head_texture_v1', 'uvraster_HeadUV.npz', 'ao_HeadUV.png', True, 'head', ALB)
hl = R.luminance(hg)
for r in REGIONS:
    if HC[r].sum() > 50:
        lums[r].append(hl[HC[r]])
save(pad(hg, hcov), T / 'm372_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'm372_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm372_head_metal_rough_1k.png')
R.write_mask([mask(HC[r], hcov) for r in REGIONS], T / 'm372_head_region_mask.png', size=N)
Image.fromarray(hcls).save(T / 'm372_head_material_classes.png')
RR = {r: ramps_for(r, np.concatenate(lums[r])) for r in REGIONS}
ramps = {k: [RR[r][k] for r in REGIONS] for k in VARIANTS}
mats = [{'base': 'M372_A', 'prefix': 'M372', 'mask': 'm372_region_mask.png', 'regions': REGIONS, 'palettes': VARIANTS, 'ramps': ramps},
        {'base': 'M372Head_A', 'prefix': 'M372Head', 'mask': 'm372_head_region_mask.png', 'regions': REGIONS,
         'palettes': VARIANTS, 'ramps': ramps}]
(T / 'm372_ramps.json').write_text(json.dumps({'variants': list(VARIANTS), 'materials': mats}, indent=1) + '\n')
for k in VARIANTS:
    print('RAMP', k, {r: [round(x * 255) for x in RR[r][k]['colors'][8]] for r in REGIONS})
