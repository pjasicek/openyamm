#!/usr/bin/env python3
"""Textures, region masks and tier ramps for har, the Hesper Ashrunners (CLAUDE_CREATURE_TEXTURES.md). Run after
uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py.

Three tiers (skins har_a/har_b/har_c: 10070 Scav, 10071 Raider, 10072 Gunner) recolour FOUR regions of one shared
texture set: R = the cloak and hood (ash grey), G = the scarf and the forearm/shin wraps (rust orange), B = the white
Ancient ceramic scrap plates, A = the under-clothes (charcoal-brown tunic, sleeves, trousers). No native palette: A is
fitted to the texture itself (the approved concept's look), B and C keep A's shading (each stop's luminance relative to
the region's median, compressed by SHADE) on the brief's colours (TIERS).
- Classes per texel by piece and colour (uv_raster.py pieces, creature.json garments): eyes (P38/P40), goggles (P10,
  P25, P81: brass, or the dark lens), skin (the face P02 and the bare fingers: skin hue, moderate saturation), wraps
  (rust: saturated red-orange), plate (white texels of the plate pieces and the boots' shin plates), gold edging and
  brass (yellow, saturated), cloak (P01, the hood's grey), under-clothes (tunic P04, trousers P07, the torso's dark
  cloth), leather (brown straps, belt, boots, pack), metal (grey canisters of the belt and pack).
- Skin repainted (natm): one albedo x Meshy's fine shading. AO graded into the base colour; ORM red = per-class
  specular mask (openyamm_specular_mask), green = roughness, blue 0. Masks padded into the gutters.
- Packed body page (2026-10-22 review, uv_pack.py / uv_atlas.py / resample_meshy.py): the body set is BODY_SIZE
  (2048 x 1024, about 382 texels/m) on the packed layout, from Meshy's maps moved onto it (work/meshy_body_packed); the
  head set stays 1K on HeadUV. Env BODY_MESHY (default work/meshy_body_packed; meshy/retexture_v1 with the old
  rasters rebuilds the Meshy-layout 1K set).
Writes textures/har_*. PREVIEW=1 also writes work/classes_body.png / classes_head.png and work/tierprev_*.png."""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
N = 1024
SKIN_MIX = 0.85
REGIONS = ['cloak', 'wraps', 'plate', 'under']
VARIANTS = ['har_a', 'har_b', 'har_c']
TIERS = {   # sRGB median albedo per region for B and C (A comes from the texture); the brief: B charcoal cloak, red-brown
    # wraps, scorched plates; C sand cloak, ochre wraps, sand-stained ivory plates. Polish 2026-10-22: C's wraps were a
    # saturated yellow (200, 136, 44) -> muted ochre (darker, less chroma); B's red-brown browner (was 116, 48, 34)
    'har_b': {'cloak': (54, 53, 56), 'wraps': (104, 54, 40), 'plate': (156, 150, 138), 'under': (44, 40, 38)},
    'har_c': {'cloak': (170, 142, 100), 'wraps': (138, 94, 46), 'plate': (218, 204, 172), 'under': (82, 68, 54)},
}
SHADE = 0.7
SCARF_X, SCARF_F = 0.07, 0.05
SCARF_W = {}   # head raster shape -> the scarf's soft weight
WRAPS_ALBEDO = np.array([150, 66, 32]) / 255   # the body's scarf tail / wraps median (sRGB)
# tier A's cloak: Meshy painted it warm brown-grey (116, 98, 89); the concept's ash grey is cooler
TIER_A = {'cloak': (126, 123, 120)}
PLATE_PIECES = [21, 22, 23, 24, 30, 31, 32, 35, 44, 45]
CLASS = {'skin': 1, 'cloak': 8, 'wraps': 8, 'under': 8, 'leather': 8, 'plate': 11, 'brass': 9, 'metal': 9, 'eye': 6,
         'lens': 11}
SPEC = {'skin': 0.35, 'cloak': 0.15, 'wraps': 0.15, 'under': 0.15, 'leather': 0.35, 'plate': 0.55, 'brass': 0.9,
        'metal': 0.8, 'eye': 0.9, 'lens': 0.9}
ROUGH = {'skin': 0.55, 'cloak': 0.9, 'wraps': 0.88, 'under': 0.88, 'leather': 0.65, 'plate': 0.45, 'brass': 0.35,
         'metal': 0.4, 'eye': 0.2, 'lens': 0.15}
