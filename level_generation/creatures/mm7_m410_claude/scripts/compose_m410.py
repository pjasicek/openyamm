#!/usr/bin/env python3
"""Textures, region masks and tier ramps for the m410 thief (after mm7_m190_claude/scripts/compose_m190.py;
CLAUDE_CREATURE_TEXTURES.md). Run after transfer_uv.py, uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py.
Tiers recolour two regions, as the native ACT transforms do: R = the vest, its shoulder caps and the cap (palette
entries 147-245), G = the trousers (entries 81-137). Skin, the red mask, leather, gold, studs and the pouch stay.
Tier A Thief = palette 84 (purple vest, green trousers: the HD masters' colours), B Rogue = 85 (green, brown-orange),
C Master Thief = 86 (red, dark red) - from the 7m411/m412/7m413 sprite frame tables. The head set holds the cap, so it
has a region mask too, with the body's ramps (tools/merge_head_material.py needs them equal).
- Skin (body: arms and hands of the torso shell; head: the face): one albedo (the median of the classified Meshy skin of
  both sets, so the neck matches) times Meshy's fine shading, mixed SKIN_MIX over Meshy's colour.
- Shading patches that follow the UV islands evened out in 3D (smooth3d: vest, trousers; user review); the bare
  arms and hands are forced to skin by bone (Meshy's highlights read as gold/metal) and painted flat.
- Base colour graded by the rest-pose AO (averaged over the 3D surface first, ao_smooth3d); ORM red = per-class specular (openyamm_specular_mask), green = roughness,
  blue = 0.
- Ramps: each tier's colours of the region's native pixels (with repetition), sorted by luminance and rank-matched to
  the region texels (stop i at t = i/15 of the texels' 2nd-98th linear-luminance range takes the native colour at the
  share of texels below it), x RAMP_GAIN (body and head pooled).
- The dagger keeps its own texture (make_dagger.py, 128 x 512); ORM from its colour (steel vs leather).
Writes textures/m410_*."""
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
import os
SKIN_MIX, RAMP_GAIN = 0.85, 1.35
# body skin (arms, hands): no Meshy shading at all (user review 2026-10-20: its strokes and the UV-space blurs of the
# fragmented atlas showed the arm's islands as angular light/dark patches); the face keeps Meshy's detail (lips, brows)
BODY_SKIN_MIX, BODY_SKIN_DETAIL, HEAD_SKIN_DETAIL = 1.0, 0.0, 1.15
PALS = {'m410_a': 84, 'm410_b': 85, 'm410_c': 86}
REGION_IDX = {'vest': (147, 246), 'trousers': (81, 138)}
SPEC = {'skin': 0.45, 'vest': 0.3, 'trousers': 0.35, 'cloth': 0.2, 'metal': 0.7, 'gold': 0.8, 'leather': 0.35, 'eye': 0.9}
ROUGH = {'skin': 0.55, 'vest': 0.65, 'trousers': 0.6, 'cloth': 0.85, 'metal': 0.35, 'gold': 0.3, 'leather': 0.6, 'eye': 0.2}
CLASS_ID = {'skin': 1, 'vest': 8, 'trousers': 8, 'cloth': 8, 'metal': 9, 'gold': 9, 'leather': 8, 'eye': 6}


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


def repaint_skin(img, m, albedo, sigma=6.0, exponent=HEAD_SKIN_DETAIL, mix=SKIN_MIX):
    L = R.luminance(img)
    num = ndimage.gaussian_filter(np.where(m, L, 0.0), sigma); den = ndimage.gaussian_filter(m.astype(float), sigma)
    Lb = num / np.maximum(den, 1e-4)
    detail = np.clip((L / np.maximum(Lb, 1e-4)) ** exponent, 0.5, 1.5)
    new = srgb(np.clip(lin(albedo)[None, :] * detail[m][:, None], 0, 1))
    out = img.copy(); out[m] = img[m] * (1 - mix) + new * mix
    return out


def ao_grade(img, ao, cov, strength=0.4, floor=0.45):
    f = np.clip(1 - strength + strength * np.maximum(ao, floor), 0, 1)
    out = img.copy(); out[cov] = img[cov] * f[cov][:, None]; return out


