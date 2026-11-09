#!/usr/bin/env python3
"""Textures, region mask and nine palette ramps for the m312 peasant dwarf woman (after ../mm7_m302_claude/scripts/compose_m302.py;
CLAUDE_CREATURE_TEXTURES.md). Run after transfer_uv.py, uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py.
Regions, as the native ACT swaps: R = cloth (entries 138-239: the purple dress - bodice, sleeve stripes, skirt - and the
dress-coloured stains on the apron, which follow the dress in every native look), G = hair (entries 28-59: bun and
ringlets on the head set, and hair paint on the face shell's hairline). Skin, the white apron and chemise, lacing,
shoes, earrings and scissors keep their colour.
- The legs (piece 3) above the shoes are hidden by the dress in every standing clip and show only in the death: they
  are painted as dress cloth (the skirt's median colour x Meshy's shading) inside the cloth region, so a raised leg
  reads as the dress over it.
- Hands repainted to one skin albedo x Meshy's fine shading; the head keeps Meshy's colour.
- Ramps rank-matched to the native pixels (palette 313 luminance order), x RAMP_GAIN, over the region texels'
  2nd-98th luminance percentile.
Writes textures/m312_*."""
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
X = 'm312'
SKIN_MIX, RAMP_GAIN = 0.85, 1.35
# descriptors 322-330: outfit A (322-324), B (325-327), C (328-330), tiers 1-3
# descriptors 313-321: outfit A (313-315), B (316-318), C (319-321), tiers 1-3
PALS = {f'{X}_a1': 313, f'{X}_a2': 314, f'{X}_a3': 315, f'{X}_b1': 316, f'{X}_b2': 317, f'{X}_b3': 318,
        f'{X}_c1': 319, f'{X}_c2': 320, f'{X}_c3': 321}
BASE_PAL = 313
REGION_IDX = {'cloth': (138, 240), 'hair': (28, 60)}
LEG_Z = 0.13                                   # the shoe tops (1.7 m model scale)
SPEC = {'linen': 0.15, 'skin': 0.45, 'cloth': 0.2, 'wool': 0.15, 'fleece': 0.15, 'leather': 0.35, 'metal': 0.7, 'hair': 0.3, 'eye': 0.9}
ROUGH = {'linen': 0.85, 'skin': 0.55, 'cloth': 0.85, 'wool': 0.9, 'fleece': 0.9, 'leather': 0.6, 'metal': 0.35, 'hair': 0.65, 'eye': 0.2}
CLASS_ID = {'linen': 8, 'skin': 1, 'hair': 2, 'cloth': 8, 'wool': 8, 'fleece': 2, 'leather': 8, 'metal': 9, 'eye': 6}


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
    purple = (hue > 235) & (hue < 320) & (sat > 0.22) & (val > 0.06)
    eye = cov & np.isin(piece, [20, 21])
    if head:
        blonde = (hue > 35) & (hue < 65) & (sat > 0.25) & (val > 0.35)
        hair = cov & (np.isin(piece, [4, 7, 8]) | ((piece == 1) & blonde))
        metal = cov & np.isin(piece, [15, 16])
        cloth = cov & (piece == 1) & purple & ~hair & (val < 0.55)   # bodice paint at the neckline (not the pale chemise specks)
        skin = cov & np.isin(piece, [1, 25]) & ~hair & ~cloth
        return {'cloth': cloth, 'hair': hair, 'skin': skin, 'eye': eye, 'metal': metal}
    legs = cov & (piece == 3) & (pos[..., 2] > LEG_Z)
    cloth = cov & (purple | legs) & ~np.isin(piece, [5, 6])
    skin = cov & np.isin(piece, [5, 6]) & ((hue < 40) | (hue > 330)) & (sat > 0.12)
    metal = cov & np.isin(piece, [26, 27, 28, 29])
    white = cov & ~cloth & ~skin & ~metal & (sat < 0.2) & (val > 0.45)
    leather = cov & ~(cloth | skin | metal | white | eye)
    return {'cloth': cloth, 'skin': skin, 'metal': metal, 'linen': white, 'leather': leather, 'eye': eye, 'legs': legs}


