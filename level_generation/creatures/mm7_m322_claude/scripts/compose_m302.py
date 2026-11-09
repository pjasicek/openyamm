#!/usr/bin/env python3
"""Textures, region mask and nine palette ramps for the m302 peasant dwarf (after compose_m190.py; CLAUDE_CREATURE_TEXTURES.md).
Run after transfer_uv.py, uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py.
Regions, as the native ACT swaps (the 118 entries that differ between the nine palettes): R = cloth (entries 160-248:
the green cap and shirt; body: green texels of the skin shell P00 and trousers P03 - sleeves and the shirt band; head:
the cap P04), G = hair (entries 97-137: beard P02 and nape hair P05 on the head set, plus the brows/moustache painted on
the face skin: dark saturated brown texels of P00 in the head set). Skin, vest leather and fleece, trousers, belt,
bracers and boots keep their colour.
- Body skin (hands, neck: P00 texels of skin hue that are not green and not leather-dark) repainted to one albedo (median of
  the classified skin) times Meshy's fine shading (SKIN_MIX); the head keeps Meshy's colour.
- Base colour graded by the rest-pose AO; ORM red = per-class specular (openyamm_specular_mask), green = roughness.
- Ramps rank-matched to the native pixels: the region's native pixels (standing and walking frames) ordered by their
  base palette-58 luminance; stop i takes, in every palette, the mean colour of the pixels in the i-th 16-quantile
  window x RAMP_GAIN (sprites carry baked shading), over the region texels' 2nd-98th luminance percentile. One texel
  luminance therefore maps to the same native pixel rank in all nine looks.
- The club keeps its own texture (make_club.py); ORM from its colour (wood).
Writes textures/m302_*."""
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
X = 'm302'
SKIN_MIX, RAMP_GAIN = 0.85, 1.35
# descriptors 322-330: outfit A (322-324), B (325-327), C (328-330), tiers 1-3
PALS = {f'{X}_a1': 303, f'{X}_a2': 304, f'{X}_a3': 305, f'{X}_b1': 58, f'{X}_b2': 307, f'{X}_b3': 308,
        f'{X}_c1': 309, f'{X}_c2': 310, f'{X}_c3': 311}
BASE_PAL = 58
REGION_IDX = {'cloth': (160, 249), 'hair': (97, 138)}
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
    green = (hue > 70) & (hue < 175) & (sat > 0.22) & (val > 0.06)
    eye = cov & np.isin(piece, [8, 9])
    if head:
        cloth = cov & ((piece == 4) | (green & (piece == 0)))   # the cap, and cap paint on the face shell (not the olive beard)
        hair = cov & np.isin(piece, [2, 5]) & ~cloth
        # brows/moustache painted on the face skin: darker, more saturated brown than the face
        hair |= cov & (piece == 0) & (hue > 8) & (hue < 40) & (sat > 0.5) & (val < 0.42)
        skin = cov & (piece == 0) & ~hair
        return {'cloth': cloth, 'hair': hair, 'skin': skin, 'eye': eye}
    cloth = cov & green                                       # sleeves, shirt band; shirt paint at the vest edges
    fleece = cov & np.isin(piece, [1, 6, 7]) & (sat < 0.3) & (val > 0.55)
    metal = cov & (piece == 3) & (sat < 0.15) & (val > 0.55) & ~fleece
    skin = cov & (piece == 0) & ~cloth & ((hue < 32) | (hue > 340)) & (sat > 0.18) & (sat < 0.62) & (val > 0.42)
    wool = cov & (piece == 3) & ~cloth & ~metal & (sat < 0.35) & (val > 0.3)
    leather = cov & ~(cloth | fleece | metal | skin | wool | eye)
    return {'cloth': cloth, 'fleece': fleece, 'metal': metal, 'skin': skin, 'wool': wool, 'leather': leather, 'eye': eye}


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
R.write_mask([soft(HC['cloth'], hcov), soft(HC['hair'], hcov)], T / f'{X}_head_region_mask.png', size=N)
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
lum = {'cloth': R.luminance(np.concatenate([g[C['cloth']], hg[HC['cloth']]])), 'hair': R.luminance(hg[HC['hair']])}
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
            w = p_all[int(n * i / 16):max(int(n * (i + 1) / 16), int(n * i / 16) + 1)]
            c = pal[pid][w].mean(0)
            cols.append(np.clip(lin(np.clip(c * RAMP_GAIN, 0, 1)), 0, 1))
        ramps[k].append({'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': [[round(float(v), 6) for v in c] for c in cols]})
        report[f'{region}_{k}'] = [[round(float(v) * 255) for v in srgb(cols[j])] for j in (2, 8, 14)]
    print('NATIVE', region, 'pixels', n, 'texel luminance range', round(float(lo), 4), round(float(hi), 4))
print('RAMPS sRGB stops 2/8/14', json.dumps(report))
# ---------------------------------------------------------------- club
cl = np.asarray(Image.open(T / f'{X}_club_basecolor.png').convert('RGB'), np.float64) / 255
save(np.stack([np.full(cl.shape[:2], 0.3), np.full(cl.shape[:2], 0.75), np.zeros(cl.shape[:2])], -1), T / f'{X}_club_metal_rough.png')
save(np.dstack([np.full(cl.shape[:2], 0.5), np.full(cl.shape[:2], 0.5), np.ones(cl.shape[:2])]), T / f'{X}_club_normal.png')
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Dwarf_A', 'prefix': 'Dwarf', 'mask': f'{X}_region_mask.png', 'regions': list(REGION_IDX),
                      'palettes': PALS, 'ramps': ramps},
                     {'base': 'DwarfHead_A', 'prefix': 'DwarfHead', 'mask': f'{X}_head_region_mask.png',
                      'regions': list(REGION_IDX), 'ramps': ramps}]}
(T / f'{X}_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
(T / f'{X}_swatches.json').write_text(json.dumps({'skin_srgb': [round(float(v) * 255) for v in SKIN]}, indent=1) + '\n')
