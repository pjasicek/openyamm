#!/usr/bin/env python3
"""Textures, region masks and tier ramps for the m254 golem (after mm7_m414_claude/scripts/compose_m414.py;
CLAUDE_CREATURE_TEXTURES.md). Run after transfer_uv.py, uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py.

Tiers (native sprite frame tables m255/m256/m257, mm7_m254/manifest.json): A Bronze Golem = palette 255 (green
stripes: the HD masters' colours), B Brass Golem = 256, C Gold Golem = 257. The palettes recolour only the striped cloth
(nemes, crown, false beard, loincloth, belt) and in TWO families whose brightness order flips between the tiers:
  R = the dark-green stripes (entries 151-198): A dark green, B light cyan, C tan;
  G = the light-green stripes (entries 212-250): A green, B blue, C red.
The gold-bronze metal body, the gold trims and studs, the black collar and cuffs, the ivory horns stay.
- Gold (the cast body skin, trims, studs, ear studs): one albedo from the native gold pixels (mean of the pixels below
  the 90 % luminance quantile, the top tenth being baked highlight; linear luminance x GOLD_GAIN), times Meshy's fine
  shading, mixed SKIN_MIX over Meshy's colour; both sets share it.
- Stripes: the green cloth texels split into dark and light by their luminance against the masked local mean
  (sigma 7 texels), soft; padded like the colour, then blurred 0.7.
- Base colour graded by the rest-pose AO; ORM red = per-class specular (openyamm_specular_mask), green = roughness,
  blue = 0 (metallic factor 0 at runtime).
- Ramps: each tier's colours of the family's native pixels (with repetition), sorted by luminance and rank-matched to the
  region texels (m410 rule), x RAMP_GAIN (body and head pooled).
Writes textures/m254_*."""
import json, sys, glob
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
SKIN_MIX, RAMP_GAIN, GOLD_GAIN = 0.85, 1.1, 1.4   # cloth gain 1.35 came out pastel next to the native
# the dark family's texels sit low in their range (Meshy painted the dark stripes near black): 1.1 left the B cyan and
# C tan stripes darker than the native (mean sRGB 30,77,75 vs 28,99,94)
RAMP_GAIN_REGION = {'dark': 1.3, 'light': 1.0}
PALS = {'m254_a': 255, 'm254_b': 256, 'm254_c': 257}
REGION_IDX = {'dark': (151, 199), 'light': (212, 251)}
SPEC = {'gold': 0.8, 'dark': 0.5, 'cloth': 0.1, 'ivory': 0.35, 'eye': 0.8}
ROUGH = {'gold': 0.3, 'dark': 0.45, 'cloth': 0.85, 'ivory': 0.4, 'eye': 0.3}
CLASS_ID = {'gold': 9, 'dark': 9, 'cloth': 8, 'ivory': 4, 'eye': 6}
CLOTH_P = [1, 3, 4, 5, 6]                  # loincloth, crown, nemes, belt, beard
DARK_P = [2, 9, 10, 11, 12]                # collar, ankle and wrist cuffs
GOLD_P = list(range(17, 41)) + [41, 42, 13, 14]   # collar studs, ear studs, horn sockets
IVORY_P = [7, 8]
EYE_P = [15, 16]


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


def repaint(img, m, albedo, sigma=6.0):
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


def classify(base, cov, piece):
    hue, sat, val = hsv(base)
    goldhue = (hue > 25) & (hue < 65) & (sat > 0.3) & (val > 0.3)
    green = (hue > 85) & (hue < 200) & (sat > 0.18)
    eye = cov & np.isin(piece, EYE_P)
    ivory = cov & np.isin(piece, IVORY_P) & ~(goldhue & (sat > 0.5))      # creamy horns (sat 0.3-0.5) are ivory
    # green painted on the skin or the collar next to the cloth (Meshy spill under the nemes and the loincloth) is cloth
    # too: left out, it stayed green on the B/C tiers
    cloth = cov & ((np.isin(piece, CLOTH_P) & green) | (np.isin(piece, [0, 2]) & green & (sat > 0.25)))
    gold = cov & ~(eye | ivory | cloth) & (np.isin(piece, GOLD_P) | ((piece == 0) & ~(val < 0.28))
                                           | (np.isin(piece, CLOTH_P + DARK_P + IVORY_P) & goldhue))
    dark = cov & ~(eye | ivory | cloth | gold)
    return {'gold': gold, 'dark': dark, 'cloth': cloth, 'ivory': ivory, 'eye': eye}


