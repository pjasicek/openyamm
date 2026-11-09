#!/usr/bin/env python3
"""Textures, region masks and tier ramps for the m438 zombie (after mm7_m190_claude/scripts/compose_m190.py;
CLAUDE_CREATURE_TEXTURES.md). Run after transfer_uv.py, uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py.
Tiers recolour one region, as the native ACT transforms do (mm7_m438 config/variants: entries 94-209 change, the
identity mask shows the trousers and the headband): R = the trousers (piece P01, wound texels seen through its holes
excluded) in the body set and the headband in the head set. Skin, wounds, bone, rope stay. Tier A Rotted Corpse =
palette 118 (olive-brown, the HD masters' colours), B Walking Dead = 119 (pale grey), C Zombie = 123 (dark
charcoal-teal) - from the 7m439 / m440 / 7m441 sprite frame tables (assets_dev/engine/rendering/sprite_frames).
- Skin (body pieces P00 skin, P02/P03 feet, P16 shin; the head set's skin): Meshy painted salmon/peach patches on the
  grey-green skin; one albedo (the native sprite's grey-green skin x 1.4) times Meshy's fine shading, mixed SKIN_MIX
  over Meshy's colour. Wounds (saturated red, saturation > 0.6) keep Meshy's paint.
- Base colour graded by the rest-pose AO; ORM red = per-class specular (openyamm_specular_mask), green = roughness,
  blue = 0. Material class map per set (1 skin/flesh, 5 bone/teeth, 6 eye, 8 cloth/rope).
- Ramps: histogram-matched to the native pixels: the region's pixels in the standing, walking and attack frames
  (palette entries that change between the tiers), ordered by their tier-A luminance; stop j (at luminance
  lo + j/15 (hi - lo), lo/hi the region texels' 2nd/98th percentiles, body and head together) takes each tier
  palette's mean colour around the rank the texels reach at that luminance, x RAMP_GAIN. One ramp set for both sets.
- The severed-forearm prop is textured from this body set by forearm_textures.py.
Writes textures/m438_*."""
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
SKIN_MIX, RAMP_GAIN = 0.85, 1.35
PALS = {'m438_a': 118, 'm438_b': 119, 'm438_c': 123}
SPEC = {'skin': 0.35, 'wound': 0.45, 'cloth': 0.2, 'rope': 0.2, 'bone': 0.45, 'eye': 0.9, 'hair': 0.3}
ROUGH = {'skin': 0.6, 'wound': 0.5, 'cloth': 0.85, 'rope': 0.85, 'bone': 0.45, 'eye': 0.2, 'hair': 0.7}
CLASS_ID = {'skin': 1, 'wound': 1, 'cloth': 8, 'rope': 8, 'bone': 5, 'eye': 6, 'hair': 2}


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


def classify(base, cov, piece, head=False, pos=None):
    hue, sat, val = hsv(base)
    red = ((hue < 18) | (hue > 335)) & (sat > 0.6) & (val > 0.15)    # the salmon skin patches (sat 0.4-0.5) are skin
    if head:
        eye = cov & np.isin(piece, [14, 15])
        bone = cov & (piece == 13)
        # the headband by colour AND rest position (uv_raster 'pos'): around the skull above the brow (z 1.635-1.71 m;
        # the colour alone also took yellowish speckles on the face), plus the knot and tails at the back of the head
        z, yb = pos[..., 2], pos[..., 1]
        where = ((z > 1.635) & (z < 1.71)) | ((yb > 0.07) & (z > 1.55) & (z < 1.71))
        band = cov & (piece == 0) & (hue > 28) & (hue < 70) & (sat > 0.28) & (val > 0.2) & where
        band = ndimage.binary_closing(ndimage.binary_opening(band, iterations=1), iterations=3) & cov & (piece == 0) & where
        wound = cov & (piece == 0) & red & ~band
        hair = np.zeros_like(cov)
        skin = cov & (piece == 0) & ~band & ~wound
        return {'skin': skin, 'wound': wound, 'cloth': band, 'rope': np.zeros_like(cov), 'bone': bone, 'eye': eye, 'hair': hair}
    skin_p = np.isin(piece, [0, 2, 3, 16])
    wound = cov & red & (skin_p | (piece == 1))
    cloth = cov & (piece == 1) & ~wound
    rope = cov & np.isin(piece, [4, 5])
    bone = cov & np.isin(piece, [6, 7, 8, 9, 10, 11, 12])
    wound |= bone & red                                         # Meshy painted parts of the bone rods red: blood on bone
    bone &= ~wound
    skin = cov & skin_p & ~wound
    z = np.zeros_like(cov)
    return {'skin': skin, 'wound': wound, 'cloth': cloth, 'rope': rope, 'bone': bone, 'eye': z, 'hair': z}


