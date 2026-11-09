#!/usr/bin/env python3
"""Textures, region mask and tier ramps for m234 (CLAUDE_CREATURE_TEXTURES.md), adapted from mm7_m234_claude. Run after
uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py. Head set from meshy/head_retexture_v1.

Tiers (mm7_m234/variants.json: 262 Stone Gargoyle 235, 263 Marble Gargoyle 236, 264 Obsidian Gargoyle 237) recolour ONE
region, as the native mask does (mm7_m234/manifest.json 'regions': wing_membranes; native indices 10..141): the
membranes green -> blue (236) -> red (237). The stone body, horns, claws, wing struts, tail and red eyes stay (the
descriptors' TintColor for B/C is not applied: the native sprites do not show it; README).
- Classes per texel: membrane = the wing garment (5) with a green hue, stone = the rest of the body (class 1),
  eyes = pieces 3/4, teeth = pieces 5, 7..22, mouth = dark red texels of the head set.
- AO graded into the base colour; ORM red = per-class specular mask, green = roughness.
- Ramps per tier from that tier's native pixels of the region's palette indices, rank-matched to the region's texel
  luminance (2nd-98th percentile), gain RAMP_GAIN; mask padded into the gutters.
Writes textures/m234_*."""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
NATIVE = HERE.parent / 'mm7_m234' / 'native'
PALDIR = HERE.parents[2] / 'assets_dev' / 'worlds' / 'mm7' / 'textures'
N = 1024
SKIN_MIX = 0.85; RAMP_GAIN = {'cloth': 1.0}
# the stone graded toward the native sprites: native stone median (62, 60, 69) x 1.4 = (87, 84, 97) over Meshy's (109, 112,
# 116); the same gain on the body and the head sets keeps the neck seam
STONE_GAIN = np.array([0.80, 0.76, 0.84])
PALS = {'m234_a': 235, 'm234_b': 236, 'm234_c': 237}
REGION_IDX = None
CLASS = {'skin': 1, 'cloth': 3, 'eye': 6, 'tooth': 5, 'mouth': 7}
SPEC = {'skin': 0.3, 'cloth': 0.3, 'eye': 0.9, 'tooth': 0.6, 'mouth': 0.5}
ROUGH = {'skin': 0.8, 'cloth': 0.7, 'eye': 0.2, 'tooth': 0.4, 'mouth': 0.5}
PREVIEW_COL = {'skin': (160, 160, 170), 'cloth': (20, 200, 40), 'eye': (255, 0, 0), 'tooth': (255, 255, 230), 'mouth': (120, 20, 30)}


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
    """m234: 'cloth' is the recolour region (the wing membranes); 'skin' the stone"""
    h, s, v = hsv(base)
    C = {}
    C['cloth'] = cov & (gar == 5) & (h > 50) & (h < 170) & (s > 0.15)
    C['eye'] = cov & np.isin(piece, [3, 4])
    C['tooth'] = cov & np.isin(piece, [5] + list(range(7, 23)))
    C['mouth'] = cov & ((h < 20) | (h > 330)) & (s > 0.35) & (v < 0.5) & ~C['eye'] & ~C['tooth'] if head_layout else np.zeros_like(cov)
    C['skin'] = cov & ~C['cloth'] & ~C['eye'] & ~C['tooth'] & ~C['mouth']
    return C


# ---------------------------------------------------------------- native region colours per tier
def pal(i):
    return np.frombuffer(open(PALDIR / f'pal{i:03d}.act', 'rb').read()[:768], np.uint8).reshape(256, 3).astype(np.float64) / 255


BASEP = (pal(235) * 255).astype(int)              # the native sprites are drawn in palette 235 (tier A, exact bypass)
LUT = {tuple(c): i for i, c in enumerate(BASEP)}
frames = sorted(p for p in NATIVE.glob('m234*.png') if p.name[4] in 'saw')
idx_pixels = []
for f in frames:
    a = np.asarray(Image.open(f).convert('RGBA'))
    m = a[..., 3] > 0
    idx_pixels.append(np.array([LUT.get(tuple(c), -1) for c in a[m][:, :3]]))
IDX = np.concatenate(idx_pixels)
import colorsys
_h = np.array([colorsys.rgb_to_hsv(*c) for c in pal(235)])
MAN = json.load(open(HERE.parent / 'mm7_m234' / 'manifest.json'))['recolor']['native_indices']
dif = np.array([i for i in MAN if _h[i, 1] > 0.15 and 0.15 < _h[i, 0] < 0.47])     # the green membrane entries
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
    g = base.copy()                                         # m234: the stone keeps Meshy's paint (no skin repaint) ...
    g[C['skin']] = np.clip(g[C['skin']] * STONE_GAIN, 0, 1)  # ... graded toward the native stone
    g = ao_grade(g, load(HERE / 'work' / ao_png, 'L'), cov)
    print('CLASSES', tag, {k: int(m.sum()) for k, m in C.items()}, 'covered', int(cov.sum()),
          'skin albedo', np.round(albedo * 255).tolist())
    cls = np.zeros((N, N), np.uint8); spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8)
    for k, m in C.items():
        if m.any():
            cls[m] = CLASS[k]; spec[m] = SPEC[k]; rgh[m] = np.clip(ROUGH[k] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
    return g, normal, spec, rgh, cls, C, cov, albedo


cfg_ramps = {}
g, normal, spec, rgh, cls, C, cov, ALB = build(HERE / 'meshy' / 'retexture_v1', 'uvraster_UVMap.npz', 'ao_UVMap.png', False, 'body')
lum = R.luminance(g)
cloth_l = [lum[C['cloth']]]
save(pad(g, cov), T / 'm234_basecolor_1k.png'); save(pad(normal, cov), T / 'm234_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'm234_metal_rough_1k.png')
mask = lambda m: ndimage.gaussian_filter(pad(m.astype(float), cov), 0.7)
R.write_mask([mask(C['cloth'])], T / 'm234_region_mask.png', size=N)
Image.fromarray(cls).save(T / 'm234_material_classes.png')
HM = HERE / 'meshy' / 'head_retexture_v1'
if HM.exists():
    hg, hn, hspec, hrgh, hcls, HC, hcov, _ = build(HM, 'uvraster_HeadUV.npz', 'ao_HeadUV.png', True, 'head', ALB)
    hl = R.luminance(hg)
    save(pad(hg, hcov), T / 'm234_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'm234_head_normal_1k.png')
    save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm234_head_metal_rough_1k.png')
    hmask = lambda m: ndimage.gaussian_filter(pad(m.astype(float), hcov), 0.7)
    R.write_mask([hmask(HC['cloth'])], T / 'm234_head_region_mask.png', size=N)
    Image.fromarray(hcls).save(T / 'm234_head_material_classes.png')
cr = ramps_for('cloth', np.concatenate(cloth_l))
ramps = {k: [cr[k]] for k in PALS}
mats = [{'base': 'M234_A', 'prefix': 'M234', 'mask': 'm234_region_mask.png', 'regions': ['cloth'], 'palettes': PALS, 'ramps': ramps}]
if HM.exists():
    mats.append({'base': 'M234Head_A', 'prefix': 'M234Head', 'mask': 'm234_head_region_mask.png', 'regions': ['cloth'],
                 'palettes': PALS, 'ramps': ramps})
(T / 'm234_ramps.json').write_text(json.dumps({'variants': list(PALS), 'materials': mats}, indent=1) + '\n')
for k in PALS:
    print('RAMP', k, 'cloth mid', [round(x, 3) for x in cr[k]['colors'][8]])
