#!/usr/bin/env python3
"""Textures, region mask and tier ramps for m238 (CLAUDE_CREATURE_TEXTURES.md), adapted from mm7_m238_claude. Run after
uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py. Head set from meshy/head_retexture_v1.

Tiers (mm7_m238/variants.json: 265 Djinni 239, 266 Genie 240, 267 Efreet 241) recolour ONE region, as the native mask
does (mm7_m238/manifest.json 'regions': cloth = the green top, collar, wrist cuffs and earrings; native indices
221..247): green -> violet (240) -> red (241). Blue skin, navy hair, gold, the gems and the mist stay.
- Classes per texel: cloth = green hue; gold = saturated yellow; mist = the vortex garment (5) and the core below the
  hips; skin = blue texels of the body piece; hair = dark navy texels of the head set (ponytail, hair); eye = the eye
  pieces 5/6 and the red forehead jewel 7/9; leather = the rest (lips, dark trim).
- Skin repainted (natm): one albedo x Meshy's fine shading. The mist is lifted toward the HD master's pale blue-white
  (MIST_LIFT). AO graded into the base colour; ORM red = per-class specular mask, green = roughness.
- Ramps per tier from that tier's native pixels of the region's palette indices, rank-matched to the region's texel
  luminance (2nd-98th percentile), gain RAMP_GAIN; mask padded into the gutters.
- The lamp keeps Meshy's maps (ORM from its colour classes: gold, blue enamel).
Writes textures/m238_*."""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
NATIVE = HERE.parent / 'mm7_m238' / 'native'
PALDIR = HERE.parents[2] / 'assets_dev' / 'worlds' / 'mm7' / 'textures'
N = 1024
SKIN_MIX = 0.85; RAMP_GAIN = {'cloth': 1.15}   # 1.3 read pale next to the native green
PALS = {'m238_a': 239, 'm238_b': 240, 'm238_c': 241}
REGION_IDX = None
CLASS = {'skin': 1, 'hair': 2, 'cloth': 8, 'leather': 8, 'gold': 9, 'steel': 9, 'eye': 6, 'mist': 11}   # 11 = vortex mist
SPEC = {'skin': 0.45, 'hair': 0.35, 'cloth': 0.45, 'leather': 0.35, 'gold': 1.0, 'steel': 0.8, 'eye': 0.9, 'mist': 0.3}
ROUGH = {'skin': 0.5, 'hair': 0.55, 'cloth': 0.5, 'leather': 0.6, 'gold': 0.3, 'steel': 0.35, 'eye': 0.2, 'mist': 0.6}
PREVIEW_COL = {'skin': (230, 170, 140), 'hair': (150, 90, 20), 'cloth': (20, 200, 40), 'leather': (90, 50, 20),
               'mist': (200, 230, 255), 'gold': (250, 210, 0), 'steel': (180, 180, 190), 'eye': (255, 0, 255)}


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
    C['eye'] = cov & np.isin(piece, [5, 6, 7, 9])
    C['mist'] = cov & ((gar == 5) | ((piece == 0) & (pos[..., 2] < HIP_Z))) & ~C['eye']
    C['cloth'] = cov & (h > 80) & (h < 170) & (s > 0.3) & (v > 0.08) & ~C['mist'] & ~C['eye']
    C['gold'] = cov & (h > 30) & (h < 65) & (s > 0.45) & (v > 0.40) & ~C['cloth'] & ~C['mist'] & ~C['eye']
    C['steel'] = np.zeros_like(cov)
    blue = cov & (h > 195) & (h < 265) & ~C['mist'] & ~C['eye'] & ~C['gold'] & ~C['cloth']
    C['hair'] = blue & (v < 0.32) & (pos[..., 2] > HAIR_Z) if head_layout else np.zeros_like(cov)
    C['skin'] = blue & ~C['hair'] & (s > 0.2)
    C['leather'] = cov & ~np.any([m for m in C.values()], axis=0)
    return C


# ---------------------------------------------------------------- native region colours per tier
def pal(i):
    return np.frombuffer(open(PALDIR / f'pal{i:03d}.act', 'rb').read()[:768], np.uint8).reshape(256, 3).astype(np.float64) / 255


BASEP = (pal(239) * 255).astype(int)              # the native sprites are drawn in palette 239 (tier A, exact bypass)
LUT = {tuple(c): i for i, c in enumerate(BASEP)}
frames = sorted(p for p in NATIVE.glob('m238*.png') if p.name[4] in 'saw')
idx_pixels = []
for f in frames:
    a = np.asarray(Image.open(f).convert('RGBA'))
    m = a[..., 3] > 0
    idx_pixels.append(np.array([LUT.get(tuple(c), -1) for c in a[m][:, :3]]))