# ---------------------------------------------------------------- body set
M = HERE / 'meshy' / 'body_retexture_v1'
base = load(M / 'texture_urls_0_base_color.png'); normal = load(M / 'texture_urls_0_normal.png')
rough_m = load(M / 'texture_urls_0_roughness.png', 'L')
Rz = np.load(HERE / 'work' / 'uvraster_UVMap.npz'); piece = Rz['piece']; cov = piece >= 0
C = classify(base, cov, piece)
# ---------------------------------------------------------------- head set
HM = HERE / 'meshy' / 'head_retexture_v1'
hb = load(HM / 'texture_urls_0_base_color.png'); hn = load(HM / 'texture_urls_0_normal.png')
hr_m = load(HM / 'texture_urls_0_roughness.png', 'L')
Rh = np.load(HERE / 'work' / 'uvraster_HeadUV.npz'); hpiece = Rh['piece']; hcov = hpiece >= 0
HC = classify(hb, hcov, hpiece, head=True, pos=Rh['pos'])
hue_b, sat_b, val_b = hsv(base)
# skin albedo from the native sprite: the grey-green torso/head pixels of m438sa0 (palette entries that no tier changes,
# saturation < 0.35; median sRGB 80/80/70, hue 60) x SKIN_GAIN (sprites carry baked shading). Meshy's own grey median
# was warmer (120/113/100, hue 34) and its salmon patches warmer still.
INV0 = json.loads((HERE / 'references_native' / 'inventory.json').read_text())
P0 = {p: np.frombuffer((REPO / INV0['palette_sources'][p]['path']).read_bytes()[:768], np.uint8).reshape(256, 3).astype(float)
      for p in ('118', '119')}
idx0 = np.array(Image.open(REPO / INV0['sources']['m438sa0']['path'])); top0 = np.where((idx0 != 0).any(1))[0].min()
reg0 = idx0[top0:top0 + 90]; same0 = np.abs(P0['118'] - P0['119']).max(1) <= 8
c0 = P0['118'][reg0[same0[reg0] & (reg0 != 0)]]
s0 = (c0.max(1) - c0.min(1)) / np.maximum(c0.max(1), 1)
SKIN_GAIN = 1.4
SKIN = np.clip(np.median(c0[s0 < 0.35], 0) * SKIN_GAIN / 255, 0, 1)
print('SKIN albedo sRGB', np.round(SKIN * 255).tolist(), 'from', int((s0 < 0.35).sum()), 'native pixels')
# wounds (review 2026-10-20: Meshy's flat saturated red read as poster paint): re-graded toward the native wound
# colours, the red/crimson pixels of the standing and walking frames (palette entries no tier changes; median sRGB
# 64/12/13, 5..95 % luminance 9..75), histogram-matched: each wound texel takes the native wound colour at the rank its
# Meshy luminance holds among all wound texels (Meshy's detail order kept), x WOUND_GAIN; blended through a 1-texel
# feather so the wound edge does not outline
WOUND_GAIN = 1.0                 # 1.15 still read bright on the shin under the viewer light
_wp = []
for fr in [f'm438sa{v}' for v in range(5)] + [f'm438w{c}0' for c in 'aceg']:
    _i = np.array(Image.open(REPO / INV0['sources'][fr]['path'])); _wp.append(_i[_i != 0])
