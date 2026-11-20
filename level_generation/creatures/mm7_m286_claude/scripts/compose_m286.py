#!/usr/bin/env python3
"""Textures, region mask and tier ramps for the m286 minotaur (after mm7_m190_claude/scripts/compose_m190.py;
CLAUDE_CREATURE_TEXTURES.md). Run after transfer_uv.py, uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py.
Tiers recolour one region, as the native palettes do (entries 191-245 change between 287/288/289): R = the green fur
loincloth (fused into the body shell P00) and the green wrist bands P05/P06. Skin, fur legs, mane, hooves, gold, the
belt's blue beads, the silver spikes, horns and eyes stay. Tier A Minotaur = palette 287 (olive green, the HD masters'
colours), B Minotaur Headsman = 288 (teal), C Minotaur Lord = 289 (red) - from the m287/m288/m289 sprite frame tables.
The head set (bull head, ears, jaw, horns, eyes, nose ring, crown tuft) has no recolour region and keeps Meshy's colour.
- Skin: the grey-brown hide of the torso, arms and hands (body shell above the belt, not the painted mane on the back):
  one albedo (the median of the classified Meshy skin) times Meshy's fine shading, mixed SKIN_MIX over Meshy's colour.
- Base colour graded by the rest-pose AO; ORM red = per-class specular (openyamm_specular_mask), green = roughness,
  blue = 0.
- Ramps: each tier palette's colours of the region's native pixels (pixel-weighted, saturated ones), sorted by
  luminance and sampled at 16 quantiles, x RAMP_GAIN, over the region texels' 2nd-98th luminance percentile.
- The axe keeps its own texture (make_axe.py, 512 x 1024); ORM from its colour (polished copper-steel vs the haft).
Writes textures/m286_*."""
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
SKIN_MIX, RAMP_GAIN = 0.85, float(__import__('os').environ.get('RAMP_GAIN', '1.2'))   # v2: 1.35 read lighter than the native (user review)
PALS = {'m286_a': 287, 'm286_b': 288, 'm286_c': 289}
REGION_IDX = {'cloth': (191, 246)}
BELT_Z = 1.0                                                    # v2 rest belt height
GAR = {int(k): v for k, v in json.loads((HERE / 'work' / 'garments.json').read_text()).items()}   # weights_fix.py labels
MANE = [p for p, g in GAR.items() if g == 7]                      # v2: mane sheet + cards on the neck and back
CROWN = [p for p, g in GAR.items() if g == 1 and p not in (3, 7, 8, 9, 10, 11, 14, 19, 20)]   # crown cards
BEADS = [13] + [p for p, g in GAR.items() if g == 4]; SPIKES = [p for p, g in GAR.items() if g == 8]   # v2: buckle P13
SPEC = {'skin': 0.45, 'cloth': 0.25, 'metal': 0.7, 'gold': 0.8, 'leather': 0.35, 'hair': 0.35, 'horn': 0.5, 'eye': 0.9}
ROUGH = {'skin': 0.55, 'cloth': 0.8, 'metal': 0.35, 'gold': 0.3, 'leather': 0.6, 'hair': 0.6, 'horn': 0.45, 'eye': 0.2}
CLASS_ID = {'skin': 1, 'hair': 2, 'cloth': 8, 'metal': 9, 'gold': 9, 'leather': 8, 'horn': 10, 'eye': 6}


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


# v2c (user review 2026-10-21: "muscles need to stand out more"): v2 kept only the shading above a 6 px blur, which
# stripped Meshy's muscle-scale shading (torso band energy 0.184 -> 0.059; HD master 0.231, native x2 0.277). The
# detail is now taken relative to a SKIN_SIGMA px blur (pecs, abs, serratus, deltoids and arm muscles survive) with a
# contrast exponent SKIN_GAMMA; the hue stays the single albedo (Meshy's colour patches do not come back).
SKIN_SIGMA = float(__import__('os').environ.get('SKIN_SIGMA', '3'))
SKIN_GAMMA = float(__import__('os').environ.get('SKIN_GAMMA', '1.1'))
AO_STRENGTH = float(__import__('os').environ.get('AO_STRENGTH', '0.55'))
CAV_GAIN = float(__import__('os').environ.get('CAV_GAIN', '0.6'))   # v2c: geometry convexity (cavity_bake.py)
SKIN_CLIP = tuple(float(x) for x in __import__('os').environ.get('SKIN_CLIP', '0.6,1.6').split(','))


