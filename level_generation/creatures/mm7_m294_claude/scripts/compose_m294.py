#!/usr/bin/env python3
"""Textures, region mask and tier ramps for the Necromancer (palettes 295/296/297; one region from
mm7_m294/variants.json: R the purple garment, native indices 188-232 -> purple / maroon / grey; white hair, pale skin,
the black cape and boots and the gold stay, as in the native). Copied from the Warlock (mm7_m426_claude/scripts/
compose_m426.py). Run after uv_raster.py (UVMap and HeadUV at 1024) and bake_ao_natm.py.
Differences: the HD masters show a COVERED outfit (user decision 2026-10-20, see README): a purple tunic with black
inset panels where the native has cut-outs; only its purple texels are the tier region (the black panels stay black in
every tier). Meshy's purple is very dark (V 0.12-0.24); the ramps, measured from the native pixels, lift it to the
native purple. Skin is NOT repainted (Meshy's pale face and hands match the masters; no patches). Region texels:
garment 1 (tunic, sleeves; hands excluded by hue) and the tunic hem/front flap below the split (piece 0 / 14 of
garment 2), purple hue 250-330, S > 0.2.
Material classes (8-bit, 1K): 1 skin, 2 hair, 6 eye, 8 cloth (tunic, cape, leggings, boots), 9 metal (gold).
Writes textures/m294_*."""
import json, sys, os
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
SKIN = np.array([212, 160, 128]) / 255
SKIN_MIX = 0.8
# per-tier ramp gain (sRGB multiplier on the native colours). The guide's 1.3-1.45x albedo lift made tier A hot
# magenta in the viewer (rendered tunic median sRGB 137,19,141 vs the native frames' 72,0,72; review 2026-10-20);
# the gains are calibrated so the RENDERED median luminance of the tunic (viewer light, hue-masked) matches the native
# frames' median per palette (scripts/tier_match.py)
RAMP_GAIN = {k: float(v) for k, v in zip(('m294_a', 'm294_b', 'm294_c'), os.environ.get('RAMP_GAINS', '0.85,0.8,0.2').split(','))}
PALS = {'m294_a': 295, 'm294_b': 296, 'm294_c': 297}
_V = json.load(open(HERE.parent / 'mm7_m294' / 'variants.json'))['regions']
IDX = {'garment': _V[0]['palette_indices']}
SPEC = {'skin': 0.35, 'hair': 0.3, 'cloth': 0.15, 'gold': 1.0, 'bead': 0.7, 'eye': 0.9, 'collar': 0.6}
ROUGH = {'skin': 0.6, 'hair': 0.55, 'cloth': 0.88, 'gold': 0.32, 'bead': 0.35, 'eye': 0.2, 'collar': 0.45}


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


def repaint_skin(img, m, sigma=6.0):
    L = R.luminance(img)
    num = ndimage.gaussian_filter(np.where(m, L, 0.0), sigma); den = ndimage.gaussian_filter(m.astype(float), sigma)
    Lb = num / np.maximum(den, 1e-4)
    detail = np.clip((L / np.maximum(Lb, 1e-4)) ** 1.15, 0.5, 1.5)
    new = srgb(np.clip(lin(SKIN)[None, :] * detail[m][:, None], 0, 1))
    out = img.copy(); out[m] = img[m] * (1 - SKIN_MIX) + new * SKIN_MIX
    return out


def ao_grade(img, ao, cov, strength=0.4, floor=0.45):
    f = np.clip(1 - strength + strength * np.maximum(ao, floor), 0, 1)
    out = img.copy(); out[cov] = img[cov] * f[cov][:, None]; return out


# ---------------------------------------------------------------- native region colours per tier (indexed bitmaps)
src = json.load(open(HERE.parent / 'mm7_m294' / 'sources.json'))['sources']
frames = [n for n, s in src.items() if s.get('referenced') and n[4] in 'swa']          # standing, walking, attack
pals = {k: np.frombuffer(open(REPO / f'assets_dev/worlds/mm7/textures/pal{p:03d}.act', 'rb').read()[:768], np.uint8)
        .reshape(256, 3).astype(np.float64) / 255 for k, p in PALS.items()}