_wc = P0['118'][np.concatenate(_wp)] / 255
_mx, _mn = _wc.max(1), _wc.min(1); _sat = (_mx - _mn) / np.maximum(_mx, 1e-6)
_h = np.array([__import__('colorsys').rgb_to_hsv(*x)[0] for x in _wc]) * 360
NATIVE_WOUND = _wc[((_h < 18) | (_h > 335)) & (_sat > 0.5) & (_mx > 0.08)]
NATIVE_WOUND = NATIVE_WOUND[np.argsort(R.luminance(NATIVE_WOUND), kind='stable')]
print('WOUND native pixels', len(NATIVE_WOUND), 'median sRGB', np.round(np.median(NATIVE_WOUND, 0) * 255).tolist())
_wl_all = np.sort(np.concatenate([R.luminance(base[C['wound']]), R.luminance(hb[HC['wound']])]))


def regrade_wounds(img, m):
    L = R.luminance(img)
    q = np.searchsorted(_wl_all, L) / max(len(_wl_all), 1)
    new = NATIVE_WOUND[np.clip((q * (len(NATIVE_WOUND) - 1)).astype(int), 0, len(NATIVE_WOUND) - 1)] * WOUND_GAIN
    k = np.clip(ndimage.gaussian_filter(m.astype(float), 0.6) * 1.5, 0, 1)[..., None]
    k = np.where(m[..., None], 1.0, k)
    return np.clip(img * (1 - k) + new * k, 0, 1)


g = ao_grade(regrade_wounds(repaint_skin(base, C['skin'], SKIN), C['wound']), load(HERE / 'work' / 'ao_UVMap.png', 'L'), cov)
hg = ao_grade(regrade_wounds(repaint_skin(hb, HC['skin'], SKIN), HC['wound']), load(HERE / 'work' / 'ao_HeadUV.png', 'L'), hcov)
# torn hole rims (review 2026-10-20): Meshy painted the frayed cloth around every trouser hole as a pale grey band;
# inside the mask it took the light half of the ramp and showed as a uniform white halo on tier B (palette 119 maps
# the lit cloth entries to near-white, the shadow entries to dark grey). Trouser texels within 7 texels of a wound are
# (or within 3 cm of one in 3D) are brought down to at most the cloth's 25th-percentile luminance (linear scale, hue kept): a shadowed torn edge in
# every tier instead of a light ring
_rim = C['cloth'] & ndimage.binary_dilation(C['wound'], iterations=7)
# ... and by rest position (uv_raster 'pos'): the cuff above the shin wound and hole edges on other UV islands sit
# within 3 cm of a wound texel in 3D but far from it in UV space
from scipy.spatial import cKDTree
_pos = Rz['pos']; _wt = cKDTree(_pos[C['wound'] & np.isin(piece, [0, 1, 2, 16])][::3])
_ci = np.argwhere(C['cloth']); _dist, _ = _wt.query(_pos[C['cloth']], k=1, distance_upper_bound=0.05)
_near = np.zeros_like(C['cloth']); _near[_ci[_dist < 0.03, 0], _ci[_dist < 0.03, 1]] = True
_rim |= _near
_Lc = np.percentile(R.luminance(g[C['cloth']]), 25); _L = R.luminance(g)
_hot = _rim & (_L > _Lc)
g[_hot] = srgb(lin(g[_hot]) * (_Lc / np.maximum(_L[_hot], 1e-6))[:, None])
print('RIM trouser texels near wounds darkened to the cloth 25th percentile', int(_hot.sum()))
print('WOUND regraded median sRGB body', np.round(np.median(g[C['wound']], 0) * 255).tolist())
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
# ivory for the stump's new bone shafts (stump_bone.py maps them into work/bone_patch.json, free atlas texels): the
# native sprites' pale bone pixels (unchanged palette entries of m438sa0..4, value > 0.6, saturation 0.12-0.5, hue
# 15-60: median sRGB 187/156/126) x 1.15, with soft mottling (Meshy's rod paint was salmon, 212/156/121)
import colorsys
_ip = []
for fr in [f'm438sa{v}' for v in range(5)]:
    _i = np.array(Image.open(REPO / INV0['sources'][fr]['path'])); _ip.append(_i[(_i != 0) & same0[_i]])