def smooth3d(img, pos, masks, sigma_small=0.006, sigma_3d=0.025, k=32, nref=60000, seed=0):
    """Even out shading patches that follow the UV islands (user review 2026-10-20: angular light and dark patches on
    the trousers; Meshy paints each island's shading on its own, so neighbouring islands disagree). Per mask, the local
    luminance (3D Gaussian over sigma_small: a UV-space blur reached into unrelated islands packed beside each other) is
    replaced by its 3D average over sigma_3d, keeping the detail below sigma_small."""
    from scipy.spatial import cKDTree
    out = img.copy(); rng = np.random.default_rng(seed); L = R.luminance(img).ravel(); P = pos.reshape(-1, 3)
    for m in masks:
        if m.sum() < 100:
            continue
        idx = np.flatnonzero(m); tree = cKDTree(P[idx])
        d, j = tree.query(P[idx], k=k); w = np.exp(-0.5 * (d / sigma_small) ** 2)
        Ls = (w * L[idx][j]).sum(1) / np.maximum(w.sum(1), 1e-9)
        ref = rng.choice(idx.size, min(nref, idx.size), replace=False); t2 = cKDTree(P[idx][ref])
        d, j = t2.query(P[idx], k=k); w = np.exp(-0.5 * (d / sigma_3d) ** 2)
        L3 = (w * Ls[ref][j]).sum(1) / np.maximum(w.sum(1), 1e-9)
        f = np.clip(L3 / np.maximum(Ls, 1e-4), 0.5, 2.0)
        flat = out.reshape(-1, 3); flat[idx] = np.clip(flat[idx] * f[:, None], 0, 1)
        print(f'SMOOTH3D {int(m.sum())} texels: shading factor p5..p95 {np.percentile(f, 5):.2f}..{np.percentile(f, 95):.2f}')
    return out


def ao_smooth3d(ao, pos, cov, sigma=0.015, k=32, nref=80000, seed=1):
    """The rest-pose AO averaged over the rest-pose surface (user review 2026-10-20: the bake on the low-poly mesh has
    per-triangle steps that showed as angular light/dark patches on the bare arms even with a flat skin colour)."""
    from scipy.spatial import cKDTree
    idx = np.flatnonzero(cov); rng = np.random.default_rng(seed); ref = rng.choice(idx, min(nref, idx.size), replace=False)
    P = pos.reshape(-1, 3); d, j = cKDTree(P[ref]).query(P[idx], k=k)
    w = np.exp(-0.5 * (d / sigma) ** 2); A = ao.ravel()[ref]
    out = ao.copy().ravel(); out[idx] = (w * A[j]).sum(1) / np.maximum(w.sum(1), 1e-9)
    return out.reshape(ao.shape)


def classify(base, cov, piece, garment, head=False):
    hue, sat, val = hsv(base)
    gold = cov & (hue > 30) & (hue < 62) & (sat > 0.4) & (val > 0.4) & ~np.isin(piece, [2, 3, 14])
    eye = cov & np.isin(piece, [16, 17])
    metal = cov & ~gold & ~eye & (sat < 0.15) & (val > 0.45) & np.isin(piece, [0, 7, 8, 15])   # studs, buckle
    purple = (hue > 235) & (hue < 330) & (sat > 0.12)
    vest = cov & ~(gold | metal | eye) & (np.isin(piece, [3, 7, 8]) | ((piece == 0) & purple))
    trousers = cov & ~(gold | eye) & (piece == 2)
    skin = cov & ~(gold | metal | eye | vest | trousers) & np.isin(piece, [0, 1]) & ((hue < 40) | (hue > 330)) \
        & (sat > 0.06) & (sat < 0.6) & (val > 0.3)
    cloth = cov & ~(gold | metal | eye | vest | trousers | skin) & np.isin(piece, [6, 14])          # pouch, red mask
    leather = cov & ~(gold | metal | eye | vest | trousers | skin | cloth)
    return {'skin': skin, 'vest': vest, 'trousers': trousers, 'cloth': cloth, 'metal': metal, 'gold': gold,
            'leather': leather, 'eye': eye}


