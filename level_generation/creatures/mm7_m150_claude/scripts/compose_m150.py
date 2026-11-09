#!/usr/bin/env python3
"""Textures, region mask and tier ramps for m150 (CLAUDE_CREATURE_TEXTURES.md), adapted from mm7_m150_claude. Run after
uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py. Head set from meshy/head_retexture_v1.

Tiers (mm7_m150/variants.json: 199 Angel 151, 200 Angel Lord 152, 201 Archangel 153) recolour ONE region, as the
native mask does (mm7_m150/manifest.json 'regions': cloth = the green skirt; native indices 201..246 of the recolour):
the skirt green -> blue (152) -> magenta (153). Wings, skin, steel, brass, leather tabs, shield and sword stay.
- Classes per texel: cloth = green hue (the skirt), gold = saturated yellow, steel = low saturation, leather = dark
  warm, skin = warm texels of the skin pieces (0 torso/arms/face, 2 legs, 4/5 forearms and hands), feathers = the wing
  garment (5), eyes = pieces 39/40, hair = dark texels of the helmet/hair piece 3 in the head set.
- Skin repainted (natm): one albedo x Meshy's fine shading. AO graded into the base colour; ORM red = per-class
  specular mask (openyamm_specular_mask), green = roughness.
- Ramps per tier from that tier's native pixels of the region's palette indices, rank-matched to the region's texel
  luminance (2nd-98th percentile), gain RAMP_GAIN; mask padded into the gutters.
- Props: the Meshy sword keeps its maps (ORM red from its colour classes, green its roughness); the shield's base is
  the unskewed sheet (make_props_m150.py), its ORM by colour (bronze/brass, leather).
Writes textures/m150_*."""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
NATIVE = HERE.parent / 'mm7_m150' / 'native'
PALDIR = HERE.parents[2] / 'assets_dev' / 'worlds' / 'mm7' / 'textures'
N = 1024
BODY_SHARP_SIGMA, BODY_SHARP_AMT, BODY_NORMAL_GAIN = float(os.environ.get('BODY_SHARP_SIGMA', '1.2')), float(os.environ.get('BODY_SHARP_AMT', '0.8')), float(os.environ.get('BODY_NORMAL_GAIN', '1.6'))
SKIN_MIX = 0.85; RAMP_GAIN = {'cloth': 1.15}   # 1.3 read pale next to the native green
PALS = {'m150_a': 151, 'm150_b': 152, 'm150_c': 153}
REGION_IDX = None
CLASS = {'skin': 1, 'hair': 2, 'cloth': 8, 'leather': 8, 'gold': 9, 'steel': 9, 'eye': 6, 'feather': 2}
SPEC = {'skin': 0.45, 'hair': 0.3, 'cloth': 0.25, 'leather': 0.35, 'gold': 1.0, 'steel': 0.8, 'eye': 0.9, 'feather': 0.2}
ROUGH = {'skin': 0.5, 'hair': 0.6, 'cloth': 0.85, 'leather': 0.6, 'gold': 0.3, 'steel': 0.35, 'eye': 0.2, 'feather': 0.8}
PREVIEW_COL = {'skin': (230, 170, 140), 'hair': (150, 90, 20), 'cloth': (20, 200, 40), 'leather': (90, 50, 20),
               'feather': (140, 140, 255), 'gold': (250, 210, 0), 'steel': (180, 180, 190), 'eye': (255, 0, 255)}


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


def lin(x): return R.srgb_to_linear(x)
def srgb(x):
    x = np.asarray(x, np.float64); return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(np.maximum(x, 0), 1 / 2.4) - 0.055)