_ic = P0['118'][np.concatenate(_ip)] / 255
_ih = np.array([colorsys.rgb_to_hsv(*x) for x in _ic])
_im = (_ih[:, 2] > 0.6) & (_ih[:, 1] > 0.12) & (_ih[:, 1] < 0.5) & (_ih[:, 0] * 360 > 15) & (_ih[:, 0] * 360 < 60)
BONE = np.clip(np.median(_ic[_im], 0) * 1.15, 0, 1)
_bp = json.loads((HERE / 'work' / 'bone_patch.json').read_text()) if (HERE / 'work' / 'bone_patch.json').exists() else None
print('BONE ivory sRGB', np.round(BONE * 255).tolist(), 'patch', _bp)
gp, nrp, mrp = pad(g, cov), pad(normal, cov), np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1)
if _bp:
    r0_, c0_, n_ = _bp['row'], _bp['col'], _bp['size']; sl = (slice(r0_, r0_ + n_), slice(c0_, c0_ + n_))
    mot = ndimage.gaussian_filter(np.random.default_rng(5).normal(0, 1, (n_, n_)), 2.0); mot /= max(np.abs(mot).max(), 1e-6)
    gp[sl] = np.clip(BONE[None, None, :] * (1 + 0.12 * mot[..., None]), 0, 1)
    nrp[sl] = (0.5, 0.5, 1.0); mrp[sl] = (SPEC['bone'], ROUGH['bone'], 0.0); cm[sl] = CLASS_ID['bone']