# ---------------------------------------------------------------- body set
M = HERE / 'meshy' / 'body_retexture_v1'
base = load(M / 'texture_urls_0_base_color.png'); normal = load(M / 'texture_urls_0_normal.png')
rough_m = load(M / 'texture_urls_0_roughness.png', 'L')
Rz = np.load(HERE / 'work' / 'uvraster_UVMap.npz'); piece, gar = Rz['piece'], Rz['garment']; cov = piece >= 0
C = classify(base, cov, piece, gar)
# the bare arms and hands are skin wherever the colour test failed (user review 2026-10-20: Meshy's warm highlights read as
# gold and its pale ones as metal, so 18k arm texels kept Meshy's raw paint and a metal/gold shine: angular patches)
ARMB = np.array([any(k in str(n) for k in ('UpperArm', 'Forearm', 'Hand', 'Finger', 'Thumb')) for n in Rz['bone_names']])
hue_, sat_, _ = hsv(base)
armskin = cov & np.isin(piece, [0, 1]) & (Rz['bone'] >= 0) & ARMB[np.clip(Rz['bone'], 0, None)] \
    & ~((hue_ > 235) & (hue_ < 330) & (sat_ > 0.12)) & ~C['eye']
for k in C:
    C[k] = C[k] & ~armskin
C['skin'] = C['skin'] | armskin
print('ARMSKIN texels forced to skin', int(armskin.sum()))
# ---------------------------------------------------------------- head set
HM = HERE / 'meshy' / 'head_retexture_v1'
hb = load(HM / 'texture_urls_0_base_color.png'); hn = load(HM / 'texture_urls_0_normal.png')
hr_m = load(HM / 'texture_urls_0_roughness.png', 'L')
Rh = np.load(HERE / 'work' / 'uvraster_HeadUV.npz'); hpiece, hgar = Rh['piece'], Rh['garment']; hcov = hpiece >= 0
HC = classify(hb, hcov, hpiece, hgar, head=True)
SKIN = np.median(np.concatenate([base[C['skin']], hb[HC['skin']]]), 0)
print('SKIN albedo sRGB', np.round(SKIN * 255).tolist())
g = ao_grade(repaint_skin(base, C['skin'], SKIN, exponent=BODY_SKIN_DETAIL, mix=BODY_SKIN_MIX),
             ao_smooth3d(load(HERE / 'work' / 'ao_UVMap.png', 'L'), Rz['pos'], cov), cov)
g = smooth3d(g, Rz['pos'], [C['trousers'], C['vest']])     # skin is flat x the 3D AO already
hg = ao_grade(repaint_skin(hb, HC['skin'], SKIN), load(HERE / 'work' / 'ao_HeadUV.png', 'L'), hcov)
print('CLASSES body', {k: int(m.sum()) for k, m in C.items()}, 'covered', int(cov.sum()))
print('CLASSES head', {k: int(m.sum()) for k, m in HC.items()}, 'covered', int(hcov.sum()))
def maps(img, nrm, rgh_m, cls, cov_, extra=None):
    spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8); cm = np.zeros((N, N), np.uint8)
    for k, m in cls.items():
        if not m.any():
            continue
        cm[m] = CLASS_ID[k]; spec[m] = SPEC[k]
        # skin and trousers: the class roughness alone (Meshy's roughness varies per UV island, and the highlights then
        # showed the islands as light facets on the bare arms; user review)
        var = 0.0 if k in ('skin', 'trousers') else 0.5
        rgh[m] = np.clip(ROUGH[k] + (rgh_m[m] - np.median(rgh_m[m])) * var, 0.1, 1)
    return spec, rgh, cm


