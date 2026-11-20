#!/usr/bin/env python3
"""Textures, region mask and nine palette ramps for the 7m452 peasant goblin (after ../mm7_m302_claude/scripts/compose_m302.py;
CLAUDE_CREATURE_TEXTURES.md). Run after transfer_uv.py, uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py.
Regions, as the native ACT swaps (the green skin never changes): R = tunic (entries 185-255: the red cloth of the torso
shell and the skirt), G = trousers (entries 152-181: the trouser shell), B = topknot (entries 135-150: the grey hair
on top of the head set; the brown tie stays). Fur trim, belt, bracers, buckle, boots and skin keep their colour.
- Body skin (bare arms, neck, hands: true-HSV green, gob2 rule) repainted to one albedo x Meshy's fine shading; the head
  keeps Meshy's colour.
- Ramps histogram-matched to the native pixels (palette 497 luminance order): stop i (texel luminance lo + i/15 (hi -
  lo), the region texels' 2nd-98th percentile) takes each palette's mean colour around the same quantile of the native
  pixels as that luminance has among the texels, x RAMP_GAIN. (Rank windows of equal native width made the dark-skewed
  trousers render near-black.) Red tunic paint on the head shell's neckline is in the tunic region too.
- The billhook keeps its own texture (make_billhook.py); ORM from its colour (iron vs wood).
Writes textures/7m452_*."""
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
X = '7m452'
SKIN_MIX, RAMP_GAIN = 0.85, 1.35
# descriptors 439-447: outfit A (439-441), B (442-444), C (445-447), tiers 1-3
PALS = {f'{X}_a1': 453, f'{X}_a2': 454, f'{X}_a3': 455, f'{X}_b1': 393, f'{X}_b2': 493, f'{X}_b3': 494,
        f'{X}_c1': 495, f'{X}_c2': 497, f'{X}_c3': 498}
BASE_PAL = 497
REGION_IDX = {'tunic': (185, 256), 'trousers': (152, 182), 'hair': (135, 151)}
HAIR_Z = 1.66                                   # the topknot rises above the scalp (1.8 m model)
SPEC = {'tunic': 0.2, 'trousers': 0.2, 'fur': 0.15, 'skin': 0.45, 'cloth': 0.2, 'wool': 0.15, 'fleece': 0.15, 'leather': 0.35, 'metal': 0.7, 'hair': 0.3, 'eye': 0.9}
ROUGH = {'tunic': 0.85, 'trousers': 0.85, 'fur': 0.9, 'skin': 0.55, 'cloth': 0.85, 'wool': 0.9, 'fleece': 0.9, 'leather': 0.6, 'metal': 0.35, 'hair': 0.65, 'eye': 0.2}
CLASS_ID = {'tunic': 8, 'trousers': 8, 'fur': 2, 'skin': 1, 'hair': 2, 'cloth': 8, 'wool': 8, 'fleece': 2, 'leather': 8, 'metal': 9, 'eye': 6}


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
    green = (hue > 55) & (hue < 130) & (sat > 0.2) & (val > 0.12)
    red = ((hue < 25) | (hue > 330)) & (sat > 0.3) & (val > 0.12)
    eye = cov & np.isin(piece, [11, 12])
    if head:
        hair = cov & (piece == 1) & (pos[..., 2] > HAIR_Z) & (sat < 0.3) & (val > 0.3)
        tunic = cov & (piece == 1) & red & (pos[..., 2] < HAIR_Z - 0.15)   # tunic paint at the neckline of the head shell
        skin = cov & np.isin(piece, [1, 13]) & ~hair & ~tunic
        return {'tunic': tunic, 'hair': hair, 'skin': skin, 'eye': eye}
    tunic = cov & np.isin(piece, [0, 3]) & red
    trousers = cov & (piece == 2)
    skin = cov & np.isin(piece, [0, 4, 5]) & green
    fur = cov & np.isin(piece, [0, 3]) & ~tunic & ~skin & (sat < 0.25) & (val > 0.45)
    metal = cov & np.isin(piece, [8, 9, 10, 14]) & (hue > 30) & (hue < 65) & (sat > 0.35) & (val > 0.4)
    leather = cov & ~(tunic | trousers | skin | fur | metal | eye)
    return {'tunic': tunic, 'trousers': trousers, 'skin': skin, 'fur': fur, 'metal': metal, 'leather': leather, 'eye': eye}


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


R.write_mask([soft(C['tunic'], cov), soft(C['trousers'], cov), np.zeros((N, N))], T / f'{X}_region_mask.png', size=N)
R.write_mask([soft(HC['tunic'], hcov), np.zeros((N, N)), soft(HC['hair'], hcov)], T / f'{X}_head_region_mask.png', size=N)
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
lum = {'tunic': R.luminance(np.concatenate([g[C['tunic']], hg[HC['tunic']]])), 'trousers': R.luminance(g[C['trousers']]), 'hair': R.luminance(hg[HC['hair']])}
ramps = {k: [] for k in PALS}
report = {}
for region in REGION_IDX:
    lo, hi = np.percentile(lum[region], [2, 98])
    p_all = np.concatenate(pix[region])
    order = np.argsort(R.luminance(pal[BASE_PAL][p_all]), kind='stable'); p_all = p_all[order]
    n = len(p_all)
    for k, pid in PALS.items():
        cols = []
        # histogram matching: stop i sits at texel luminance lo + i/15 (hi - lo); it takes the native colour at the
        # same quantile among the native pixels as that luminance has among the region's texels (window +-1/32)
        Ls = np.sort(lum[region])
        for i in range(16):
            q = float(np.searchsorted(Ls, lo + (hi - lo) * i / 15) / len(Ls))
            w = p_all[int(n * max(q - 1 / 32, 0)):max(int(n * min(q + 1 / 32, 1)), int(n * max(q - 1 / 32, 0)) + 1)]
            c = pal[pid][w].mean(0)
            cols.append(np.clip(lin(np.clip(c * RAMP_GAIN, 0, 1)), 0, 1))
        ramps[k].append({'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': [[round(float(v), 6) for v in c] for c in cols]})
        report[f'{region}_{k}'] = [[round(float(v) * 255) for v in srgb(cols[j])] for j in (2, 8, 14)]
    print('NATIVE', region, 'pixels', n, 'texel luminance range', round(float(lo), 4), round(float(hi), 4))
print('RAMPS sRGB stops 2/8/14', json.dumps(report))
# ---------------------------------------------------------------- club
cl = np.asarray(Image.open(T / f'{X}_club_basecolor.png').convert('RGB'), np.float64) / 255
ch, cs, cv = hsv(cl); iron = cs < 0.25
save(np.stack([np.where(iron, 0.7, 0.3), np.where(iron, 0.4, 0.75), np.zeros(cl.shape[:2])], -1), T / f'{X}_club_metal_rough.png')
save(np.dstack([np.full(cl.shape[:2], 0.5), np.full(cl.shape[:2], 0.5), np.ones(cl.shape[:2])]), T / f'{X}_club_normal.png')
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Goblin_A', 'prefix': 'Goblin', 'mask': f'{X}_region_mask.png', 'regions': list(REGION_IDX),
                      'palettes': PALS, 'ramps': ramps},
                     {'base': 'GoblinHead_A', 'prefix': 'GoblinHead', 'mask': f'{X}_head_region_mask.png',
                      'regions': list(REGION_IDX), 'ramps': ramps}]}
(T / f'{X}_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
(T / f'{X}_swatches.json').write_text(json.dumps({'skin_srgb': [round(float(v) * 255) for v in SKIN]}, indent=1) + '\n')