save(gp, T / 'm438_basecolor_1k.png'); save(nrp, T / 'm438_normal_1k.png')
save(mrp, T / 'm438_metal_rough_1k.png')
Image.fromarray(cm).save(T / 'm438_material_classes.png')
hspec, hrgh, hcm = maps(hr_m, HC)
save(pad(hg, hcov), T / 'm438_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'm438_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm438_head_metal_rough_1k.png')
Image.fromarray(hcm).save(T / 'm438_head_material_classes.png')


def soft(m, c):
    """Mask padded like the colour (nearest island texel into gutters), blurred, then zeroed on wound texels."""
    return np.clip(ndimage.gaussian_filter(pad(m.astype(float), c), 0.7), 0, 1)


# trousers: wound texels and their 2-texel border stay out of the mask (they carry the wound's colour; on tier B they
# took the light end of the ramp as white halos), then pad and blur as usual
WOUND_RIM = ndimage.binary_dilation(C['wound'], iterations=2)
body_r = soft(C['cloth'] & ~WOUND_RIM, cov); body_r[C['wound'] | C['rope'] | C['skin'] | C['bone']] = 0
# the band's 1-texel border carries skin colour (white specks under the tier-B band): mask from the band eroded by one
# texel, soft edge limited to 1 texel beyond the band
head_r = soft(ndimage.binary_erosion(HC['cloth'], iterations=1), hcov)
far = ndimage.distance_transform_edt(~HC['cloth']) > 1
head_r[(HC['skin'] | HC['wound'] | HC['eye'] | HC['bone']) & far] = 0
if _bp:
    body_r[_bp['row']:_bp['row'] + _bp['size'], _bp['col']:_bp['col'] + _bp['size']] = 0   # the bone patch never recolours
R.write_mask([body_r], T / 'm438_region_mask.png', size=N)
R.write_mask([head_r], T / 'm438_head_region_mask.png', size=N)
# ---------------------------------------------------------------- ramps (rank-matched to the native sprite pixels)
INV = json.loads((HERE / 'references_native' / 'inventory.json').read_text())
pal = {k: np.frombuffer((REPO / INV['palette_sources'][str(p)]['path']).read_bytes()[:768], np.uint8).reshape(256, 3) / 255
       for k, p in PALS.items()}
chg = (np.abs(pal['m438_a'] - pal['m438_b']).max(1) > 0.03) | (np.abs(pal['m438_c'] - pal['m438_a']).max(1) > 0.03)
FRAMES = [f'm438sa{v}' for v in range(5)] + [f'm438w{c}{v}' for c in 'aceg' for v in (0, 2, 4)] + [f'm438a{c}0' for c in 'aceg']
pix = []
for fr in FRAMES:
    idx = np.array(Image.open(REPO / INV['sources'][fr]['path']))
    pix.append(idx[chg[idx] & (idx != 0)])
pix = np.concatenate(pix)
order = np.argsort(R.luminance(pal['m438_a'][pix]), kind='stable'); pix = pix[order]
lum = np.concatenate([R.luminance(g[C['cloth'] & ~_hot]), R.luminance(hg[HC['cloth']])])   # the darkened rims stay out of the histogram
lo, hi = np.percentile(lum, [2, 98])
ramps, report = {k: [] for k in PALS}, {}
# histogram matching: stop j sits at luminance lo + j/15 (hi - lo); its colour is the native colour at the rank the
# region's texels reach at that luminance (texel CDF), so the share of dark-green shadow vs olive-brown cloth matches
# the sprite (a plain 16-quantile ramp put most texels on the green shadow entries: tier A read dark green)
ls_ = np.sort(lum)
for k in PALS:
    cols = []
    for j in range(16):
        q = np.searchsorted(ls_, lo + j / 15 * (hi - lo)) / len(ls_)
        a_ = int(np.clip(q - 1 / 32, 0, 1) * (len(pix) - 1)); b_ = max(int(np.clip(q + 1 / 32, 0, 1) * (len(pix) - 1)), a_ + 1)
        c = pal[k][pix[a_:b_]].mean(0)
        cols.append(np.clip(lin(np.clip(c * RAMP_GAIN, 0, 1)), 0, 1))
    ramps[k].append({'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': [[round(float(v), 6) for v in c] for c in cols]})
    report[k] = [[round(float(v) * 255) for v in srgb(cols[j])] for j in (2, 8, 14)]
print('NATIVE region pixels', len(pix), 'palette entries', len(set(pix.tolist())))
print('RAMPS sRGB stops 2/8/14', report, 'range', round(float(lo), 4), round(float(hi), 4))
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Zombie_A', 'prefix': 'Zombie', 'mask': 'm438_region_mask.png', 'regions': ['cloth'],
                      'palettes': PALS, 'ramps': ramps},
                     {'base': 'ZombieHead_A', 'prefix': 'ZombieHead', 'mask': 'm438_head_region_mask.png', 'regions': ['cloth'],
                      'palettes': PALS, 'ramps': ramps}]}
(T / 'm438_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
(T / 'm438_swatches.json').write_text(json.dumps({'skin_srgb': [round(float(v) * 255) for v in SKIN],
                                                    'wound_srgb': [round(float(v) * 255) for v in np.median(g[C['wound']], 0)],
                                                    'wound_ramp_srgb': [[round(float(v) * 255) for v in NATIVE_WOUND[int(q * (len(NATIVE_WOUND) - 1))] * WOUND_GAIN]
                                                                        for q in np.linspace(0, 1, 16)],
                                                    'bone_srgb': [round(float(v) * 255) for v in BONE]},
                                                   indent=1) + '\n')
