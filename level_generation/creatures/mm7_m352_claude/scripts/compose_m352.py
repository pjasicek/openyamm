#!/usr/bin/env python3
"""Textures, region masks and tier ramps for m352, the MM7 male human peasant 1 (CLAUDE_CREATURE_TEXTURES.md). Run
after uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py.

Nine variants (outfits A/B/C x tiers A/B/C = descriptors 358..366 'Peasant Human1 Male<o> <t>', dsft palettes
353..361, mm7_m352/variants.json) recolour THREE regions, as the native masks do: R = the tunic (palette indices of
variants.json channel 0 plus its dark shades 197..210), G = the hair (72..74, 91, 95, 97, 99: black, black, red,
blonde, ..., white), B = the beard (231..248). Skin, eyes, belt, studs, trousers and shoes stay.
- Classes per texel by piece and colour (uv_raster.py): tunic = piece 0 green; leather = piece 0 non-green (belt),
  shoes, strap end; linen = trouser legs; brass = studs and buckle; hair = the hair shell plus dark scalp texels of
  the head above the brows; beard = dark texels of the head below the eyes on the face side; skin = the rest of the
  head, hands and forearms; eyes.
- Skin repainted (natm): one albedo x Meshy's fine shading. AO graded into the base colour; ORM red = per-class
  specular mask (openyamm_specular_mask), green = roughness.
- Ramps per tier from that tier's native pixels of the region's palette indices (stand and walk, all views), sorted
  by luminance and rank-matched to the region's texel luminance (2nd-98th percentile), gain RAMP_GAIN; masks padded
  into the gutters. PREVIEW=1 also writes work/classes_body.png / classes_head.png.
Writes textures/m352_*."""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
NATIVE = HERE.parent / 'mm7_m352' / 'native'
PALDIR = HERE.parents[2] / 'assets_dev' / 'worlds' / 'mm7' / 'textures'
N = 1024
SKIN_MIX = 0.85
RAMP_GAIN = {'tunic': 1.3, 'hair': 1.25, 'beard': 1.25}
# texel luminance (2nd-98th pct) -> native quantile window: the sprite's baked deep shadows (tunic) stretched across
# Meshy's narrow cloth range turned its mottling into dark patches
QWIN = {'tunic': (0.35, 0.97), 'hair': (0.1, 0.99), 'beard': (0.1, 0.99)}
VARIANTS = {f'm352_{o}{t}': 353 + 3 * i + j for i, o in enumerate('abc') for j, t in enumerate('abc')}
REGIONS = ['tunic', 'hair', 'beard']
_V = json.load(open(HERE.parent / 'mm7_m352' / 'variants.json'))['variants'][0]['regions']
REGION_IDX = {'tunic': sorted(set(_V[0]['native_indices']) | set(range(197, 211))),
              'hair': [72, 73, 74, 91, 95, 97, 99],
              'beard': [231, 235, 237, 241, 242, 243, 244, 245, 246, 248]}