PREVIEW_COL = {'scarf_geo': (255, 60, 0), 'skin': (230, 170, 140), 'cloak': (40, 70, 230), 'wraps': (240, 110, 20), 'plate': (0, 255, 255),
               'under': (110, 140, 110), 'leather': (90, 50, 20), 'brass': (250, 210, 0), 'metal': (160, 160, 160),
               'eye': (255, 0, 255), 'lens': (255, 255, 255)}


def load(path, mode='RGB', shape=(N, N)):
    im = Image.open(path).convert(mode); wh = (shape[1], shape[0])
    return np.asarray(im.resize(wh, Image.LANCZOS) if im.size != wh else im, np.float64) / 255


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


def classify(base, gar, pos, cov, piece, bone, bone_names):
    h, s, v = hsv(base)
    handb = np.isin(bone, [i for i, n in enumerate(bone_names) if 'Hand' in str(n) or 'Finger' in str(n)])
    C = {}
    C['eye'] = cov & np.isin(piece, [38, 40])
    gog = cov & np.isin(piece, [10, 25, 81])
    yellow = (h > 30) & (h < 62) & (s > 0.35) & (v > 0.35)
    rust = ((h < 30) | (h > 345)) & (s > 0.62) & (v > 0.3) & (base[..., 0] - base[..., 1] > 55 / 255)   # not the browns (s 0.4-0.55)
    skinhue = (h < 38) & (s > 0.18) & (s < 0.55) & (v > 0.35)
    brown = (h > 12) & (h < 45) & (s > 0.3) & (v < 0.62)
    white = (s < 0.22) & (v > 0.55)
    C['lens'] = gog & ~yellow & (v < 0.35)
    C['brass'] = (gog & ~C['lens']) | (cov & yellow & ~C['eye'])
    face = cov & (piece == 2)
    C['skin'] = (face & skinhue & ~rust) | (cov & (piece == 0) & handb & skinhue & ~rust)
    # polish 2026-10-22: Meshy painted the goggles' band across the forehead; the goggles are now a mesh on the hood
    # (face_fix.py), so the face piece's forehead (2-10 cm above the eyes, in front) is skin
    if np.isin(piece, (38, 40)).any():
        ez = float(np.median(pos[np.isin(piece, (38, 40))][:, 2])); ey = float(np.median(pos[np.isin(piece, (38, 40))][:, 1]))
        C['skin'] |= face & (pos[..., 2] > ez + 0.02) & (pos[..., 2] < ez + 0.10) & (pos[..., 1] < ey + 0.03)
    taken = C['eye'] | C['lens'] | C['brass'] | C['skin']
    C['wraps'] = cov & rust & ~taken & ~np.isin(piece, PLATE_PIECES)
    # the hood piece (P03) holds the scarf too: Meshy's head paint of the scarf is a duller orange (s 0.35-0.6) than the
    # body's wraps; the hood's grey cloth stays below s 0.25
    C['wraps'] |= cov & (piece == 3) & ~taken & ((h < 35) | (h > 345)) & (s > 0.35) & (base[..., 0] - base[..., 1] > 30 / 255)
    # ... and Meshy painted most of the scarf grey: the hood piece's front below the eyes (nose, mouth, chin and the
    # wrap round the throat) is the scarf by position (repainted rust in build())
    if (piece == 3).any() and np.isin(piece, (38, 40)).any():
        ez = float(np.median(pos[np.isin(piece, (38, 40))][:, 2])); ey = float(np.median(pos[np.isin(piece, (38, 40))][:, 1]))
        # by position: below the eyes, in front, within SCARF_X of the face's centre line, the weight fading out over
        # SCARF_F to the sides (a hard edge showed as a straight seam across the hood's side drape)
        cx_ = float(np.median(pos[piece == 2][:, 0]))
        cand = cov & (piece == 3) & (pos[..., 2] < ez - 0.015) & (pos[..., 2] > ez - 0.24) & (pos[..., 1] < ey + 0.035)
        wx = np.clip((SCARF_X + SCARF_F - np.abs(pos[..., 0] - cx_)) / SCARF_F, 0, 1)
        wz = np.clip((ez - 0.015 - pos[..., 2]) / 0.02, 0, 1)
        W_ = np.where(cand, wx * wz, 0.0); W_ = W_ * W_ * (3 - 2 * W_)
        SCARF_W[piece.shape] = W_
        C['scarf_geo'] = W_ > 0.5
        C['wraps'] |= C['scarf_geo'] & ~C['eye']
    taken |= C['wraps']
    plate_p = cov & np.isin(piece, PLATE_PIECES)
    boots = cov & np.isin(piece, [5, 6])
    C['plate'] = (plate_p | boots) & white & ~taken
    taken |= C['plate']
    C['cloak'] = cov & np.isin(piece, [1, 3]) & ~taken
    taken |= C['cloak']
    gear = cov & np.isin(gar, [7, 16]) & ~taken
    C['metal'] = gear & (s < 0.2) & (v > 0.3)
    C['leather'] = (gear & ~C['metal']) | (cov & ~taken & brown & ~np.isin(piece, [4, 7]))
    C['leather'] |= boots & ~taken
    taken |= C['metal'] | C['leather']
    C['under'] = cov & ~taken & np.isin(piece, [0, 4, 7, 9])
    rest = cov & ~(taken | C['under'])
    C['leather'] |= rest & ~face
    C['skin'] |= rest & face          # the rest of the face piece (lips and chin under the scarf) stays skin
    C['plate'] &= ~C['skin']
    return C