def repaint_skin(img, m, albedo, sigma=None):
    sigma = SKIN_SIGMA if sigma is None else sigma
    L = R.luminance(lin(img))           # v2c: the ratio is applied to a linear albedo, so measure it on linear luminance
    num = ndimage.gaussian_filter(np.where(m, L, 0.0), sigma); den = ndimage.gaussian_filter(m.astype(float), sigma)
    Lb = num / np.maximum(den, 1e-4)
    detail = np.clip((L / np.maximum(Lb, 1e-4)) ** SKIN_GAMMA, *SKIN_CLIP)   # linear ratio (v2: 0.5..1.5 on sRGB)
    new = srgb(np.clip(lin(albedo)[None, :] * detail[m][:, None], 0, 1))
    out = img.copy(); out[m] = img[m] * (1 - SKIN_MIX) + new * SKIN_MIX
    return out


def ao_grade(img, ao, cov, strength=None, floor=0.45):
    strength = AO_STRENGTH if strength is None else strength                # v2c: 0.4 -> 0.55
    f = np.clip(1 - strength + strength * np.maximum(ao, floor), 0, 1)
    out = img.copy(); out[cov] = img[cov] * f[cov][:, None]; return out


SKULL = 1.807                                                   # v2 rest skull top (step1_clean.py)


def classify(base, cov, piece, pos, head=False):
    hue, sat, val = hsv(base)
    z, y = pos[..., 2], pos[..., 1]
    green = (hue > 60) & (hue < 170) & (sat > 0.2) & (val > 0.08)
    if head:
        eye = cov & np.isin(piece, [10, 11])                          # v2 eyes P10/P11
        gold = cov & (piece == 3)                                     # nose ring P03
        # v2: the horns are fused into the body shell (the weights_fix.py rule: skin above the skull's sides)
        x, zz = pos[..., 0], pos[..., 2]
        horn = cov & (piece == 0) & ((((zz > SKULL - 0.10) & (np.abs(x) > 0.125)) | (zz > SKULL + 0.025)))
        hair = cov & (np.isin(piece, CROWN + [9, 19, 20] + MANE))      # crown cards, forelock, brow tufts
        skin = cov & ~(eye | gold | horn | hair)
        none = np.zeros_like(cov)
        return {'skin': skin, 'cloth': none, 'metal': none, 'gold': gold, 'leather': none, 'hair': hair, 'horn': horn,
                'eye': eye}
    # v2: kilt P01 + front flap P12 (whole shells, any hue: the ramp replaces it), green band padding P04/P05
    cloth = cov & (np.isin(piece, [1, 12]) | (np.isin(piece, [4, 5]) & green))
    gold = cov & ~cloth & np.isin(piece, [4, 5, 6] + BEADS) & (((hue > 30) & (hue < 62) & (sat > 0.35) & (val > 0.35)) |
                                                              ((hue > 190) & (hue < 270) & (sat > 0.3)))   # + blue beads
    metal = cov & ~cloth & (np.isin(piece, SPIKES) | (np.isin(piece, [4, 5]) & (sat < 0.25) & (val > 0.45)))
    leather = cov & ~(cloth | gold | metal) & np.isin(piece, [4, 5, 6] + BEADS)
    body = cov & np.isin(piece, [0] + MANE) & ~cloth
    horn = body & (z < 0.16) & (val < 0.3)                            # black hooves
    mane = body & ((np.isin(piece, MANE)) | ((z > BELT_Z + 0.1) & (y > 0.02) & (sat > 0.5) & (hue > 8) & (hue < 40)))
    fur = body & ~horn & (z < BELT_Z)
    # v2c: every body-shell texel above the belt that is not mane/hoof is skin (the hue window left grey-yellow Meshy
    # patches unrepainted: hard-edged light blotches on the chest and shoulders)
    skin = body & ~(horn | mane | fur) & ~np.isin(piece, MANE) & (val > 0.05)
    hair = (mane | fur | (body & ~(horn | skin)))
    eye = np.zeros_like(cov)
    return {'skin': skin, 'cloth': cloth, 'metal': metal, 'gold': gold, 'leather': leather, 'hair': hair, 'horn': horn,
            'eye': eye}