spec, rgh, cm = maps(g, normal, rough_m, C, cov)
gb = pad(g, cov); covs = cov
save(gb, T / 'm410_basecolor_1k.png'); save(pad(normal, cov), T / 'm410_normal_1k.png')
save(np.stack([pad(spec, covs), pad(rgh, covs), np.zeros((N, N))], -1), T / 'm410_metal_rough_1k.png')
Image.fromarray(cm).save(T / 'm410_material_classes.png')
hspec, hrgh, hcm = maps(hg, hn, hr_m, HC, hcov)
save(pad(hg, hcov), T / 'm410_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'm410_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm410_head_metal_rough_1k.png')
Image.fromarray(hcm).save(T / 'm410_head_material_classes.png')
# mask (padded like the colour, then blurred)
def soft(m, c):
    return np.clip(ndimage.gaussian_filter(pad(m.astype(float), c), 0.7), 0, 1)


R.write_mask([soft(C['vest'], cov), soft(C['trousers'], cov)], T / 'm410_region_mask.png', size=N)
R.write_mask([soft(HC['vest'], hcov), np.zeros((N, N))], T / 'm410_head_region_mask.png', size=N)
# ---------------------------------------------------------------- ramps (rank-matched to the native sprite pixels)
# The indexed native bitmaps: a region's pixels are those whose palette index lies in its range and recolours between
# the tiers.
INV = json.loads((HERE / 'references_native' / 'inventory.json').read_text())
pal = {k: np.frombuffer((REPO / INV['palette_sources'][str(p)]['path']).read_bytes()[:768], np.uint8).reshape(256, 3) / 255
       for k, p in PALS.items()}
FRAMES = [f'm410sa{v}' for v in range(5)] + [f'm410w{c}{v}' for c in 'aceg' for v in (0, 2, 4)] + [f'm410a{c}0' for c in 'aceg']
pix = {'vest': [], 'trousers': []}
for fr in FRAMES:
    idx = np.array(Image.open(REPO / INV['sources'][fr]['path']))
    rows = np.where((idx != 0).any(1))[0]; top, h = rows.min(), rows.max() - rows.min()
    yy = np.arange(idx.shape[0])[:, None] + np.zeros_like(idx)
    for region, (a, b) in REGION_IDX.items():
        m = (idx >= a) & (idx < b)
        # only entries that really recolour between the tiers (shared greys: fletchings, piping)
        chg = (np.abs(pal['m410_a'] - pal['m410_b']).max(1) > 0.03) | (np.abs(pal['m410_c'] - pal['m410_b']).max(1) > 0.03)
        m &= chg[idx]
        pix[region].append(idx[m])
lum = {'vest': np.concatenate([R.luminance(g[C['vest']]), R.luminance(hg[HC['vest']])]), 'trousers': R.luminance(g[C['trousers']])}
ramps = {k: [] for k in PALS}
report = {}
for region in ('vest', 'trousers'):
    lo, hi = np.percentile(lum[region], [2, 98])
    # m410: each tier's colours of the region's native PIXELS (with repetition), sorted by luminance, stops at the
    # 2..98 % quantiles: unique palette entries over-weighted the many near-black shade entries (tier A vest came out
    # black)
    # rank-matched: stop i sits at t = i/15 of the texels' linear-luminance range; it takes the native colour at the
    # quantile equal to the share of region texels below that t (dark texels crowd the low t: evenly spaced quantiles
    # turned the trousers black)
    tt = np.clip((lum[region] - lo) / (hi - lo), 0, 1)
    qs = [float(np.clip((tt <= i / 15).mean(), 0.02, 0.98)) for i in range(16)]
    used = np.concatenate(pix[region]); n = len(used)
    for k in PALS:
        X = pal[k][used]; X = X[np.argsort(R.luminance(X))]
        cols = [np.clip(lin(np.clip(X[int(round(qs[i] * (len(X) - 1)))] * RAMP_GAIN, 0, 1)), 0, 1) for i in range(16)]
        ramps[k].append({'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': [[round(float(v), 6) for v in c] for c in cols]})
        report[f'{region}_{k}'] = [[round(float(v) * 255) for v in srgb(cols[j])] for j in (2, 8, 14)]
    print('NATIVE', region, 'pixels', n)
print('RAMPS sRGB stops 2/8/14', report)
# ---------------------------------------------------------------- props (the dagger's base colour from make_dagger.py)
ax = np.asarray(Image.open(T / 'm410_dagger_basecolor.png').convert('RGB'), np.float64) / 255
ah, as_, av = hsv(ax)
steel = (as_ < 0.2) & (av > 0.3)
save(np.stack([np.where(steel, 0.75, 0.3), np.where(steel, 0.35, 0.7), np.zeros(ax.shape[:2])], -1), T / 'm410_dagger_metal_rough.png')
save(np.dstack([np.full(ax.shape[:2], 0.5), np.full(ax.shape[:2], 0.5), np.ones(ax.shape[:2])]), T / 'm410_dagger_normal.png')
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Thief_A', 'prefix': 'Thief', 'mask': 'm410_region_mask.png', 'regions': ['vest', 'trousers'],
                      'palettes': PALS, 'ramps': ramps},
                     {'base': 'ThiefHead_A', 'prefix': 'ThiefHead', 'mask': 'm410_head_region_mask.png', 'regions': ['vest', 'trousers'],
                      'palettes': PALS, 'ramps': ramps}]}
(T / 'm410_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
(T / 'm410_swatches.json').write_text(json.dumps({'skin_srgb': [round(float(v) * 255) for v in SKIN]}, indent=1) + '\n')

