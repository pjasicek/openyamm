#!/usr/bin/env python3
"""Textures, region masks and tier ramps for m362, the MM7 male human peasant 2 (CLAUDE_CREATURE_TEXTURES.md). Run
after uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py.

Nine variants (outfits A/B/C x tiers A/B/C = descriptors 367..375 'Peasant Human2 Male<o> <t>', dsft palettes
363..371, mm7_m362/variants.json) recolour THREE regions, as the native masks do: R = the violet doublet and shoulder
rolls (variants.json purple_vest indices plus the other purple entries that change), G = the hair (96..117: blond,
brown, black, white, ginger ...), B = the jaw stubble (76..93: skin tones in tier A, grey/black/white/ginger beards in
the others; a soft jaw mask at 0.7 like the native's). Skin, shirt, white bands, belt, breeches, boots and the rapier
stay.
- Classes per texel by piece and colour (uv_raster.py): vest = doublet/skirt/shoulder-roll pieces in a blue-violet hue;
  linen = shirt sleeves, cuffs, collar, white bands, the shirt in the chest opening and the breeches; leather = belt,
  boots, boot cuffs, scabbard; brass = studs, laces, hilt; hair = garment 3; eyes; skin = rest.
- Skin and hair repainted (natm): one albedo x Meshy's fine shading (Meshy painted a pale streak in the hair). AO graded; ORM red = per-class specular mask, green =
  roughness.
- Ramps per tier from the tier's native pixels of the region's palette indices (stand and walk, all views), sorted by
  luminance, rank-matched to the region's texel luminance inside a native quantile window (QWIN); masks padded.
PREVIEW=1 also writes work/classes_body.png / classes_head.png. Writes textures/m362_*."""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
NATIVE = HERE.parent / 'mm7_m362' / 'native'
PALDIR = HERE.parents[2] / 'assets_dev' / 'worlds' / 'mm7' / 'textures'
N = 1024
SKIN_MIX = 0.85
RAMP_GAIN = {'vest': 1.3, 'hair': 1.2, 'beard': 1.1}
# texel luminance (2nd-98th pct) -> native quantile window: the sprite's baked deep shadows (tunic) stretched across
# Meshy's narrow cloth range turned its mottling into dark patches
QWIN = {'vest': (0.35, 0.97), 'hair': (0.15, 0.99), 'beard': (0.2, 0.95)}
VARIANTS = {f'm362_{o}{t}': 363 + 3 * i + j for i, o in enumerate('abc') for j, t in enumerate('abc')}
REGIONS = ['vest', 'hair', 'beard']
_VJ = json.load(open(HERE.parent / 'mm7_m362' / 'variants.json'))
_P = {i: np.frombuffer(open(PALDIR / f'pal{i:03d}.act', 'rb').read()[:768], np.uint8).reshape(256, 3).astype(int) for i in range(363, 372)}
_purple = [k for k in range(150, 241) if _P[363][k][2] > _P[363][k][0] + 10 and _P[363][k][2] > _P[363][k][1] + 10
           and max(np.abs(_P[p][k] - _P[363][k]).sum() for p in _P) > 20]
REGION_IDX = {'vest': sorted(set(_VJ['regions'][0]['palette_indices']) | set(_purple)),
              'hair': list(range(96, 118)),
              'beard': list(range(76, 94))}