# ---------------------------------------------------------------- body set
M = HERE / 'meshy' / 'body_retexture_v2'
base = load(M / 'texture_urls_0_base_color.png'); normal = load(M / 'texture_urls_0_normal.png')
rough_m = load(M / 'texture_urls_0_roughness.png', 'L')
Rz = np.load(HERE / 'work' / 'uvraster_UVMap.npz'); piece, pos = Rz['piece'], Rz['pos']; cov = piece >= 0
C = classify(base, cov, piece, pos)
# ---------------------------------------------------------------- head set
HM = HERE / 'meshy' / 'head_retexture_v2'
hb = load(HM / 'texture_urls_0_base_color.png'); hn = load(HM / 'texture_urls_0_normal.png')
hr_m = load(HM / 'texture_urls_0_roughness.png', 'L')
Rh = np.load(HERE / 'work' / 'uvraster_HeadUV.npz'); hpiece, hpos = Rh['piece'], Rh['pos']; hcov = hpiece >= 0
HC = classify(hb, hcov, hpiece, hpos, head=True)
SKIN = np.median(base[C['skin']], 0)                              # albedo from the skin-coloured texels
print('SKIN albedo sRGB', np.round(SKIN * 255).tolist())
# v2c: Meshy's mid-scale luminance is patchy paint, not muscle shading (a 40 px detail scale brought back dark blotches);
# the muscle definition comes from the mesh instead: skin albedo x (1 + CAV_GAIN * convexity), body and head sets alike
def cavity(img, m, layer):
    cv = np.load(HERE / 'work' / f'cavity_{layer}.npy')
    out = img.copy(); out[m] = np.clip(img[m] * np.clip(1 + CAV_GAIN * cv[m], 0.45, 1.45)[:, None], 0, 1); return out


# v2c: the HD masters' muscle shading projected onto the skin (hd_shading_bake.py: log ratio of muscle-scale luminance
# from the four views); the main source of the pecs / six-pack / serratus / arm definition
HD_GAIN = float(__import__('os').environ.get('HD_GAIN', '0.8'))


def hdshade(img, m, layer):
    hv = np.load(HERE / 'work' / f'hdshade_{layer}.npy')
    out = img.copy(); out[m] = np.clip(img[m] * np.clip(np.exp(HD_GAIN * hv[m]), 0.35, 1.6)[:, None], 0, 1); return out


g = ao_grade(hdshade(cavity(repaint_skin(base, C['skin'], SKIN), C['skin'], 'UVMap'), C['skin'], 'UVMap'),
             load(HERE / 'work' / 'ao_UVMap.png', 'L'), cov)
# v2c: the level neck cut put the trapezius tops and upper-chest edges in the head set; their skin (dominant bone not
# B_Head) takes the body repaint too, blended over ~3 texels, so no grey Meshy-head patches border the body skin
hbn = list(Rh['bone_names']); hbone = Rh['bone']
nonhead = HC['skin'] & (hbone != hbn.index('B_Head'))
soft = np.clip(ndimage.gaussian_filter(nonhead.astype(float), 3.0), 0, 1) * HC['skin']
hrep = repaint_skin(hb, nonhead, SKIN)
hb2 = hb * (1 - soft[..., None]) + hrep * soft[..., None]
print('HEADSET non-head skin texels repainted', int(nonhead.sum()))
hg = ao_grade(hdshade(cavity(hb2, HC['skin'], 'HeadUV'), nonhead, 'HeadUV'), load(HERE / 'work' / 'ao_HeadUV.png', 'L'), hcov)
print('CLASSES body', {k: int(m.sum()) for k, m in C.items()}, 'covered', int(cov.sum()))
print('CLASSES head', {k: int(m.sum()) for k, m in HC.items()}, 'covered', int(hcov.sum()))
def maps(img, nrm, rgh_m, cls, cov_, extra=None):
    spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8); cm = np.zeros((N, N), np.uint8)
    for k, m in cls.items():
        if not m.any():
            continue
        cm[m] = CLASS_ID[k]; spec[m] = SPEC[k]
        rgh[m] = np.clip(ROUGH[k] + (rgh_m[m] - np.median(rgh_m[m])) * 0.5, 0.1, 1)
    return spec, rgh, cm


