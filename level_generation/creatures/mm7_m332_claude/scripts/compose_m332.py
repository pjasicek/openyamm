#!/usr/bin/env python3
"""Textures, region mask and nine palette ramps for the m332 peasant elf (after ../mm7_m302_claude/scripts/compose_m302.py;
CLAUDE_CREATURE_TEXTURES.md). Run after transfer_uv.py, uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py.
Regions, as the native ACT swaps: R = cloth (entries 150-245: the burgundy tights; body: the skin shell P00 below the
belt, red hue, not the brown shoes), G = hair (entries 107-146: the ponytail P04 and the blonde hair painted on the scalp
of the head set's P00). Skin, vest, bracers, belt, brass and the dagger keep their colour.
- Body skin (arms, chest, hands) repainted to one albedo x Meshy's fine shading; the head keeps Meshy's colour; the eye
  shells get procedural sclera, iris and pupil (Meshy painted them skin-coloured, as on m312).
- Base colour graded by the rest-pose AO; ORM red = per-class specular (openyamm_specular_mask), green = roughness.
- Ramps rank-matched to the native pixels (palette 59 order) x RAMP_GAIN, over the region texels' 2nd-98th luminance
  percentile.
Writes textures/m332_*."""
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
X = 'm332'
SKIN_MIX, RAMP_GAIN = 0.85, 1.35
# descriptors 340-348: outfit A (340-342), B (343-345), C (346-348), tiers 1-3 (palettes from ../mm7_m332/variants.json)
PALS = {f'{X}_a1': 333, f'{X}_a2': 334, f'{X}_a3': 59, f'{X}_b1': 60, f'{X}_b2': 61, f'{X}_b3': 62,
        f'{X}_c1': 339, f'{X}_c2': 340, f'{X}_c3': 341}
BASE_PAL = 59
REGION_IDX = {'cloth': (150, 246), 'hair': (107, 147)}
BELT_Z = 1.0
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


def classify(base, cov, piece, pos, head=False):
    hue, sat, val = hsv(base)
    eye = cov & np.isin(piece, [28, 29])
    if head:
        blonde = (hue > 38) & (hue < 75) & (sat > 0.25) & (val > 0.35)
        hair = cov & ((piece == 4) | ((piece == 0) & blonde))
        skin = cov & (piece == 0) & ~hair
        return {'hair': hair, 'skin': skin, 'eye': eye}
    red = ((hue > 300) | (hue < 14)) & (sat > 0.3)
    z = pos[..., 2]
    shoe = (z < 0.16) & ~red & (hue > 12) & (hue < 50)       # brown shoe leather at the ankles
    cloth = cov & (piece == 0) & (z < BELT_Z) & (z > 0.06) & ~shoe & (np.abs(pos[..., 0]) < 0.3)   # the tights by position (the arms hang outside |x| 0.3)
    cloth |= cov & (piece == 0) & (z >= BELT_Z) & (z < BELT_Z + 0.08) & red & (np.abs(pos[..., 0]) < 0.3)   # tights paint up to the belt
    metal = cov & np.isin(piece, [5, 15, 6, 8, 10, 11, 12, 13, 14, 16, 17, 19, 23, 25, 31]) & (hue > 30) & (hue < 65) & (sat > 0.3)
    skin = cov & np.isin(piece, [0, 2, 3]) & ~cloth & (pos[..., 2] >= BELT_Z - 0.02) & ((hue < 35) | (hue > 340)) & (sat > 0.15) & (sat < 0.65) & (val > 0.35)
    skin |= cov & np.isin(piece, [2, 3]) & ((hue < 35) | (hue > 340)) & (sat > 0.12)
    leather = cov & ~(cloth | metal | skin | eye)
    return {'cloth': cloth, 'skin': skin, 'metal': metal, 'leather': leather, 'eye': eye}