CLASS = {'skin': 1, 'hair': 2, 'beard': 1, 'vest': 8, 'linen': 8, 'leather': 8, 'brass': 9, 'eye': 6}
SPEC = {'skin': 0.45, 'hair': 0.3, 'beard': 0.45, 'vest': 0.2, 'linen': 0.2, 'leather': 0.35, 'brass': 1.0, 'eye': 0.9}
ROUGH = {'skin': 0.5, 'hair': 0.6, 'beard': 0.5, 'vest': 0.85, 'linen': 0.85, 'leather': 0.6, 'brass': 0.3, 'eye': 0.2}
PREVIEW_COL = {'skin': (230, 170, 140), 'hair': (150, 90, 20), 'beard': (255, 60, 0), 'vest': (120, 40, 220),
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
    C['eye'] = cov & np.isin(piece, [16, 18])
    C['hair'] = cov & (gar == 3)
    C['brass'] = cov & ((gar == 7) | (np.isin(piece, [13, 24, 25, 31, 32]) & (v > 0.35)))
    violet = (h > 205) & (h < 300) & (s > 0.2)
    C['vest'] = cov & np.isin(piece, [4, 8, 9, 12]) & violet
    white = (s < 0.22) & (v > 0.45)
    C['linen'] = cov & (np.isin(piece, [3, 10, 11, 14, 27, 30]) | (np.isin(piece, [0, 4, 8, 9, 12]) & white)) & ~C['vest']
    C['leather'] = cov & np.isin(piece, [5, 6, 13, 15, 17, 21, 22, 24, 25, 31, 32]) & ~C['brass']
    taken = np.any([m for m in C.values()], axis=0)
    C['skin'] = cov & np.isin(piece, [0, 1, 2, 29, 45]) & ~taken
    # jaw stubble: the skin of the head below the eyes on the face side, above the chin line (soft mask later)
    z_, y_ = pos[..., 2], pos[..., 1]
    jaw = (z_ < EYE_Z - 0.03) & (z_ > EYE_Z - 0.115) & (y_ < HEAD_Y + 0.01) & ~((z_ < EYE_Z - 0.085) & (y_ > HEAD_Y - 0.035))
    C['beard'] = C['skin'] & (piece == 0) & jaw
    C['skin'] &= ~C['beard']
    rest = cov & ~np.any([m for m in C.values()], axis=0)
    C['vest'] |= rest & np.isin(piece, [4, 8, 9, 12]) & (s > 0.15) & ~white
    rest = cov & ~np.any([m for m in C.values()], axis=0)
    C['leather'] |= rest
    return C


# ---------------------------------------------------------------- native region colours per tier
def pal(i):
    return np.frombuffer(open(PALDIR / f'pal{i:03d}.act', 'rb').read()[:768], np.uint8).reshape(256, 3).astype(np.float64) / 255


BASEP = (pal(363) * 255).astype(int)
LUT = {tuple(c): i for i, c in enumerate(BASEP)}
IDX = []
for f in sorted(p for p in NATIVE.glob('m362*.png') if p.name[4] in 'sw'):
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


# head geometry for the beard/scalp split (rest pose, from the head layout raster)
_H = np.load(HERE / 'work' / 'uvraster_HeadUV.npz')
EYE_Z = float(np.median(_H['pos'][np.isin(_H['piece'], [16, 18])][:, 2]))
_hp = (_H['piece'] == 0) & (_H['pos'][..., 2] > EYE_Z - 0.15)
HEAD_Y = float(np.median(_H['pos'][_hp][:, 1]))
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
        albedo = np.median(base[C['skin'] | C['beard']], 0) if (C['skin'] | C['beard']).sum() > 100 else np.array([0.85, 0.65, 0.55])
    g = repaint_skin(base, C['skin'] | C['beard'], albedo)
    if C['hair'].sum() > 100:                              # one hair albedo x Meshy's fine shading (pale streak)
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
save(pad(g, cov), T / 'm362_basecolor_1k.png'); save(pad(normal, cov), T / 'm362_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'm362_metal_rough_1k.png')
mask = lambda m, cv: ndimage.gaussian_filter(pad(m.astype(float), cv), 0.7)
R.write_mask([mask(C[r], cov) if r != 'beard' else np.zeros((N, N)) for r in REGIONS], T / 'm362_region_mask.png', size=N)
# the stubble is a soft 0.7 jaw mask on the head set only (native jaw_stubble: mask_sigma 5, weight 0.7)
hmask_r = lambda HC, r, cv: (np.clip(ndimage.gaussian_filter(HC['beard'].astype(float), 4.0) * 1.6, 0, 1) * 0.7 * (HC['beard'] | HC['skin'])) if r == 'beard' else mask(HC[r], cv)
Image.fromarray(cls).save(T / 'm362_material_classes.png')
hg, hn, hspec, hrgh, hcls, HC, hcov, _ = build(HERE / 'meshy' / 'head_texture_v1', 'uvraster_HeadUV.npz', 'ao_HeadUV.png', True, 'head', ALB)
hl = R.luminance(hg)
for r in REGIONS:
    if HC[r].sum() > 50:
        lums[r].append(hl[HC[r]])
save(pad(hg, hcov), T / 'm362_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'm362_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm362_head_metal_rough_1k.png')
R.write_mask([hmask_r(HC, r, hcov) for r in REGIONS], T / 'm362_head_region_mask.png', size=N)
Image.fromarray(hcls).save(T / 'm362_head_material_classes.png')
RR = {r: ramps_for(r, np.concatenate(lums[r])) for r in REGIONS}
ramps = {k: [RR[r][k] for r in REGIONS] for k in VARIANTS}
mats = [{'base': 'M362_A', 'prefix': 'M362', 'mask': 'm362_region_mask.png', 'regions': REGIONS, 'palettes': VARIANTS, 'ramps': ramps},
        {'base': 'M362Head_A', 'prefix': 'M362Head', 'mask': 'm362_head_region_mask.png', 'regions': REGIONS,
         'palettes': VARIANTS, 'ramps': ramps}]
(T / 'm362_ramps.json').write_text(json.dumps({'variants': list(VARIANTS), 'materials': mats}, indent=1) + '\n')
for k in VARIANTS:
    print('RAMP', k, {r: [round(x * 255) for x in RR[r][k]['colors'][8]] for r in REGIONS})