IDX = np.concatenate(idx_pixels)
import colorsys
_h = np.array([colorsys.rgb_to_hsv(*c) for c in pal(239)])
MAN = json.load(open(HERE.parent / 'mm7_m238' / 'manifest.json'))['recolor']['native_indices']
dif = np.array([i for i in MAN if _h[i, 1] > 0.2 and 0.22 < _h[i, 0] < 0.5])      # the green entries (cloth)
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
    if C['mist'].any():                                        # lift the mist toward the master's pale blue-white
        mL = R.luminance(g[C['mist']]); refL = R.luminance(MIST_REF[None, :])[0]
        tgt = MIST_REF[None, :] * (mL / max(np.median(mL), 1e-3))[:, None]
        g[C['mist']] = np.clip(g[C['mist']] * (1 - MIST_LIFT) + tgt * MIST_LIFT, 0, 1)
    g = ao_grade(g, load(HERE / 'work' / ao_png, 'L'), cov)
    print('CLASSES', tag, {k: int(m.sum()) for k, m in C.items()}, 'covered', int(cov.sum()),
          'skin albedo', np.round(albedo * 255).tolist())
    cls = np.zeros((N, N), np.uint8); spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8)
    for k, m in C.items():
        if m.any():
            cls[m] = CLASS[k]; spec[m] = SPEC[k]; rgh[m] = np.clip(ROUGH[k] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
    return g, normal, spec, rgh, cls, C, cov, albedo


RIG = json.load(open(HERE / 'work' / 'vortex.json'))
HIP_Z = RIG['top'] - 0.02                                     # the core cone below the hips is mist
HAIR_Z = 1.45
MIST_LIFT = float(os.environ.get('MIST_LIFT', '0.55'))       # 0 = Meshy's mist, 1 = the master's median colour
mm = np.asarray(Image.open(HERE / 'references_hd' / '01_front.png').convert('RGBA'), np.float64) / 255
low = mm[int(mm.shape[0] * 0.45):int(mm.shape[0] * 0.9)]
MIST_REF = np.median(low[low[..., 3] > 0.9][:, :3], 0)
print('MIST master median', np.round(MIST_REF * 255).tolist())
cfg_ramps = {}
g, normal, spec, rgh, cls, C, cov, ALB = build(HERE / 'meshy' / 'retexture_v1', 'uvraster_UVMap.npz', 'ao_UVMap.png', False, 'body')
lum = R.luminance(g)
cloth_l = [lum[C['cloth']]]
save(pad(g, cov), T / 'm238_basecolor_1k.png'); save(pad(normal, cov), T / 'm238_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'm238_metal_rough_1k.png')
mask = lambda m: ndimage.gaussian_filter(pad(m.astype(float), cov), 0.7)
R.write_mask([mask(C['cloth'])], T / 'm238_region_mask.png', size=N)
Image.fromarray(cls).save(T / 'm238_material_classes.png')
HM = HERE / 'meshy' / 'head_retexture_v1'
if HM.exists():
    hg, hn, hspec, hrgh, hcls, HC, hcov, _ = build(HM, 'uvraster_HeadUV.npz', 'ao_HeadUV.png', True, 'head', ALB)
    hl = R.luminance(hg); cloth_l.append(hl[HC['cloth']])
    save(pad(hg, hcov), T / 'm238_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'm238_head_normal_1k.png')
    save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm238_head_metal_rough_1k.png')
    hmask = lambda m: ndimage.gaussian_filter(pad(m.astype(float), hcov), 0.7)
    R.write_mask([hmask(HC['cloth'])], T / 'm238_head_region_mask.png', size=N)
    Image.fromarray(hcls).save(T / 'm238_head_material_classes.png')
cr = ramps_for('cloth', np.concatenate(cloth_l))
ramps = {k: [cr[k]] for k in PALS}
mats = [{'base': 'M238_A', 'prefix': 'M238', 'mask': 'm238_region_mask.png', 'regions': ['cloth'], 'palettes': PALS, 'ramps': ramps}]
if HM.exists():
    mats.append({'base': 'M238Head_A', 'prefix': 'M238Head', 'mask': 'm238_head_region_mask.png', 'regions': ['cloth'],
                 'palettes': PALS, 'ramps': ramps})
(T / 'm238_ramps.json').write_text(json.dumps({'variants': list(PALS), 'materials': mats}, indent=1) + '\n')
for k in PALS:
    print('RAMP', k, 'cloth mid', [round(x, 3) for x in cr[k]['colors'][8]])
# ---------------------------------------------------------------- lamp (Meshy maps)
LM = HERE / 'meshy' / 'lamp_geometry_v1'
LN = 512                                                       # a 30 cm corpse prop: Meshy's 2K maps cost ~22 MB
lb = np.asarray(Image.open(LM / 'texture_urls_0_base_color.png').convert('RGB').resize((LN, LN), Image.LANCZOS), np.float64) / 255
lr = np.asarray(Image.open(LM / 'texture_urls_0_roughness.png').convert('L').resize((LN, LN), Image.LANCZOS), np.float64) / 255
lh, ls_, lv = hsv(lb)
l_gold = (lh > 25) & (lh < 65) & (ls_ > 0.35)
save(np.stack([np.where(l_gold, 1.0, 0.8), np.clip(lr, 0.15, 1), np.zeros_like(lr)], -1), T / 'm238_lamp_metal_rough.png')
Image.open(LM / 'texture_urls_0_normal.png').convert('RGB').resize((LN, LN), Image.LANCZOS).save(T / 'm238_lamp_normal.png')
Image.fromarray((lb * 255 + 0.5).astype(np.uint8)).save(T / 'm238_lamp_basecolor.png')
print('PROPS lamp gold texels', int(l_gold.sum()))
