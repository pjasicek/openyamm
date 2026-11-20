#!/usr/bin/env python3
"""Textures, region masks and tier ramps for hvm, the Hesper Landfall villager (male) (CLAUDE_CREATURE_TEXTURES.md).
Run after uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py.

Three outfits (skins vm_a/vm_b/vm_c) recolour FOUR regions: R = the coat's slate-blue cloth, G = its off-white front
panel, yokes and cuffs, B = the red stand-up collar, A = the hair. There is no native palette: A is fitted to the
texture itself (fit_ramps against the base colour, so A reproduces the approved concept), B and C keep A's shading
(each stop's luminance relative to the region's median, compressed by SHADE) on an authored colour (OUTFITS).
- Classes per texel by piece, garment and colour (uv_raster.py): eyes (P09/P10), brass (garment 7: pin and clasps,
  plus the coat's gold piping by hue), hair (garment 3 plus the dark scalp above the brows), the coat's cloth by hue
  (blue coat, off-white panel, red collar, brown belt), the lit wrist strip and the ceramic belt plate / wrist band
  (off-white texels at the belt front and round the lit strip: kept out of the panel region), linen (trousers P02),
  leather (belt, pouch P05, shoes P06/P07), skin (head P01, hands P03/P04).
- Skin repainted (natm): one albedo x Meshy's fine shading. AO graded into the base colour; ORM red = per-class
  specular mask (openyamm_specular_mask), green = roughness. Masks padded into the gutters.
Writes textures/hvm_*. PREVIEW=1 also writes work/classes_body.png / classes_head.png."""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
N = 1024
SKIN_MIX = 0.85
REGIONS = ['coat', 'panel', 'collar', 'hair']
VARIANTS = ['vm_a', 'vm_b', 'vm_c']
OUTFITS = {   # sRGB median albedo per region for B and C (A comes from the texture)
    'vm_b': {'coat': (62, 80, 72), 'panel': (226, 210, 172), 'collar': (168, 124, 48), 'hair': (30, 26, 24)},
    'vm_c': {'coat': (98, 90, 84), 'panel': (190, 202, 212), 'collar': (40, 112, 116), 'hair': (104, 46, 26)},
}
SHADE = 0.7   # B/C keep A's shading as (stop luminance / region median) ** SHADE: the full ratio blew the bright stops out
CLASS = {'skin': 1, 'hair': 2, 'coat': 8, 'panel': 8, 'collar': 8, 'linen': 8, 'leather': 8, 'brass': 9, 'eye': 6,
         'ceramic': 11, 'light': 11}
SPEC = {'skin': 0.45, 'hair': 0.3, 'coat': 0.2, 'panel': 0.2, 'collar': 0.2, 'linen': 0.2, 'leather': 0.35,
        'brass': 1.0, 'eye': 0.9, 'ceramic': 0.7, 'light': 0.6}
ROUGH = {'skin': 0.5, 'hair': 0.6, 'coat': 0.85, 'panel': 0.85, 'collar': 0.85, 'linen': 0.85, 'leather': 0.6,
         'brass': 0.3, 'eye': 0.2, 'ceramic': 0.35, 'light': 0.3}
PREVIEW_COL = {'skin': (230, 170, 140), 'hair': (150, 90, 20), 'coat': (40, 70, 230), 'panel': (240, 240, 230),
               'collar': (230, 20, 20), 'linen': (110, 140, 110), 'leather': (90, 50, 20), 'brass': (250, 210, 0),
               'eye': (255, 0, 255), 'ceramic': (0, 255, 255), 'light': (120, 255, 120)}


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


_H = np.load(HERE / 'work' / 'uvraster_HeadUV.npz')
EYE_Z = float(np.median(_H['pos'][np.isin(_H['piece'], [9, 10])][:, 2]))
print('HEAD eye z', round(EYE_Z, 3))


def classify(base, gar, pos, cov, piece):
    h, s, v = hsv(base)
    C = {}
    C['eye'] = cov & np.isin(piece, [9, 10])
    C['hair'] = cov & (gar == 3)
    C['brass'] = cov & (gar == 7)
    coat = cov & (piece == 0)
    gold = coat & (h > 32) & (h < 62) & (s > 0.35) & (v > 0.42)
    brown = coat & (h > 10) & (h < 45) & (s > 0.3) & (v <= 0.42)
    red = coat & ((h < 16) | (h > 330)) & (s > 0.35) & ~brown
    light = coat & (v > 0.85) & (h > 170) & (h < 230) & (s > 0.12) & (s < 0.6)
    white = coat & (s < 0.2) & (v > 0.55) & ~light
    blue = coat & (h > 185) & (h < 255) & (s > 0.15) & ~light
    C['brass'] |= gold; C['leather'] = brown | (cov & np.isin(piece, [5, 6, 7])); C['collar'] = red
    C['light'] = light; C['coat'] = blue
    # ceramic: off-white at the belt front (the belt plate) and round the lit wrist strip (the band)
    bz = np.median(pos[brown][:, 2]) if brown.sum() > 50 else 0.95
    plate = white & (np.abs(pos[..., 2] - bz) < 0.035) & (np.abs(pos[..., 0]) < 0.07) & (pos[..., 1] < 0)
    band = np.zeros_like(white)
    if light.any():
        lc = np.median(pos[light], 0)
        band = white & (np.linalg.norm(pos - lc, axis=-1) < 0.04)
    C['ceramic'] = plate | band
    C['panel'] = white & ~C['ceramic']
    # unlabelled coat texels (seams, shading extremes) take the nearest labelled cloth class
    cloth = {'coat': C['coat'], 'panel': C['panel'], 'collar': C['collar']}
    known = np.any([C[k] for k in ('coat', 'panel', 'collar', 'brass', 'leather', 'light', 'ceramic')], axis=0)
    rest = coat & ~known
    lab = np.zeros(base.shape[:2], np.int32)
    for i, k in enumerate(cloth, 1):
        lab[cloth[k]] = i
    _, (iy, ix) = ndimage.distance_transform_edt(lab == 0, return_indices=True)
    near = lab[iy, ix]
    for i, k in enumerate(cloth, 1):
        C[k] |= rest & (near == i)
    C['linen'] = cov & (piece == 2)
    hd = cov & (piece == 1)
    C['hair'] |= hd & (v < 0.3) & (s < 0.65) & (pos[..., 2] > EYE_Z + 0.035)    # scalp under the hair cards
    taken = np.any([m for m in C.values()], axis=0)
    C['skin'] = cov & np.isin(piece, [1, 3, 4]) & ~taken
    rest = cov & ~np.any([m for m in C.values()], axis=0)
    C['brass'] |= rest
    return C