# ---------------------------------------------------------------- body set
M = HERE / 'meshy' / 'body_retexture_v1'
base = load(M / 'texture_urls_0_base_color.png'); normal = load(M / 'texture_urls_0_normal.png')
rough_m = load(M / 'texture_urls_0_roughness.png', 'L')
Rz = np.load(HERE / 'work' / 'uvraster_UVMap.npz'); piece = Rz['piece']; cov = piece >= 0
C = classify(base, cov, piece, Rz['pos'])
LEGS = C.pop('legs')
HM = HERE / 'meshy' / 'head_retexture_v1'
hb = load(HM / 'texture_urls_0_base_color.png'); hn = load(HM / 'texture_urls_0_normal.png')
hr_m = load(HM / 'texture_urls_0_roughness.png', 'L')
Rh = np.load(HERE / 'work' / 'uvraster_HeadUV.npz'); hpiece = Rh['piece']; hcov = hpiece >= 0
HC = classify(hb, hcov, hpiece, Rh['pos'], head=True)
# eyes: Meshy painted the eye shells skin-coloured; procedural sclera, blue iris and pupil looking forward (-Y)
hb = hb.copy()
for e in (20, 21):
    m = hcov & (hpiece == e); P_ = Rh['pos'][m]; c = P_.mean(0)
    d = P_ - c; d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
    ang = np.arccos(np.clip(-d[:, 1], -1, 1))
    col = np.where((ang < 0.22)[:, None], [0.07, 0.07, 0.09], np.where((ang < 0.5)[:, None], [0.27, 0.43, 0.6], [0.88, 0.84, 0.8]))
    col[(ang > 0.44) & (ang < 0.5)] = [0.17, 0.25, 0.35]
    hb[m] = col
# chest skin of the head shell (below the neck, z < CHEST_Z): the head retexture mixed bodice and chemise paint into the
# cleavage; repaint it to the face's skin albedo x Meshy's fine shading (out of the cloth mask)
CHEST_Z = 1.30
chest = hcov & (hpiece == 1) & (Rh['pos'][..., 2] < CHEST_Z + 0.02)
neck = hcov & (hpiece == 1) & (Rh['pos'][..., 2] >= CHEST_Z) & (Rh['pos'][..., 2] < CHEST_Z + 0.06) & HC['skin']
FACE = np.median(hb[neck], 0)
# flat: Meshy's shading on these tiny islands read as crumpled facets; feathered into the neck over FEATHER m
FEATHER = 0.06
zz = Rh['pos'][..., 2]; wch = np.clip((CHEST_Z + 0.02 - zz) / FEATHER, 0, 1)
blend = hcov & (hpiece == 1) & (wch > 0)
hb[blend] = hb[blend] * (1 - wch[blend][:, None]) + FACE[None, :] * wch[blend][:, None]
HC['cloth'] &= ~chest; HC['skin'] |= chest
print('CHEST repainted', int(chest.sum()), 'texels, face sRGB', np.round(FACE * 255).tolist())
print('EYES painted', int((hcov & np.isin(hpiece, [20, 21])).sum()), 'texels')
SKIN = np.median(base[C['skin']], 0)
print('SKIN albedo sRGB', np.round(SKIN * 255).tolist())
DRESS = np.median(base[C['cloth'] & (piece == 2)], 0)
base = base.copy()
Lb = R.luminance(base); dl = np.clip(Lb / max(float(np.median(Lb[C['cloth'] & (piece == 2)])), 1e-4), 0.6, 1.4)
base[LEGS] = DRESS[None, :] * dl[LEGS][:, None]
print('LEGS painted as the dress', int(LEGS.sum()), 'texels, dress sRGB', np.round(DRESS * 255).tolist())
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
cfg = {'variants': list(PALS),
       'materials': [{'base': 'M312_A', 'prefix': 'M312', 'mask': f'{X}_region_mask.png', 'regions': list(REGION_IDX),
                      'palettes': PALS, 'ramps': ramps},
                     {'base': 'M312Head_A', 'prefix': 'M312Head', 'mask': f'{X}_head_region_mask.png',
                      'regions': list(REGION_IDX), 'ramps': ramps}]}
(T / f'{X}_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
(T / f'{X}_swatches.json').write_text(json.dumps({'skin_srgb': [round(float(v) * 255) for v in SKIN]}, indent=1) + '\n')