native = {r: {k: [] for k in PALS} for r in IDX}
for n in frames:
    ix = np.asarray(Image.open(REPO / src[n]['path']))
    assert ix.ndim == 2, n
    for r, ids in IDX.items():
        sel = ix[np.isin(ix, ids)]
        for k in PALS:
            native[r][k].append(pals[k][sel])
for r in IDX:
    for k in PALS:
        X = np.concatenate(native[r][k]); L = R.luminance(X); keep = L > 0.01
        X, L = X[keep], L[keep]; o = np.argsort(L); native[r][k] = X[o]
print('NATIVE pixels', {r: len(native[r]['m294_a']) for r in IDX}, 'frames', len(frames))


def ramps_for(region, texel_lum):
    lo, hi = np.percentile(texel_lum, [2, 98]); srt = np.sort(texel_lum)
    out = {}
    for k in PALS:
        X = native[region][k]; cols = []
        for i in range(16):
            Li = lo + (hi - lo) * i / 15
            q = np.searchsorted(srt, Li) / len(srt)
            c = X[min(len(X) - 1, int(q * (len(X) - 1)))]
            cols.append([round(float(v), 6) for v in np.clip(lin(np.clip(c * RAMP_GAIN[k], 0, 1)), 0, 1)])
        out[k] = {'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols}
    return out


# ---------------------------------------------------------------- body set
M = HERE / 'meshy' / 'retexture_v1'
base = load(M / 'texture_urls_0_base_color.png'); normal = load(M / 'texture_urls_0_normal.png')
rough_m = load(M / 'texture_urls_0_roughness.png', 'L')
Rz = np.load(HERE / 'work' / 'uvraster_UVMap.npz'); gar, pos, pcs = Rz['garment'], Rz['pos'], Rz['piece']; cov = gar >= 0
hue, sat, val = hsv(base)
gold = cov & (hue > 28) & (hue < 65) & (sat > 0.3) & (val > 0.4)
tunic = cov & ((gar == 1) | (gar == 17) | ((gar == 2) & np.isin(pcs, [0, 14])))
purple = tunic & (hue > 250) & (hue < 330) & (sat > 0.2) & ~ndimage.binary_dilation(gold, iterations=1)
purple = ndimage.binary_opening(ndimage.binary_closing(purple, iterations=2), iterations=1) & tunic & ~gold
hair = cov & (gar == 12)
skin = cov & (gar == 1) & ~purple & ~gold & (sat < 0.3) & (val > 0.45)
cloth = cov & ~hair & ~skin & ~gold
g = base.copy()
# the tunic's purple is dark with fine, high-contrast weave noise; the ramp spreads the region's narrow luminance range
# over the whole native shading range, which turned that noise into glitter (review/tiers_v1.png). Within the region
# the luminance detail above a 3-texel blur is kept at DETAIL (shading and folds stay, the speckle goes)
DETAIL = 0.35
Lp = R.luminance(g)
num = ndimage.gaussian_filter(np.where(purple, Lp, 0.0), 3.0); den = ndimage.gaussian_filter(purple.astype(float), 3.0)
Lb = num / np.maximum(den, 1e-4)
fac = np.where(purple, (Lb + DETAIL * (Lp - Lb)) / np.maximum(Lp, 1e-4), 1.0)
g = np.clip(g * fac[..., None], 0, 1)


def gold_grade(img, m):
    h, s_, v = hsv(img)
    h2 = h + ((GOLD_HUE - h + 180) % 360 - 180) * 0.5
    s2 = np.clip(s_ * GOLD_SAT + 0.08, 0, 1); v2 = np.clip(v * GOLD_VAL, 0, 1)
    rgb = np.asarray(Image.fromarray((np.stack([h2 / 360, s2, v2], -1) * 255 + 0.5).astype(np.uint8), 'HSV').convert('RGB'), np.float64) / 255
    out = img.copy(); out[m] = rgb[m]; return out


GOLD_HUE, GOLD_SAT, GOLD_VAL = 42.0, 1.25, 1.0
g = gold_grade(g, gold)
g = ao_grade(g, load(HERE / 'work' / 'ao_UVMap.png', 'L'), cov)
cls = np.zeros((N, N), np.uint8); spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8)
for name, m, c in (('skin', skin, 1), ('hair', hair, 2), ('cloth', cloth, 8), ('gold', gold, 9)):
    cls[m] = c; spec[m] = SPEC[name]; rgh[m] = np.clip(ROUGH[name] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
print('CLASSES body texels', {n: int(m.sum()) for n, m in (('purple', purple), ('cloth', cloth), ('hair', hair), ('skin', skin), ('gold', gold), ('covered', cov))})
save(pad(g, cov), T / 'm294_basecolor_1k.png'); save(pad(normal, cov), T / 'm294_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'm294_metal_rough_1k.png')
Image.fromarray(cls).save(T / 'm294_material_classes.png')
gr = ramps_for('garment', R.luminance(g[purple]))
R.write_mask([ndimage.gaussian_filter(pad(purple.astype(float), cov), 0.7)], T / 'm294_region_mask.png', size=N)
materials = [{'base': 'M294_A', 'prefix': 'M294', 'mask': 'm294_region_mask.png', 'regions': ['garment'], 'palettes': PALS,
              'ramps': {k: [gr[k]] for k in PALS}}]
# ---------------------------------------------------------------- head set (face, hair; no tier region)
HM = HERE / 'meshy' / 'head_retexture_v1'
if (HM / 'texture_urls_0_base_color.png').exists():
    hb = load(HM / 'texture_urls_0_base_color.png'); hn = load(HM / 'texture_urls_0_normal.png')
    Rh = np.load(HERE / 'work' / 'uvraster_HeadUV.npz'); hg_ = Rh['garment']; hcov = hg_ >= 0
    hh, hs, hv = hsv(hb)
    eye = hcov & (hg_ == 4)
    hgold = hcov & (hg_ == 3) & (hh > 25) & (hh < 70) & (hs > 0.3)
    hhair = hcov & (hg_ == 0) & (hs < 0.1) & (hv > 0.72)
    hskin = hcov & (np.isin(hg_, [0, 5])) & ~hhair
    hao = load(HERE / 'work' / 'ao_HeadUV.png', 'L')
    hgr = ao_grade(gold_grade(hb, hgold), hao, hcov, strength=0.4)
    print('CLASSES head texels', {'skin': int(hskin.sum()), 'hair': int(hhair.sum()), 'eye': int(eye.sum()), 'covered': int(hcov.sum())})
    hspec = np.where(hskin, SPEC['skin'], 0.3); hspec[eye] = SPEC['eye']; hspec[hgold] = SPEC['gold']
    hrgh = np.where(hskin, ROUGH['skin'], 0.55); hrgh[eye] = ROUGH['eye']; hrgh[hgold] = ROUGH['gold']
    save(pad(hgr, hcov), T / 'm294_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'm294_head_normal_1k.png')
    save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm294_head_metal_rough_1k.png')
    hc = np.zeros((N, N), np.uint8); hc[hcov] = 11; hc[hskin] = 1; hc[eye] = 6; hc[hhair] = 2; hc[hgold] = 9
    Image.fromarray(hc).save(T / 'm294_head_material_classes.png')
(T / 'm294_ramps.json').write_text(json.dumps({'variants': list(PALS), 'materials': materials}, indent=1) + '\n')
for k in PALS:
    print('RAMP', k, 'garment mid', [round(x, 3) for x in gr[k]['colors'][8]])