def build(meshy_dir, raster, ao_png, tag, albedo=None):
    base = load(meshy_dir / 'texture_urls_0_base_color.png'); normal = load(meshy_dir / 'texture_urls_0_normal.png')
    rough_m = load(meshy_dir / 'texture_urls_0_roughness.png', 'L')
    Rz = np.load(HERE / 'work' / raster); gar, pos, piece = Rz['garment'], Rz['pos'], Rz['piece']; cov = gar >= 0
    C = classify(base, gar, pos, cov, piece)
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


mask = lambda m, cv: ndimage.gaussian_filter(pad(m.astype(float), cv), 0.7)


def ramps(g, C, cov):
    """{region: {variant: ramp}} for one material; None where the material has too few texels of the region."""
    out = {}
    for r in REGIONS:
        w = np.clip(np.concatenate([mask(m, c) for m, c in zip(np.split(C[r], C[r].shape[0] // N), np.split(cov, cov.shape[0] // N))]), 0, 1)
        try:
            fit, rep = R.fit_ramps(g, {'vm_a': g}, w)
        except ValueError:
            out[r] = None; continue
        a = fit['vm_a']; cols = np.array(a['colors'])
        L = cols @ np.array([0.2126, 0.7152, 0.0722])
        med = np.median(R.luminance(g)[w >= 0.9])                     # sRGB-domain luminance of the region's texels
        lmed = float(np.interp(med, np.linspace(a['range'][0], a['range'][1], 16), L))
        out[r] = {'vm_a': a}
        for k, tgt in OUTFITS.items():
            t = lin(np.array(tgt[r], np.float64) / 255)
            lt = float(t @ np.array([0.2126, 0.7152, 0.0722]))
            new = np.clip(t[None, :] * ((L / max(lmed, 1e-4)) ** SHADE)[:, None], 0, 1)
            out[r][k] = {'range': a['range'], 'colors': np.round(new, 6).tolist()}
        print('RAMPFIT', r, rep['vm_a'], 'A median', np.round(srgb(cols[8]) * 255).astype(int).tolist())
    return out


g, normal, spec, rgh, cls, C, cov, ALB = build(HERE / 'meshy' / 'body_texture_v1', 'uvraster_UVMap.npz', 'ao_UVMap.png', 'body')
save(pad(g, cov), T / 'hvm_basecolor_1k.png'); save(pad(normal, cov), T / 'hvm_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'hvm_metal_rough_1k.png')
R.write_mask([mask(C[r], cov) for r in REGIONS], T / 'hvm_region_mask.png', size=N)
Image.fromarray(cls).save(T / 'hvm_material_classes.png')
hg, hn, hspec, hrgh, hcls, HC, hcov, _ = build(HERE / 'meshy' / 'head_texture_v1', 'uvraster_HeadUV.npz', 'ao_HeadUV.png', 'head', ALB)
save(pad(hg, hcov), T / 'hvm_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'hvm_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'hvm_head_metal_rough_1k.png')
R.write_mask([mask(HC[r], hcov) for r in REGIONS], T / 'hvm_head_region_mask.png', size=N)
Image.fromarray(hcls).save(T / 'hvm_head_material_classes.png')
# one set of ramps for both materials (merge_head_material.py merges the head into the body material): fitted over the
# body and head texels together
RB = ramps(np.concatenate([g, hg]), {r: np.concatenate([C[r], HC[r]]) for r in REGIONS}, np.concatenate([cov, hcov]))
RH = RB
mats = [{'base': 'HVM_A', 'prefix': 'HVM', 'mask': 'hvm_region_mask.png', 'regions': REGIONS,
         'ramps': {k: [RB[r][k] for r in REGIONS] for k in VARIANTS}},
        {'base': 'HVMHead_A', 'prefix': 'HVMHead', 'mask': 'hvm_head_region_mask.png', 'regions': REGIONS,
         'ramps': {k: [RH[r][k] for r in REGIONS] for k in VARIANTS}}]
(T / 'hvm_ramps.json').write_text(json.dumps({'variants': VARIANTS, 'materials': mats, 'outfits': OUTFITS}, indent=1) + '\n')
for k in VARIANTS:
    print('RAMP', k, {r: [round(float(x) * 255) for x in srgb(np.array(RB[r][k]['colors'][8]))] for r in REGIONS})