CLASS = {'skin': 1, 'hair': 2, 'beard': 2, 'tunic': 8, 'linen': 8, 'leather': 8, 'brass': 9, 'eye': 6}
SPEC = {'skin': 0.45, 'hair': 0.3, 'beard': 0.25, 'tunic': 0.2, 'linen': 0.2, 'leather': 0.35, 'brass': 1.0, 'eye': 0.9}
ROUGH = {'skin': 0.5, 'hair': 0.6, 'beard': 0.7, 'tunic': 0.88, 'linen': 0.85, 'leather': 0.6, 'brass': 0.3, 'eye': 0.2}
PREVIEW_COL = {'skin': (230, 170, 140), 'hair': (150, 90, 20), 'beard': (255, 60, 0), 'tunic': (20, 200, 40),
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
    C['eye'] = cov & np.isin(piece, [10, 11])
    C['brass'] = cov & (gar == 7)
    green = (h > 70) & (h < 175) & (s > 0.18)
    C['tunic'] = cov & (piece == 0) & green
    C['leather'] = cov & ((np.isin(piece, [6, 7, 9])) | ((piece == 0) & ~green & (s > 0.25) & (h < 50)))
    C['linen'] = cov & (piece == 1)
    C['hair'] = cov & (piece == 5)
    hd = cov & (piece == 2)
    dark = hd & (v < 0.33) & (s < 0.6)
    face = pos[..., 1] < HEAD_Y - 0.01                                    # the character faces -Y
    C['hair'] |= dark & (pos[..., 2] > EYE_Z + 0.035)                     # scalp under the hair shell
    C['beard'] = dark & face & (pos[..., 2] < EYE_Z - 0.025)
    taken = np.any([m for m in C.values()], axis=0)
    C['skin'] = cov & np.isin(piece, [2, 3, 4]) & ~taken
    C['tunic'] |= cov & (piece == 0) & ~np.any([C[k] for k in ('leather', 'brass')], axis=0) & ~C['tunic'] & (s > 0.1) & (h > 60) & (h < 190)
    rest = cov & ~np.any([m for m in C.values()], axis=0)
    C['leather'] |= rest & (piece == 0)
    C['skin'] |= rest & (piece != 0)
    return C


# ---------------------------------------------------------------- native region colours per tier
def pal(i):
    return np.frombuffer(open(PALDIR / f'pal{i:03d}.act', 'rb').read()[:768], np.uint8).reshape(256, 3).astype(np.float64) / 255


BASEP = (pal(353) * 255).astype(int)
LUT = {tuple(c): i for i, c in enumerate(BASEP)}
IDX = []
for f in sorted(p for p in NATIVE.glob('m352*.png') if p.name[4] in 'sw'):
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
EYE_Z = float(np.median(_H['pos'][np.isin(_H['piece'], [10, 11])][:, 2]))
HEAD_Y = float(np.median(_H['pos'][_H['piece'] == 2][:, 1]))
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
save(pad(g, cov), T / 'm352_basecolor_1k.png'); save(pad(normal, cov), T / 'm352_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'm352_metal_rough_1k.png')
mask = lambda m, cv: ndimage.gaussian_filter(pad(m.astype(float), cv), 0.7)
R.write_mask([mask(C[r], cov) for r in REGIONS], T / 'm352_region_mask.png', size=N)
Image.fromarray(cls).save(T / 'm352_material_classes.png')
hg, hn, hspec, hrgh, hcls, HC, hcov, _ = build(HERE / 'meshy' / 'head_texture_v1', 'uvraster_HeadUV.npz', 'ao_HeadUV.png', True, 'head', ALB)
hl = R.luminance(hg)
for r in REGIONS:
    if HC[r].sum() > 50:
        lums[r].append(hl[HC[r]])
save(pad(hg, hcov), T / 'm352_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'm352_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm352_head_metal_rough_1k.png')
R.write_mask([mask(HC[r], hcov) for r in REGIONS], T / 'm352_head_region_mask.png', size=N)
Image.fromarray(hcls).save(T / 'm352_head_material_classes.png')
RR = {r: ramps_for(r, np.concatenate(lums[r])) for r in REGIONS}
ramps = {k: [RR[r][k] for r in REGIONS] for k in VARIANTS}
mats = [{'base': 'M352_A', 'prefix': 'M352', 'mask': 'm352_region_mask.png', 'regions': REGIONS, 'palettes': VARIANTS, 'ramps': ramps},
        {'base': 'M352Head_A', 'prefix': 'M352Head', 'mask': 'm352_head_region_mask.png', 'regions': REGIONS,
         'palettes': VARIANTS, 'ramps': ramps}]
(T / 'm352_ramps.json').write_text(json.dumps({'variants': list(VARIANTS), 'materials': mats}, indent=1) + '\n')
for k in VARIANTS:
    print('RAMP', k, {r: [round(x * 255) for x in RR[r][k]['colors'][8]] for r in REGIONS})