def repaint_skin(img, m, albedo, sigma=6.0):
    # v2: Meshy's skin carries brown blotches wider than the blur (deltoids, thighs: user review 'dark patches'); the
    # detail is clipped to +-20 % so only the fine shading (muscle lines, pores) survives
    L = R.luminance(img)
    num = ndimage.gaussian_filter(np.where(m, L, 0.0), sigma); den = ndimage.gaussian_filter(m.astype(float), sigma)
    Lb = num / np.maximum(den, 1e-4)
    big = ndimage.gaussian_filter(np.where(m, L, 0.0), sigma * 4) / np.maximum(ndimage.gaussian_filter(m.astype(float), sigma * 4), 1e-4)
    detail = np.clip((L / np.maximum(Lb, 1e-4)) ** 1.15, 0.8, 1.2) * np.clip(Lb / np.maximum(big, 1e-4), 0.9, 1.1)
    new = srgb(np.clip(lin(albedo)[None, :] * detail[m][:, None], 0, 1))
    out = img.copy(); out[m] = img[m] * (1 - SKIN_MIX) + new * SKIN_MIX
    return out


def repaint_region(img, m, albedo, sigma=6.0, mix=0.85):
    L = R.luminance(img)
    num = ndimage.gaussian_filter(np.where(m, L, 0.0), sigma); den = ndimage.gaussian_filter(m.astype(float), sigma)
    Lb = num / np.maximum(den, 1e-4)
    detail = np.clip((L / np.maximum(Lb, 1e-4)) ** 1.15, 0.45, 1.6)
    new = srgb(np.clip(lin(albedo)[None, :] * detail[m][:, None], 0, 1))
    out = img.copy(); out[m] = img[m] * (1 - mix) + new * mix
    return out


def ao_clean(ao, cov):
    # v2 (user review: dark triangular patches on the deltoids and thighs): the Cycles AO bake leaves whole faces
    # black where its rays start inside overlapping shells; a texel far darker than its island neighbourhood (masked
    # median over 25 px) takes that neighbourhood's value
    a = np.where(cov, ao, np.nan)
    num = ndimage.gaussian_filter(np.where(cov, ao, 0.0), 10); den = ndimage.gaussian_filter(cov.astype(float), 10)
    local = num / np.maximum(den, 1e-4)
    big = ndimage.grey_closing(np.where(cov, ao, 1.0), size=(25, 25))
    ref = np.minimum(local, big)
    bad = cov & (ao < 0.65 * ref)
    out = ao.copy(); out[bad] = ref[bad]
    return out, int(bad.sum())


def ao_grade(img, ao, cov, strength=0.4, floor=0.45):
    f = np.clip(1 - strength + strength * np.maximum(ao, floor), 0, 1)
    out = img.copy(); out[cov] = img[cov] * f[cov][:, None]; return out


LABELS = json.load(open(HERE / 'work' / 'step1_labels.json'))
HAIR = [int(k) for k, v in LABELS.items() if v == 'hair']
STEEL_ALB = np.array([float(x) for x in os.environ.get('STEEL_ALB', '128,131,138').split(',')]) / 255
WING_LUM = float(os.environ.get('WING_LUM', '0.55'))   # target median linear luminance of the feathers (masters: pale lavender)


def classify(base, gar, pos, cov, head_layout, piece, metal=None):
    h, s, v = hsv(base)
    C = {}
    C['feather'] = cov & (gar == 5)
    C['cloth'] = cov & (h > 85) & (h < 175) & (s > 0.25) & (v > 0.08) & ~C['feather']
    C['eye'] = cov & np.isin(piece, [15, 16])
    C['gold'] = cov & (h > 30) & (h < 62) & (s > 0.45) & (v > 0.40) & ~C['cloth'] & ~C['feather'] & ~C['eye']
    C['hair'] = cov & np.isin(piece, HAIR) & ~C['gold']
    st = (s < 0.25) if metal is None else ((metal > 0.5) & (s < 0.3)) | ((s < 0.12) & ~np.isin(piece, [0, 4, 5]))
    C['steel'] = cov & st & ~C['cloth'] & ~C['feather'] & ~C['eye'] & ~C['hair'] & ~C['gold']
    warm = cov & ((h < 50) | (h > 330)) & ~C['gold'] & ~C['cloth'] & ~C['steel'] & ~C['eye'] & ~C['feather'] & ~C['hair']
    C['skin'] = warm & np.isin(piece, [0, 4, 5]) & (s > 0.12) & (v > 0.08)        # v2: the dark brown blotches are skin too
    C['leather'] = cov & ~np.any([m for m in C.values()], axis=0)
    return C