def build(meshy_dir, raster, ao_png, tag, albedo=None):
    Rz = np.load(HERE / 'work' / raster); gar, pos, piece = Rz['garment'], Rz['pos'], Rz['piece']; cov = gar >= 0
    sh = piece.shape
    base = load(meshy_dir / 'texture_urls_0_base_color.png', shape=sh); normal = load(meshy_dir / 'texture_urls_0_normal.png', shape=sh)
    rough_m = load(meshy_dir / 'texture_urls_0_roughness.png', 'L', sh)
    C = classify(base, gar, pos, cov, piece, Rz['bone'], Rz['bone_names'])
    if os.environ.get('PREVIEW'):
        pv = np.zeros(sh + (3,), np.uint8)
        for k, m in C.items():
            pv[m] = PREVIEW_COL[k]
        Image.fromarray(pv).save(HERE / 'work' / f'classes_{tag}.png')
    if albedo is None:
        sk = C['skin'] & (piece == 2)
        albedo = np.median(base[sk], 0) if sk.sum() > 100 else np.array([0.74, 0.55, 0.43])
    g = repaint_skin(base, C['skin'], albedo)
    if 'scarf_geo' in C:                                   # the scarf: one rust albedo x Meshy's fine shading, soft edge
        C.pop('scarf_geo'); w_ = SCARF_W[piece.shape]
        rp = repaint_skin(g, w_ > 0, WRAPS_ALBEDO)
        g = g * (1 - w_[..., None]) + rp * w_[..., None]
    g = ao_grade(g, load(HERE / 'work' / ao_png, 'L', sh), cov)
    print('CLASSES', tag, {k: int(m.sum()) for k, m in C.items()}, 'covered', int(cov.sum()),
          'skin albedo', np.round(albedo * 255).tolist())
    cls = np.zeros(sh, np.uint8); spec = np.zeros(sh); rgh = np.full(sh, 0.8)
    for k, m in C.items():
        if m.any():
            cls[m] = CLASS[k]; spec[m] = SPEC[k]; rgh[m] = np.clip(ROUGH[k] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
    return g, normal, spec, rgh, cls, C, cov, albedo


mask = lambda m, cv: ndimage.gaussian_filter(pad(m.astype(float), cv), 0.7)


def ramps(sets):
    """One ramp set fitted over every texture set's texels together: sets = [(base colour, classes, coverage), ...]
    (body and head pages of different sizes, flattened)."""
    out = {}
    g = np.concatenate([b.reshape(-1, 1, 3) for b, _, _ in sets])
    for r in REGIONS:
        w = np.clip(np.concatenate([mask(C_[r], c).reshape(-1, 1) for _, C_, c in sets]), 0, 1)
        fit, rep = R.fit_ramps(g, {'har_a': g}, w)
        a = fit['har_a']; cols = np.array(a['colors'])
        L = cols @ np.array([0.2126, 0.7152, 0.0722])
        med = np.median(R.luminance(g)[w >= 0.9])
        lmed = float(np.interp(med, np.linspace(a['range'][0], a['range'][1], 16), L))
        out[r] = {'har_a': a}
        for k, tgt in list(TIERS.items()) + ([('har_a', TIER_A)] if r in TIER_A else []):
            t = lin(np.array(tgt[r], np.float64) / 255)
            new = np.clip(t[None, :] * ((L / max(lmed, 1e-4)) ** SHADE)[:, None], 0, 1)
            out[r][k] = {'range': a['range'], 'colors': np.round(new, 6).tolist()}
        print('RAMPFIT', r, rep['har_a'], 'A median', np.round(srgb(cols[8]) * 255).astype(int).tolist())
    return out


BODY_MESHY = HERE / os.environ.get('BODY_MESHY', 'work/meshy_body_packed')
g, normal, spec, rgh, cls, C, cov, ALB = build(BODY_MESHY, 'uvraster_UVMap.npz', 'ao_UVMap.png', 'body')
BH, BW = cov.shape
save(pad(g, cov), T / 'har_basecolor_1k.png'); save(pad(normal, cov), T / 'har_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((BH, BW))], -1), T / 'har_metal_rough_1k.png')
R.write_mask([mask(C[r], cov) for r in REGIONS], T / 'har_region_mask.png', size=(BW, BH))
Image.fromarray(cls).save(T / 'har_material_classes.png')
hg, hn, hspec, hrgh, hcls, HC, hcov, _ = build(HERE / 'meshy' / 'head_retexture_v1', 'uvraster_HeadUV.npz', 'ao_HeadUV.png', 'head', ALB)
save(pad(hg, hcov), T / 'har_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'har_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'har_head_metal_rough_1k.png')
HSW = next(iter(SCARF_W.values())) if SCARF_W else np.zeros((N, N))
hmask = {r: mask(HC[r], hcov) for r in REGIONS}
hmask['wraps'] = np.maximum(mask(HC['wraps'] & (HSW <= 0), hcov), ndimage.gaussian_filter(HSW, 0.7))
hmask['cloak'] = np.minimum(hmask['cloak'], 1 - ndimage.gaussian_filter(HSW, 0.7))
R.write_mask([hmask[r] for r in REGIONS], T / 'har_head_region_mask.png', size=N)
Image.fromarray(hcls).save(T / 'har_head_material_classes.png')
RB = ramps([(g, C, cov), (hg, HC, hcov)])
mats = [{'base': 'HAR_A', 'prefix': 'HAR', 'mask': 'har_region_mask.png', 'regions': REGIONS,
         'ramps': {k: [RB[r][k] for r in REGIONS] for k in VARIANTS}},
        {'base': 'HARHead_A', 'prefix': 'HARHead', 'mask': 'har_head_region_mask.png', 'regions': REGIONS,
         'ramps': {k: [RB[r][k] for r in REGIONS] for k in VARIANTS}}]
(T / 'har_ramps.json').write_text(json.dumps({'variants': VARIANTS, 'materials': mats, 'tiers': TIERS,
    'monsters': {'har_a': '10070 Ashrunner Scav', 'har_b': '10071 Ashrunner Raider', 'har_c': '10072 Ashrunner Gunner'}}, indent=1) + '\n')
for k in VARIANTS:
    print('RAMP', k, {r: [round(float(x) * 255) for x in srgb(np.array(RB[r][k]['colors'][8]))] for r in REGIONS})
if os.environ.get('PREVIEW'):
    for tag, img, CC in (('body', g, C), ('head', hg, HC)):
        lumi = R.luminance(img); col0 = lin(img)
        for k in VARIANTS:
            col = col0.copy()
            for r in REGIONS:
                rp = RB[r][k]; lo, hi = rp['range']; stops = np.array(rp['colors'])
                tt = np.clip((lumi - lo) / (hi - lo), 0, 1) * 15; i0 = np.minimum(np.floor(tt).astype(int), 14); fr = (tt - i0)[..., None]
                rc = stops[i0] * (1 - fr) + stops[i0 + 1] * fr; w = ndimage.gaussian_filter(CC[r].astype(float), 0.7)[..., None]
                col = col * (1 - w) + rc * w
            save(srgb(col), HERE / 'work' / f'tierprev_{tag}_{k}.png')