def stripes(img, cloth):
    """Soft dark-stripe weight inside the cloth: luminance below the masked local mean."""
    L = R.luminance(img)
    num = ndimage.gaussian_filter(np.where(cloth, L, 0.0), 7.0); den = ndimage.gaussian_filter(cloth.astype(float), 7.0)
    Lb = num / np.maximum(den, 1e-4)
    # crisp: the shader mixes the two channels one after the other, so a 0.6/0.4 split left a quarter of the green
    w = np.clip(0.5 + (Lb - L) / np.maximum(0.10 * Lb, 1e-4), 0, 1)
    return np.where(cloth, w, 0.0)


# ---------------------------------------------------------------- native pixels (indexed bitmaps, tier palettes)
pal = {k: np.frombuffer((REPO / 'assets_dev/worlds/mm7/textures' / f'pal{p}.act').read_bytes()[:768], np.uint8).reshape(256, 3) / 255
       for k, p in PALS.items()}
FRAMES = sorted(glob.glob(str(REPO / 'assets_dev/engine/sprites/m254s*.bmp'))) + \
    sorted(glob.glob(str(REPO / 'assets_dev/engine/sprites/m254w[aceg]*.bmp')))
chg = np.zeros(256, bool)
for k in ('m254_b', 'm254_c'):
    chg |= np.abs(pal['m254_a'] - pal[k]).max(1) > 0.03
idx_all = np.concatenate([np.asarray(Image.open(f)).ravel() for f in FRAMES])
idx_all = idx_all[idx_all != 0]
pix = {r: idx_all[(idx_all >= a) & (idx_all < b) & chg[idx_all]] for r, (a, b) in REGION_IDX.items()}
# native gold: non-recolouring, gold-hued pixels of tier A
ga = pal['m254_a'][idx_all[~chg[idx_all]]]
gh, gs, gv = hsv(ga[None])
gsel = (gh[0] > 25) & (gh[0] < 65) & (gs[0] > 0.35) & (gv[0] > 0.15)
gl = R.luminance(ga[gsel]); q90 = np.quantile(gl, 0.9)            # R.luminance takes sRGB (linear luminance out)
gp = ga[gsel][gl <= q90]
GOLD_LUM = float(R.luminance(gp).mean()) * GOLD_GAIN
gmid = gp[(R.luminance(gp) >= np.quantile(R.luminance(gp), 0.7))]      # chroma from the light tones (the dark ones are brown shading)
gcol = lin(np.median(gmid, 0)); gcol = gcol * GOLD_LUM / float(gcol @ np.array([0.2126, 0.7152, 0.0722]))
GOLD = srgb(np.clip(gcol, 0, 1))
print('NATIVE frames', len(FRAMES), 'stripe pixels', {k: len(v) for k, v in pix.items()}, 'gold pixels', int(gsel.sum()),
      'gold albedo sRGB', np.round(GOLD * 255).tolist(), 'linear luminance', round(GOLD_LUM, 4))
# ---------------------------------------------------------------- body and head sets
M = HERE / 'meshy' / 'retexture_v1'; HM = HERE / 'meshy' / 'head_retexture_v1'
sets = {}
for tag, job, layer in (('body', M, 'UVMap'), ('head', HM, 'HeadUV')):
    base = load(job / 'texture_urls_0_base_color.png'); normal = load(job / 'texture_urls_0_normal.png')
    rough_m = load(job / 'texture_urls_0_roughness.png', 'L')
    Rz = np.load(HERE / 'work' / f'uvraster_{layer}.npz'); piece = Rz['piece']; cov = piece >= 0
    C = classify(base, cov, piece)
    g = repaint(base, C['gold'], GOLD)
    g = ao_grade(g, load(HERE / 'work' / f'ao_{layer}.png', 'L'), cov)
    wd = stripes(g, C['cloth'])
    sets[tag] = dict(base=base, normal=normal, rough=rough_m, cov=cov, C=C, g=g, wd=wd)
    print('CLASSES', tag, {k: int(m.sum()) for k, m in C.items()}, 'covered', int(cov.sum()),
          'dark/light stripe texels', int((wd > 0.5).sum()), int((C['cloth'] & (wd <= 0.5)).sum()))


