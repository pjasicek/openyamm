#!/usr/bin/env python3
"""Textures, region mask and nine palette ramps for the m322 peasant elf woman (after ../mm7_m302_claude/scripts/compose_m302.py;
CLAUDE_CREATURE_TEXTURES.md). Run after transfer_uv.py, uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py.
Regions, as the native ACT swaps: R = cloth (entries 100-169: the green trousers), G = hair (entries 174-234: the long
red hair, its dark magenta shades included; head set: the hair shell P01 and hair paint on the face shell's hairline).
Skin, the leather vest, bracers and boots, the brass studs/grommets and the staff keep their colour.
- Body skin (bare arms, midriff, chest, the skin through the trouser lacing, hands) repainted to one albedo x Meshy's
  fine shading (SKIN_MIX); the head keeps Meshy's colour (procedural eyes if Meshy painted the eye shells over).
- Ramps from the native pixels (palette 323 luminance order), x RAMP_GAIN, over the region texels' 2nd-98th luminance
  percentile: cloth rank-matched (16 equal rank windows), hair histogram-matched (stop i takes the native colour at the
  hair texels' luminance quantile of that stop; the linear rank map turned the base red hair magenta).
Writes textures/m322_*."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
N = 1024
X = 'm322'
SKIN_MIX, RAMP_GAIN = 0.85, 1.35
# descriptors 331-339: outfit A (331-333), B (334-336), C (337-339), tiers 1-3
PALS = {f'{X}_a1': 323, f'{X}_a2': 324, f'{X}_a3': 325, f'{X}_b1': 326, f'{X}_b2': 327, f'{X}_b3': 328,
        f'{X}_c1': 329, f'{X}_c2': 330, f'{X}_c3': 331}
BASE_PAL = 323
REGION_IDX = {'cloth': (100, 170), 'hair': (174, 235)}
SPEC = {'skin': 0.45, 'cloth': 0.2, 'wool': 0.15, 'fleece': 0.15, 'leather': 0.35, 'metal': 0.7, 'hair': 0.3, 'eye': 0.9}
ROUGH = {'skin': 0.55, 'cloth': 0.85, 'wool': 0.9, 'fleece': 0.9, 'leather': 0.6, 'metal': 0.35, 'hair': 0.65, 'eye': 0.2}
CLASS_ID = {'skin': 1, 'hair': 2, 'cloth': 8, 'wool': 8, 'fleece': 2, 'leather': 8, 'metal': 9, 'eye': 6}


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


lin = R.srgb_to_linear
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


def classify(base, cov, piece, head=False):
    hue, sat, val = hsv(base)
    green = (hue > 70) & (hue < 175) & (sat > 0.2) & (val > 0.06)
    red = ((hue < 25) | (hue > 300)) & (sat > 0.45)
    eye = cov & np.isin(piece, [4, 5])
    if head:
        hair = cov & ((piece == 1) | ((piece == 0) & red & (val < 0.75) & (sat > 0.55)))
        skin = cov & np.isin(piece, [0, 8, 9, 11]) & ~hair
        return {'hair': hair, 'skin': skin, 'eye': eye}
    cloth = cov & green & (piece == 0)
    skin = cov & np.isin(piece, [0, 2, 3]) & ~cloth & ((hue < 32) | (hue > 340)) & (sat > 0.15) & (sat < 0.6) & (val > 0.45)
    skin |= cov & np.isin(piece, [2, 3])
    metal = cov & (piece >= 6) & ~np.isin(piece, [8, 9, 11]) & (hue > 30) & (hue < 65) & (sat > 0.3) & (val > 0.35)
    leather = cov & ~(cloth | skin | metal | eye)
    return {'cloth': cloth, 'skin': skin, 'metal': metal, 'leather': leather, 'eye': eye}


# ---------------------------------------------------------------- body set
M = HERE / 'meshy' / 'body_retexture_v1'
base = load(M / 'texture_urls_0_base_color.png'); normal = load(M / 'texture_urls_0_normal.png')
rough_m = load(M / 'texture_urls_0_roughness.png', 'L')
Rz = np.load(HERE / 'work' / 'uvraster_UVMap.npz'); piece = Rz['piece']; cov = piece >= 0
C = classify(base, cov, piece)
HM = HERE / 'meshy' / 'head_retexture_v1'
hb = load(HM / 'texture_urls_0_base_color.png'); hn = load(HM / 'texture_urls_0_normal.png')
hr_m = load(HM / 'texture_urls_0_roughness.png', 'L')
Rh = np.load(HERE / 'work' / 'uvraster_HeadUV.npz'); hpiece = Rh['piece']; hcov = hpiece >= 0
HC = classify(hb, hcov, hpiece, head=True)
SKIN = np.median(base[C['skin']], 0)
print('SKIN albedo sRGB', np.round(SKIN * 255).tolist())
g = ao_grade(repaint_skin(base, C['skin'], SKIN), load(HERE / 'work' / 'ao_UVMap.png', 'L'), cov)
hg = ao_grade(hb, load(HERE / 'work' / 'ao_HeadUV.png', 'L'), hcov)
print('CLASSES body', {k: int(m.sum()) for k, m in C.items()}, 'covered', int(cov.sum()))
print('CLASSES head', {k: int(m.sum()) for k, m in HC.items()}, 'covered', int(hcov.sum()))


def maps(rgh_m, cls):
    spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8); cm = np.zeros((N, N), np.uint8)
    for k, m in cls.items():
        if not m.any():
            continue
        cm[m] = CLASS_ID[k]; spec[m] = SPEC[k]
        rgh[m] = np.clip(ROUGH[k] + (rgh_m[m] - np.median(rgh_m[m])) * 0.5, 0.1, 1)
    return spec, rgh, cm


spec, rgh, cm = maps(rough_m, C)
save(pad(g, cov), T / f'{X}_basecolor_1k.png'); save(pad(normal, cov), T / f'{X}_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / f'{X}_metal_rough_1k.png')
Image.fromarray(cm).save(T / f'{X}_material_classes.png')
hspec, hrgh, hcm = maps(hr_m, HC)
save(pad(hg, hcov), T / f'{X}_head_basecolor_1k.png'); save(pad(hn, hcov), T / f'{X}_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / f'{X}_head_metal_rough_1k.png')
Image.fromarray(hcm).save(T / f'{X}_head_material_classes.png')


def soft(m, c):
    return np.clip(ndimage.gaussian_filter(pad(m.astype(float), c), 0.7), 0, 1)


R.write_mask([soft(C['cloth'], cov), np.zeros((N, N))], T / f'{X}_region_mask.png', size=N)
R.write_mask([np.zeros((N, N)), soft(HC['hair'], hcov)], T / f'{X}_head_region_mask.png', size=N)
# ---------------------------------------------------------------- ramps (rank-matched to the native sprite pixels)
INV = json.loads((HERE / 'references_native' / 'inventory.json').read_text())
pal = {p: np.frombuffer((REPO / INV['palette_sources'][str(p)]['path']).read_bytes()[:768], np.uint8).reshape(256, 3) / 255
       for p in set(PALS.values())}
chg = np.zeros(256, bool)
for p in pal:
    chg |= np.abs(pal[p] - pal[BASE_PAL]).max(1) > 0.03
FRAMES = [k for k in INV['sources'] if k[len(X):len(X) + 1] in 'sw']
pix = {r: [] for r in REGION_IDX}
for fr in FRAMES:
    idx = np.array(Image.open(REPO / INV['sources'][fr]['path']))
    for region, (a, b) in REGION_IDX.items():
        m = (idx >= a) & (idx < b) & chg[idx]
        pix[region].append(idx[m])
lum = {'cloth': R.luminance(g[C['cloth']]), 'hair': R.luminance(hg[HC['hair']])}
ramps = {k: [] for k in PALS}
report = {}
for region in REGION_IDX:
    lo, hi = np.percentile(lum[region], [2, 98])
    p_all = np.concatenate(pix[region])
    order = np.argsort(R.luminance(pal[BASE_PAL][p_all]), kind='stable'); p_all = p_all[order]
    n = len(p_all)
    for k, pid in PALS.items():
        cols = []
        for i in range(16):
            # histogram match (m322: the hair texels sit low in their range and a linear rank map turned the base
            # red hair magenta): stop i takes the native colour at the texel-luminance quantile of its luminance
            if region == 'hair':
                q = float(np.mean(lum[region] <= lo + (hi - lo) * i / 15))
                a_ = int(np.clip(q - 1 / 32, 0, 1) * (n - 1)); b_ = max(int(np.clip(q + 1 / 32, 0, 1) * (n - 1)), a_ + 1)
                w = p_all[a_:b_]
            else:                                       # cloth: linear rank map (matching its histogram darkened it)
                w = p_all[int(n * i / 16):max(int(n * (i + 1) / 16), int(n * i / 16) + 1)]
            c = pal[pid][w].mean(0)
            cols.append(np.clip(lin(np.clip(c * RAMP_GAIN, 0, 1)), 0, 1))
        ramps[k].append({'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': [[round(float(v), 6) for v in c] for c in cols]})
        report[f'{region}_{k}'] = [[round(float(v) * 255) for v in srgb(cols[j])] for j in (2, 8, 14)]
    print('NATIVE', region, 'pixels', n, 'texel luminance range', round(float(lo), 4), round(float(hi), 4))
print('RAMPS sRGB stops 2/8/14', json.dumps(report))
# ---------------------------------------------------------------- staff
st = np.asarray(Image.open(T / f'{X}_staff_basecolor.png').convert('RGB'), np.float64) / 255
save(np.stack([np.full(st.shape[:2], 0.3), np.full(st.shape[:2], 0.75), np.zeros(st.shape[:2])], -1), T / f'{X}_staff_metal_rough.png')
save(np.dstack([np.full(st.shape[:2], 0.5), np.full(st.shape[:2], 0.5), np.ones(st.shape[:2])]), T / f'{X}_staff_normal.png')
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Elf_A', 'prefix': 'Elf', 'mask': f'{X}_region_mask.png', 'regions': list(REGION_IDX),
                      'palettes': PALS, 'ramps': ramps},
                     {'base': 'ElfHead_A', 'prefix': 'ElfHead', 'mask': f'{X}_head_region_mask.png',
                      'regions': list(REGION_IDX), 'ramps': ramps}]}
(T / f'{X}_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
(T / f'{X}_swatches.json').write_text(json.dumps({'skin_srgb': [round(float(v) * 255) for v in SKIN]}, indent=1) + '\n')