spec, rgh, cm = maps(g, normal, rough_m, C, cov)
gb = pad(g, cov); covs = cov
save(gb, T / 'm286_basecolor_1k.png'); save(pad(normal, cov), T / 'm286_normal_1k.png')
save(np.stack([pad(spec, covs), pad(rgh, covs), np.zeros((N, N))], -1), T / 'm286_metal_rough_1k.png')
Image.fromarray(cm).save(T / 'm286_material_classes.png')
hspec, hrgh, hcm = maps(hg, hn, hr_m, HC, hcov)
save(pad(hg, hcov), T / 'm286_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'm286_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm286_head_metal_rough_1k.png')
Image.fromarray(hcm).save(T / 'm286_head_material_classes.png')
# mask (padded like the colour, then blurred)
def soft(m, c):
    return np.clip(ndimage.gaussian_filter(pad(m.astype(float), c), 0.7), 0, 1)


body_r = soft(C['cloth'], cov)
R.write_mask([body_r], T / 'm286_region_mask.png', size=N)
# ---------------------------------------------------------------- ramps (rank-matched to the native sprite pixels)
# The indexed native bitmaps: a region's pixels are those whose palette index lies in its range (hair: only in the top
# HAIR_TOP of the figure, as the range also holds greys used elsewhere). Ordered by their tier-B (216) luminance, the
# 16 stops take each tier's palette colour at the matching ranks (mean over a small window), so one texel luminance
# maps to the same native pixel in every tier.
INV = json.loads((HERE / 'references_native' / 'inventory.json').read_text())
pal = {k: np.frombuffer((REPO / INV['palette_sources'][str(p)]['path']).read_bytes()[:768], np.uint8).reshape(256, 3) / 255
       for k, p in PALS.items()}
FRAMES = [f'm286sa{v}' for v in range(5)] + [f'm286w{c}{v}' for c in 'aceg' for v in (0, 2, 4)] + [f'm286a{c}0' for c in 'acef']
HAIR_TOP = 0.13
pix = {'cloth': []}
for fr in FRAMES:
    idx = np.array(Image.open(REPO / INV['sources'][fr]['path']))
    rows = np.where((idx != 0).any(1))[0]; top, h = rows.min(), rows.max() - rows.min()
    yy = np.arange(idx.shape[0])[:, None] + np.zeros_like(idx)
    for region, (a, b) in REGION_IDX.items():
        m = (idx >= a) & (idx < b)
        if region == 'hair':
            m &= yy < top + HAIR_TOP * h
        # only entries that really recolour between the tiers (shared greys: fletchings, piping)
        chg = (np.abs(pal['m286_a'] - pal['m286_b']).max(1) > 0.03) | (np.abs(pal['m286_c'] - pal['m286_b']).max(1) > 0.03)
        m &= chg[idx]
        pix[region].append(idx[m])
lum = {'cloth': R.luminance(g[C['cloth']])}
ramps = {k: [] for k in PALS}
report = {}
for region in ('cloth',):
    lo, hi = np.percentile(lum[region], [2, 98])
    # m286: pixel-weighted. Each tier's colours of the region's native pixels (with their counts; saturated ones), sorted
    # by that tier's luminance, sampled at 16 quantiles between 6 % and 97 %: the entry-list rule let a few rare
    # highlight entries set the top stops (tier C's top stop came out yellow).
    allpix = np.concatenate(pix[region]); used = sorted(set(allpix.tolist())); n = len(used)
    for k in PALS:
        X = pal[k][allpix]
        mx, mn = X.max(1), X.min(1); sat = (mx - mn) / np.maximum(mx, 1e-6)
        X = X[sat > 0.25]; X = X[np.argsort(R.luminance(X))]
        # v2: hue-preserving gain (v1 clipped each sRGB channel at 1, which turned tier A's top stops yellow)
        def gain(c):
            c = c * RAMP_GAIN
            return c / max(1.0, float(c.max()))
        cols = [np.clip(lin(gain(X[int((0.06 + 0.91 * i / 15) * (len(X) - 1))])), 0, 1) for i in range(16)]
        ramps[k].append({'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': [[round(float(v), 6) for v in c] for c in cols]})
        report[f'{region}_{k}'] = [[round(float(v) * 255) for v in srgb(cols[j])] for j in (2, 8, 14)]
    print('NATIVE', region, 'palette entries used', n)
print('RAMPS sRGB stops 2/8/14', report)
# ---------------------------------------------------------------- props (the axe's base colour from make_axe.py)
ax = np.asarray(Image.open(T / 'm286_axe_basecolor.png').convert('RGB'), np.float64) / 255
ah, as_, av = hsv(ax)
steel = (as_ < 0.2) & (av > 0.3); goldp = (ah > 30) & (ah < 62) & (as_ > 0.4) & (av > 0.4)
asp = np.where(steel, 0.75, np.where(goldp, 0.8, 0.3)); arg = np.where(steel, 0.35, np.where(goldp, 0.3, 0.7))
save(np.stack([asp, arg, np.zeros(ax.shape[:2])], -1), T / 'm286_axe_metal_rough.png')
save(np.dstack([np.full(ax.shape[:2], 0.5), np.full(ax.shape[:2], 0.5), np.ones(ax.shape[:2])]), T / 'm286_axe_normal.png')
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Minotaur_A', 'prefix': 'Minotaur', 'mask': 'm286_region_mask.png', 'regions': ['cloth'],
                      'palettes': PALS, 'ramps': ramps}]}
(T / 'm286_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
(T / 'm286_swatches.json').write_text(json.dumps({'skin_srgb': [round(float(v) * 255) for v in SKIN]}, indent=1) + '\n')