# ---------------------------------------------------------------- body set
M = HERE / 'meshy' / 'body_retexture_v1'
base = load(M / 'texture_urls_0_base_color.png'); normal = load(M / 'texture_urls_0_normal.png')
rough_m = load(M / 'texture_urls_0_roughness.png', 'L')
Rz = np.load(HERE / 'work' / 'uvraster_UVMap.npz'); piece = Rz['piece']; cov = piece >= 0
C = classify(base, cov, piece, Rz['pos'])
HM = HERE / 'meshy' / 'head_retexture_v1'
hb = load(HM / 'texture_urls_0_base_color.png'); hn = load(HM / 'texture_urls_0_normal.png')
hr_m = load(HM / 'texture_urls_0_roughness.png', 'L')
Rh = np.load(HERE / 'work' / 'uvraster_HeadUV.npz'); hpiece = Rh['piece']; hcov = hpiece >= 0
HC = classify(hb, hcov, hpiece, Rh['pos'], head=True)
hb = hb.copy()
for e in (28, 29):
    m = hcov & (hpiece == e); P_ = Rh['pos'][m]; c = P_.mean(0)
    c = (P_.min(0) + P_.max(0)) / 2; fw = np.array([0.0, -1.0, 0.0])                 # box centre, looking forward
    d = P_ - c; d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
    ang = np.arccos(np.clip(d @ fw, -1, 1))
    col = np.where((ang < 0.38)[:, None], [0.06, 0.06, 0.08], np.where((ang < 0.85)[:, None], [0.30, 0.42, 0.50], [0.80, 0.77, 0.73]))
    col[(ang > 0.75) & (ang < 0.85)] = [0.16, 0.21, 0.26]
    hb[m] = col
print('EYES painted', int((hcov & np.isin(hpiece, [28, 29])).sum()), 'texels')
SKIN = np.median(base[C['skin']], 0)
# Meshy painted near-black patches on the tights (they ramp to black in every look): outlier-dark cloth texels are
# lifted to the cloth's median colour x their clipped relative luminance
base = base.copy()
Lc = R.luminance(base); medc = float(np.median(Lc[C['cloth']])); medcol = np.median(base[C['cloth']], 0)
dark = C['cloth'] & (Lc < 0.55 * medc)
cl = C['cloth']
base[cl] = medcol[None, :] * np.clip(np.sqrt(np.maximum(Lc[cl], 1e-6) / medc), 0.8, 1.2)[:, None]   # plain tights: half contrast
print('CLOTH tights flattened around the median, dark patches', int(dark.sum()), 'texels')
# neck seam: both sets painted the vest collar as a dark jagged band around the neck (head cut at z 1.462); the neck
# skin from NECK_LO up to NECK_HI is flat skin (body albedo) x AO, feathered over 3 cm at both ends
NECK_LO, NECK_HI = 1.40, 1.50
def neck_fix(img, pc, pos, cov_, extra=None):
    z = pos[..., 2]; m = cov_ & (pc == 0) & (z > NECK_LO - 0.03) & (z < NECK_HI + 0.03)
    if extra is not None:
        m &= extra
    w = np.clip(np.minimum(z - (NECK_LO - 0.03), (NECK_HI + 0.03) - z) / 0.03, 0, 1)
    out = img.copy(); out[m] = img[m] * (1 - w[m][:, None]) + SKIN[None, :] * w[m][:, None]
    return out, m
base, neck_b = neck_fix(base, piece, Rz['pos'], cov, ~C['leather'] | (Rz['pos'][..., 2] > 1.43))
C['skin'] |= neck_b; C['leather'] &= ~neck_b
print('NECK body texels', int(neck_b.sum()))
print('SKIN albedo sRGB', np.round(SKIN * 255).tolist())
g = ao_grade(repaint_skin(base, C['skin'], SKIN), load(HERE / 'work' / 'ao_UVMap.png', 'L'), cov)
# the tights' native ramp spans a narrow luminance band: the rest-pose AO (dark spots on the seat) swung them to black;
# they take no AO grade (the engine shades them)
g[C['cloth']] = base[C['cloth']]
hb, neck_h = neck_fix(hb, hpiece, Rh['pos'], hcov, ~HC['hair'])
HC['skin'] |= neck_h
print('NECK head texels', int(neck_h.sum()))
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
    if region == 'cloth':                       # flattened tights: a fixed band around their median
        md = float(np.median(lum[region])); lo, hi = md * 0.6, md * 1.4
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
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Elf_A', 'prefix': 'Elf', 'mask': f'{X}_region_mask.png', 'regions': list(REGION_IDX),
                      'palettes': PALS, 'ramps': ramps},
                     {'base': 'ElfHead_A', 'prefix': 'ElfHead', 'mask': f'{X}_head_region_mask.png',
                      'regions': list(REGION_IDX), 'ramps': ramps}]}
(T / f'{X}_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
(T / f'{X}_swatches.json').write_text(json.dumps({'skin_srgb': [round(float(v) * 255) for v in SKIN]}, indent=1) + '\n')