# ---------------------------------------------------------------- native region colours per tier
def pal(i):
    return np.frombuffer(open(PALDIR / f'pal{i:03d}.act', 'rb').read()[:768], np.uint8).reshape(256, 3).astype(np.float64) / 255


BASEP = (pal(151) * 255).astype(int)              # the native sprites are drawn in palette 151 (tier A, exact bypass)
LUT = {tuple(c): i for i, c in enumerate(BASEP)}
frames = sorted(p for p in NATIVE.glob('m150*.png') if p.name[4] in 'saw')
idx_pixels = []
for f in frames:
    a = np.asarray(Image.open(f).convert('RGBA'))
    m = a[..., 3] > 0
    idx_pixels.append(np.array([LUT.get(tuple(c), -1) for c in a[m][:, :3]]))
IDX = np.concatenate(idx_pixels)
import colorsys
_h = np.array([colorsys.rgb_to_hsv(*c) for c in pal(151)])
MAN = json.load(open(HERE.parent / 'mm7_m150' / 'manifest.json'))['recolor']['native_indices']
dif = np.array([i for i in MAN if _h[i, 1] > 0.2 and 0.22 < _h[i, 0] < 0.5])      # the green entries (skirt)
REGION_IDX = {'cloth': dif.tolist()}
print('REGION cloth palette indices', len(dif), dif.min(), dif.max())
native = {}
for reg, ids in REGION_IDX.items():
    sel = IDX[np.isin(IDX, ids)]
    for k, p in PALS.items():
        X = pal(p)[sel]; L = R.luminance(X); keep = L > 0.035
        o = np.argsort(L[keep]); native[(reg, k)] = X[keep][o]
    print('NATIVE', reg, 'pixels', len(sel), {k: np.round(np.median(native[(reg, k)], 0) * 255).tolist() for k in PALS})