def maps(rgh_m, cls):
    spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8); cm = np.zeros((N, N), np.uint8)
    for k, m in cls.items():
        if not m.any():
            continue
        cm[m] = CLASS_ID[k]; spec[m] = SPEC[k]
        rgh[m] = np.clip(ROUGH[k] + (rgh_m[m] - np.median(rgh_m[m])) * 0.5, 0.1, 1)
    return spec, rgh, cm


def soft(m, c):
    return np.clip(ndimage.gaussian_filter(pad(m.astype(float), c), 0.7), 0, 1)


for tag, pre in (('body', 'm254'), ('head', 'm254_head')):
    S = sets[tag]; cov = S['cov']
    spec, rgh, cm = maps(S['rough'], S['C'])
    save(pad(S['g'], cov), T / f'{pre}_basecolor_1k.png'); save(pad(S['normal'], cov), T / f'{pre}_normal_1k.png')
    save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / f'{pre}_metal_rough_1k.png')
    Image.fromarray(cm).save(T / f'{pre}_material_classes.png')
    cl = S['C']['cloth'].astype(float)
    R.write_mask([soft(cl * S['wd'], cov), soft(cl * (1 - S['wd']), cov)], T / f'{pre}_region_mask.png', size=N)
# ---------------------------------------------------------------- ramps (rank-matched to the native sprite pixels)
ramps = {k: [] for k in PALS}; report = {}
for ri, region in enumerate(('dark', 'light')):
    lums = []
    for S in sets.values():
        w = S['wd'] if region == 'dark' else 1 - S['wd']
        sel = S['C']['cloth'] & (w > 0.5)
        lums.append(R.luminance(S['g'][sel]))
    lum = np.concatenate(lums)
    lo, hi = np.percentile(lum, [2, 98])
    tt = np.clip((lum - lo) / (hi - lo), 0, 1)
    # the native's top tenth is baked highlight (pale, desaturated): stops read at most the 85 % quantile
    qs = [float(np.clip((tt <= i / 15).mean(), 0.02, 0.85)) for i in range(16)]
    used = pix[region]
    for k in PALS:
        X = pal[k][used]; X = X[np.argsort(R.luminance(X))]
        gain = RAMP_GAIN_REGION.get(region, RAMP_GAIN)
        cols = [np.clip(lin(np.clip(X[int(round(qs[i] * (len(X) - 1)))] * gain, 0, 1)), 0, 1) for i in range(16)]
        ramps[k].append({'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': [[round(float(v), 6) for v in c] for c in cols]})
        report[f'{region}_{k}'] = [[round(float(v) * 255) for v in srgb(cols[j])] for j in (2, 8, 14)]
    print('NATIVE', region, 'pixels', len(used), 'texel luminance range', round(float(lo), 4), round(float(hi), 4))
print('RAMPS sRGB stops 2/8/14', report)
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Golem_A', 'prefix': 'Golem', 'mask': 'm254_region_mask.png', 'regions': ['dark_stripe', 'light_stripe'],
                      'palettes': PALS, 'ramps': ramps},
                     {'base': 'GolemHead_A', 'prefix': 'GolemHead', 'mask': 'm254_head_region_mask.png',
                      'regions': ['dark_stripe', 'light_stripe'], 'palettes': PALS, 'ramps': ramps}]}
(T / 'm254_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
(T / 'm254_swatches.json').write_text(json.dumps({'gold_srgb': [round(float(v) * 255) for v in GOLD]}, indent=1) + '\n')