def ramps_for(reg, texel_lum):
    lo, hi = np.percentile(texel_lum, [2, 98]); srt = np.sort(texel_lum)
    out = {}
    for k in PALS:
        X = native[(reg, k)]; cols = []
        for i in range(16):
            Li = lo + (hi - lo) * i / 15
            q = np.searchsorted(srt, Li) / len(srt)
            c = X[min(len(X) - 1, int(q * (len(X) - 1)))]
            cols.append([round(float(v), 6) for v in np.clip(lin(np.clip(c * RAMP_GAIN[reg], 0, 1)), 0, 1)])
        out[k] = {'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols}
    return out


def build(meshy_dir, raster, ao_png, head_layout, tag, albedo=None):
    base = load(meshy_dir / 'texture_urls_0_base_color.png'); normal = load(meshy_dir / 'texture_urls_0_normal.png')
    rough_m = load(meshy_dir / 'texture_urls_0_roughness.png', 'L')
    metal = load(meshy_dir / 'texture_urls_0_metallic.png', 'L')
    Rz = np.load(HERE / 'work' / raster); gar, pos = Rz['garment'], Rz['pos']; cov = gar >= 0
    C = classify(base, gar, pos, cov, head_layout, Rz['piece'], metal)
    if os.environ.get('PREVIEW'):
        pv = np.zeros((N, N, 3), np.uint8)
        for k, m in C.items():
            pv[m] = PREVIEW_COL[k]
        Image.fromarray(pv).save(HERE / 'work' / f'classes_{tag}.png')
    if albedo is None:                                     # the head reuses the body's albedo: no neck seam
        albedo = np.median(base[C['skin']], 0) if C['skin'].sum() > 100 else np.array([0.85, 0.65, 0.55])
    g = repaint_skin(base, C['skin'], albedo)
    # v2: Meshy paints metals as dark albedo + metallic; the runtime is non-metallic with a specular mask, so steel read
    # black (user review of v1). Polished steel albedo x Meshy's fine shading, like the skin repaint.
    if C['steel'].any():
        g = repaint_region(g, C['steel'], STEEL_ALB, mix=0.9)
    if not head_layout:
        # v2 shoulder straps (piece 3): Meshy painted them solid gold with dark brown discs (user review: 'the dark
        # circles'); the masters draw steel straps with brass rims and gold studs: a RIM_PX band along the strap's UV
        # island edge stays brass, the inside becomes steel, the dark discs gold studs
        m3 = cov & (Rz['piece'] == 3)
        if m3.any():
            dist = ndimage.distance_transform_edt(m3)
            inner = m3 & (dist > float(os.environ.get('RIM_PX', '7')))
            hh, sv, vv = hsv(base)
            disc = inner & (vv < 0.42)
            plate = inner & ~disc
            g = repaint_region(g, plate, STEEL_ALB, mix=0.95)
            gold_alb = np.median(base[C['gold'] & ~m3], 0) if (C['gold'] & ~m3).any() else np.array([0.9, 0.75, 0.3])
            g = repaint_region(g, disc, gold_alb, mix=0.95)
            C['steel'] = C['steel'] | plate; C['gold'] = (C['gold'] & ~plate) | disc
            for k_ in ('leather', 'skin', 'cloth'):
                C[k_] = C[k_] & ~inner
            print('STRAPS plate texels', int(plate.sum()), 'studs', int(disc.sum()), 'rim', int((m3 & ~inner).sum()))
            # Meshy also painted a second gold strap with brown discs onto the cuirass under/beside the real strap: on
            # the skin shell, gold and dark-disc texels within STRAP_NEAR m of the strap shell and above the cuirass
            # rim band become steel
            from scipy.spatial import cKDTree
            sp = pos[m3][::7]
            cand = cov & (Rz['piece'] == 0) & (C['gold'] | (C['leather'] & (vv < 0.45)))
            near = np.zeros_like(cov)
            if cand.any():
                d, _ = cKDTree(sp).query(pos[cand], k=1, distance_upper_bound=float(os.environ.get('STRAP_NEAR', '0.06')))
                near[cand] = np.isfinite(d)
            # the strap shell is open (its stud openings are holes, 112 boundary edges): the torso under it shows
            # through and Meshy painted it skin; every skin-shell texel within STRAP_UNDER of the strap becomes steel
            p0 = cov & (Rz['piece'] == 0)
            d0, _ = cKDTree(pos[m3]).query(pos[p0], k=1, distance_upper_bound=float(os.environ.get('STRAP_UNDER', '0.012')))
            under = np.zeros_like(cov); under[p0] = np.isfinite(d0)
            near |= under
            g = repaint_region(g, near, STEEL_ALB, mix=0.95)
            C['steel'] = C['steel'] | near
            for k_ in ('gold', 'leather', 'skin'):
                C[k_] &= ~near
            print('STRAPS skin-shell texels under the strap', int(under.sum()))
            print('STRAPS cuirass texels under/beside the straps repainted steel', int(near.sum()))
            # the normal map carries Meshy's painted disc relief there too (the viewer showed light ovals): flatten it
            flat = ndimage.gaussian_filter((plate | disc | near).astype(float), 1.5)[..., None]
            normal[:] = normal * (1 - flat) + np.array([0.5, 0.5, 1.0]) * flat
    if C['feather'].any():
        fl = R.luminance(g[C['feather']]); k = WING_LUM / max(float(np.median(fl)), 1e-3)
        g[C['feather']] = srgb(np.clip(lin(g[C['feather']]) * k, 0, 1))
        print('FEATHERS median lum', round(float(np.median(fl)), 3), 'gain', round(k, 2))
    aoc, nbad = ao_clean(load(HERE / 'work' / ao_png, 'L'), cov)
    print('AOCLEAN', tag, 'texels replaced', nbad)
    g = ao_grade(g, aoc, cov)
    # v5 (user review: blurry armour): unsharp mask and stronger normal slopes on the hard surfaces (steel, gold,
    # leather); skin, feathers and cloth stay soft
    hard = (C['steel'] | C['gold'] | C['leather'])[..., None].astype(float)
    hard = ndimage.gaussian_filter(hard, (1.0, 1.0, 0))
    bl = ndimage.gaussian_filter(g, (BODY_SHARP_SIGMA, BODY_SHARP_SIGMA, 0))
    g = np.clip(g + (g - bl) * BODY_SHARP_AMT * hard, 0, 1)
    nn = normal * 2 - 1
    nn[..., :2] *= 1 + (BODY_NORMAL_GAIN - 1) * hard
    nn /= np.maximum(np.linalg.norm(nn, axis=-1, keepdims=True), 1e-6)
    normal = nn * 0.5 + 0.5
    print('CLASSES', tag, {k: int(m.sum()) for k, m in C.items()}, 'covered', int(cov.sum()),
          'skin albedo', np.round(albedo * 255).tolist())
    cls = np.zeros((N, N), np.uint8); spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8)
    for k, m in C.items():
        if m.any():
            cls[m] = CLASS[k]; spec[m] = SPEC[k]; rgh[m] = np.clip(ROUGH[k] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
    return g, normal, spec, rgh, cls, C, cov, albedo


cfg_ramps = {}
g, normal, spec, rgh, cls, C, cov, ALB = build(HERE / 'meshy' / 'retexture_v2', 'uvraster_UVMap.npz', 'ao_UVMap.png', False, 'body')
lum = R.luminance(g)
cloth_l = [lum[C['cloth']]]
save(pad(g, cov), T / 'm150_basecolor_1k.png'); save(pad(normal, cov), T / 'm150_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'm150_metal_rough_1k.png')
mask = lambda m: ndimage.gaussian_filter(pad(m.astype(float), cov), 0.7)
R.write_mask([mask(C['cloth'])], T / 'm150_region_mask.png', size=N)
Image.fromarray(cls).save(T / 'm150_material_classes.png')
HM = HERE / 'meshy' / 'head_retexture_v2'
if HM.exists():
    hg, hn, hspec, hrgh, hcls, HC, hcov, _ = build(HM, 'uvraster_HeadUV.npz', 'ao_HeadUV.png', True, 'head', ALB)
    hl = R.luminance(hg); cloth_l.append(hl[HC['cloth']])
    save(pad(hg, hcov), T / 'm150_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'm150_head_normal_1k.png')
    save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm150_head_metal_rough_1k.png')
    hmask = lambda m: ndimage.gaussian_filter(pad(m.astype(float), hcov), 0.7)
    R.write_mask([hmask(HC['cloth'])], T / 'm150_head_region_mask.png', size=N)
    Image.fromarray(hcls).save(T / 'm150_head_material_classes.png')
cr = ramps_for('cloth', np.concatenate(cloth_l))
ramps = {k: [cr[k]] for k in PALS}
mats = [{'base': 'M150_A', 'prefix': 'M150', 'mask': 'm150_region_mask.png', 'regions': ['cloth'], 'palettes': PALS, 'ramps': ramps}]
if HM.exists():
    mats.append({'base': 'M150Head_A', 'prefix': 'M150Head', 'mask': 'm150_head_region_mask.png', 'regions': ['cloth'],
                 'palettes': PALS, 'ramps': ramps})
(T / 'm150_ramps.json').write_text(json.dumps({'variants': list(PALS), 'materials': mats}, indent=1) + '\n')
for k in PALS:
    print('RAMP', k, 'cloth mid', [round(x, 3) for x in cr[k]['colors'][8]])
# ---------------------------------------------------------------- props: sword (Meshy maps) and shield (own paint)
P_ = T / 'props'
sb = np.asarray(Image.open(P_ / 'sword_base_color.png').convert('RGB'), np.float64) / 255
sr = np.asarray(Image.open(P_ / 'sword_roughness.png').convert('L'), np.float64) / 255
sh_, ss_, sv_ = hsv(sb)
s_gold = (sh_ > 25) & (sh_ < 65) & (ss_ > 0.35) & (sv_ > 0.3)
s_grip = ~s_gold & (sv_ < 0.25)
sspec = np.where(s_gold, 1.0, np.where(s_grip, 0.35, 0.9))
SP = 512                                                       # a hand prop: 512 px maps (Meshy returns 2K)
small = lambda im: im.resize((SP, SP), Image.LANCZOS)
small(Image.fromarray((np.stack([sspec, np.clip(sr, 0.15, 1), np.zeros_like(sr)], -1) * 255 + 0.5).astype(np.uint8))).save(T / 'm150_sword_metal_rough.png')
small(Image.open(P_ / 'sword_normal.png').convert('RGB')).save(T / 'm150_sword_normal.png')
small(Image.open(P_ / 'sword_base_color.png').convert('RGB')).save(T / 'm150_sword_basecolor.png')
# v2 helmet and shield: Meshy maps (1K); steel (metallic, low saturation) repainted like the body's
PROP_N = 1024
SHARP_SIGMA, SHARP_AMT, NORMAL_GAIN = float(os.environ.get('SHARP_SIGMA', '1.5')), float(os.environ.get('SHARP_AMT', '0.9')), float(os.environ.get('NORMAL_GAIN', '2.0'))


def meshy_prop(name, steel=True):
    base = np.asarray(Image.open(P_ / f'{name}_base_color.png').convert('RGB').resize((PROP_N, PROP_N), Image.LANCZOS), np.float64) / 255
    met = np.asarray(Image.open(P_ / f'{name}_metallic.png').convert('L').resize((PROP_N, PROP_N), Image.LANCZOS), np.float64) / 255
    rgh = np.asarray(Image.open(P_ / f'{name}_roughness.png').convert('L').resize((PROP_N, PROP_N), Image.LANCZOS), np.float64) / 255
    hh, ss, vv = hsv(base)
    gold = (hh > 25) & (hh < 65) & (ss > 0.35) & (vv > 0.3)
    jewel = (hh > 150) & (hh < 200) & (ss > 0.35)
    stl = (ss < 0.3) & (vv > 0.03) & ~gold & ~jewel           # the helmet's steel carries metallic ~0.44 (0.5 missed half)
    if steel and stl.any():
        base = repaint_region(base, stl, STEEL_ALB, mix=0.9)
    jewel = (hh > 150) & (hh < 200) & (ss > 0.35)
    spec = np.where(gold | stl, 1.0, np.where(jewel, 0.9, 0.35))
    # sharper read at game distance (user review: the helmet looked soft): unsharp mask on the base colour (sigma
    # SHARP_SIGMA px, amount SHARP_AMT) and the normal map's slopes x NORMAL_GAIN (Meshy's are shallow), renormalised
    bl = ndimage.gaussian_filter(base, (SHARP_SIGMA, SHARP_SIGMA, 0))
    base = np.clip(base + (base - bl) * SHARP_AMT, 0, 1)
    save(base, T / f'm150_{name}_basecolor.png')
    save(np.stack([spec, np.clip(rgh, 0.15, 1), np.zeros_like(rgh)], -1), T / f'm150_{name}_metal_rough.png')
    nrm = np.asarray(Image.open(P_ / f'{name}_normal.png').convert('RGB').resize((PROP_N, PROP_N), Image.LANCZOS), np.float64) / 255 * 2 - 1
    nrm[..., :2] *= NORMAL_GAIN; nrm /= np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-6)
    save(nrm * 0.5 + 0.5, T / f'm150_{name}_normal.png')
    return int(gold.sum()), int(stl.sum())


hg_, hs_ = meshy_prop('helmet')
sg_, ss2 = meshy_prop('shield', steel=False)                  # the heater's face is dark bronze, not steel
print('PROPS helmet gold/steel texels', hg_, hs_, '| shield gold', sg_)
print('PROPS sword gold texels', int(s_gold.sum()), 'grip', int(s_grip.sum()))
