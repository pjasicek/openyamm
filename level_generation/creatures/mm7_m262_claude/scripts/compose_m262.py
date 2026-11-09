#!/usr/bin/env python3
"""Textures, region masks and tier ramps for m262 (CLAUDE_CREATURE_TEXTURES.md), from mm7_m150_claude/compose_m150.py.
Run after uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py. Head set from meshy/head_retexture_v1.

Tiers (mm7_m262/variants.json: 283 Harpy 263 (the sprites' own palette), 284 Harpy Hag 264, 285 Harpy Queen 56)
recolour TWO regions, as the native masks do (mm7_m262/manifest.json 'regions'): R = flight_feathers (palette indices
162..236: teal -> violet -> magenta), G = metal_inserts (121..140: the teal bracers and the bodice's teal band).
Skin, silver hair, silver bodice cups, gold, the brown coverts and thigh feathers, the orange legs and talons stay.
- Classes per texel: feather = the wing garment (5) and the tail/thigh feathers; flight = teal-green texels of the wing
  garment (region R); insert = teal texels outside the wings (region G); gold = saturated yellow; steel = low
  saturation (bodice cups, hair in the body set); skin = warm texels of the skin pieces; claw = the orange legs and
  dark talons (pieces 1/2); eyes = pieces 13/14; hair = the hair pieces in the head set.
- Skin repainted (natm): one albedo x Meshy's fine shading. AO graded into the base colour; ORM red = per-class
  specular mask, green = roughness. Ramps per tier from that tier's native pixels of the region's palette indices,
  rank-matched to the region's texel luminance (2nd-98th percentile); masks padded into the gutters.
- Prop: the Meshy knife keeps its maps (ORM red from its colour classes, green its roughness).
Writes textures/m262_*."""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
_L = json.load(open(Path(__file__).resolve().parents[1] / 'work' / 'part_labels.json'))
HAIR = [int(k) for k, v in _L.items() if v == 'hair']
T = HERE / 'textures'; T.mkdir(exist_ok=True)
NATIVE = HERE.parent / 'mm7_m262' / 'native'
PALDIR = HERE.parents[2] / 'assets_dev' / 'worlds' / 'mm7' / 'textures'
N = 1024
SKIN_MIX = 0.85; RAMP_GAIN = {'flight': 1.15, 'insert': 1.3}
PALS = {'m262_a': 263, 'm262_b': 264, 'm262_c': 56}
REGION_IDX = None
CLASS = {'skin': 1, 'hair': 2, 'flight': 2, 'insert': 9, 'leather': 2, 'gold': 9, 'steel': 9, 'eye': 6, 'feather': 2, 'claw': 4}
SPEC = {'skin': 0.45, 'hair': 0.3, 'flight': 0.3, 'insert': 0.8, 'leather': 0.2, 'gold': 1.0, 'steel': 0.8, 'eye': 0.9, 'feather': 0.2, 'claw': 0.5}
ROUGH = {'skin': 0.5, 'hair': 0.6, 'flight': 0.6, 'insert': 0.35, 'leather': 0.8, 'gold': 0.3, 'steel': 0.35, 'eye': 0.2, 'feather': 0.8, 'claw': 0.45}
PREVIEW_COL = {'skin': (230, 170, 140), 'hair': (150, 90, 20), 'flight': (20, 200, 160), 'insert': (0, 120, 255),
               'leather': (90, 50, 20), 'feather': (140, 100, 60), 'gold': (250, 210, 0), 'steel': (180, 180, 190),
               'eye': (255, 0, 255), 'claw': (255, 120, 0)}


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


def classify(base, gar, pos, cov, head_layout, piece):
    h, s, v = hsv(base)
    C = {}
    teal = (h > 140) & (h < 205) & (s > 0.22) & (v > 0.12)
    C['flight'] = cov & (gar == 5) & teal
    C['feather'] = cov & ((gar == 5) | (gar == 7)) & ~C['flight']
    C['eye'] = cov & np.isin(piece, [13, 14])
    C['claw'] = cov & np.isin(piece, [1, 2])
    rest = cov & ~C['flight'] & ~C['feather'] & ~C['eye'] & ~C['claw']
    C['insert'] = rest & teal
    C['gold'] = rest & (h > 30) & (h < 62) & (s > 0.45) & (v > 0.40) & ~C['insert']
    C['steel'] = rest & (s < 0.18) & ~C['insert']
    C['hair'] = (rest & np.isin(piece, HAIR) & ~C['gold']) if head_layout else np.zeros_like(cov)
    C['steel'] &= ~C['hair']
    warm = rest & ((h < 50) | (h > 330)) & ~C['gold'] & ~C['steel'] & ~C['insert'] & ~C['hair']
    C['skin'] = warm & np.isin(piece, [0, 3, 4]) & (s > 0.12) & (s < 0.8) & (v > 0.2)
    C['leather'] = cov & ~np.any([m for m in C.values()], axis=0)
    return C


# ---------------------------------------------------------------- native region colours per tier
def pal(i):
    return np.frombuffer(open(PALDIR / f'pal{i:03d}.act', 'rb').read()[:768], np.uint8).reshape(256, 3).astype(np.float64) / 255


BASEP = (pal(263) * 255).astype(int)              # the native sprites are drawn in palette 263 (tier A, exact bypass)
LUT = {tuple(c): i for i, c in enumerate(BASEP)}
frames = sorted(p for p in NATIVE.glob('m262*.png') if p.name[4] in 'wan')
idx_pixels = []
for f in frames:
    a = np.asarray(Image.open(f).convert('RGBA'))
    m = a[..., 3] > 0
    idx_pixels.append(np.array([LUT.get(tuple(c), -1) for c in a[m][:, :3]]))
IDX = np.concatenate(idx_pixels)
import colorsys
REG = {r['name']: r['palette_indices'] for r in json.load(open(HERE.parent / 'mm7_m262' / 'manifest.json'))['regions']}
dif = np.array(REG['flight_feathers'])
REGION_IDX = {'flight': REG['flight_feathers'], 'insert': REG['metal_inserts']}
print('REGION palette indices', {k: (len(v), min(v), max(v)) for k, v in REGION_IDX.items()})
native = {}
for reg, ids in REGION_IDX.items():
    sel = IDX[np.isin(IDX, ids)]
    for k, p in PALS.items():
        X = pal(p)[sel]; L = R.luminance(X); keep = L > 0.035
        o = np.argsort(L[keep]); native[(reg, k)] = X[keep][o]
    print('NATIVE', reg, 'pixels', len(sel), {k: np.round(np.median(native[(reg, k)], 0) * 255).tolist() for k in PALS})


def ramps_for(reg, texel_lum):
    """index correspondence: the region's native pixels sorted by their tier-A luminance; stop i takes the pixels at the
    texel-luminance quantile of stop i (a window of 1/32 of them) and averages THE SAME palette indices in each tier's
    palette (rank-matching each tier on its own luminance put a grey index at tier C's mid stop)"""
    lo, hi = np.percentile(texel_lum, [2, 98]); srt = np.sort(texel_lum)
    sel = IDX[np.isin(IDX, REGION_IDX[reg])]
    A0 = list(PALS.values())[0]
    LA = R.luminance(pal(A0)[sel]); keep = LA > 0.035
    sel = sel[keep][np.argsort(LA[keep])]; n = len(sel); w = max(1, n // 64)
    out = {}
    for k, p in PALS.items():
        cols = []
        for i in range(16):
            Li = lo + (hi - lo) * i / 15
            q = np.searchsorted(srt, Li) / len(srt); j = int(q * (n - 1))
            c = pal(p)[sel[max(0, j - w):j + w + 1]].mean(0)
            cols.append([round(float(v), 6) for v in np.clip(lin(np.clip(c * RAMP_GAIN[reg], 0, 1)), 0, 1)])
        out[k] = {'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols}
    return out


def build(meshy_dir, raster, ao_png, head_layout, tag, albedo=None):
    base = load(meshy_dir / 'texture_urls_0_base_color.png'); normal = load(meshy_dir / 'texture_urls_0_normal.png')
    rough_m = load(meshy_dir / 'texture_urls_0_roughness.png', 'L')
    Rz = np.load(HERE / 'work' / raster); gar, pos = Rz['garment'], Rz['pos']; cov = gar >= 0
    C = classify(base, gar, pos, cov, head_layout, Rz['piece'])
    if os.environ.get('PREVIEW'):
        pv = np.zeros((N, N, 3), np.uint8)
        for k, m in C.items():
            pv[m] = PREVIEW_COL[k]
        Image.fromarray(pv).save(HERE / 'work' / f'classes_{tag}.png')
    if albedo is None:                                     # the head reuses the body's albedo: no neck seam
        albedo = np.median(base[C['skin']], 0) if C['skin'].sum() > 100 else np.array([0.85, 0.65, 0.55])
    g = repaint_skin(base, C['skin'], albedo)
    g = ao_grade(g, load(HERE / 'work' / ao_png, 'L'), cov)
    print('CLASSES', tag, {k: int(m.sum()) for k, m in C.items()}, 'covered', int(cov.sum()),
          'skin albedo', np.round(albedo * 255).tolist())
    cls = np.zeros((N, N), np.uint8); spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8)
    for k, m in C.items():
        if m.any():
            cls[m] = CLASS[k]; spec[m] = SPEC[k]; rgh[m] = np.clip(ROUGH[k] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
    return g, normal, spec, rgh, cls, C, cov, albedo


cfg_ramps = {}
g, normal, spec, rgh, cls, C, cov, ALB = build(HERE / 'meshy' / 'retexture_v1', 'uvraster_UVMap.npz', 'ao_UVMap.png', False, 'body')
lum = R.luminance(g)
reg_l = {'flight': [lum[C['flight']]], 'insert': [lum[C['insert']]]}
save(pad(g, cov), T / 'm262_basecolor_1k.png'); save(pad(normal, cov), T / 'm262_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'm262_metal_rough_1k.png')
mask = lambda m: ndimage.gaussian_filter(pad(m.astype(float), cov), 0.7)
R.write_mask([mask(C['flight']), mask(C['insert'])], T / 'm262_region_mask.png', size=N)
Image.fromarray(cls).save(T / 'm262_material_classes.png')
HM = HERE / 'meshy' / 'head_retexture_v1'
if HM.exists():
    hg, hn, hspec, hrgh, hcls, HC, hcov, _ = build(HM, 'uvraster_HeadUV.npz', 'ao_HeadUV.png', True, 'head', ALB)
    hl = R.luminance(hg)
    for k_ in reg_l:
        if HC[k_].sum() > 50:
            reg_l[k_].append(hl[HC[k_]])
    save(pad(hg, hcov), T / 'm262_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'm262_head_normal_1k.png')
    save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm262_head_metal_rough_1k.png')
    hmask = lambda m: ndimage.gaussian_filter(pad(m.astype(float), hcov), 0.7)
    R.write_mask([hmask(HC['flight']), hmask(HC['insert'])], T / 'm262_head_region_mask.png', size=N)
    Image.fromarray(hcls).save(T / 'm262_head_material_classes.png')
rr = {k_: ramps_for(k_, np.concatenate(v_)) for k_, v_ in reg_l.items()}
ramps = {k: [rr['flight'][k], rr['insert'][k]] for k in PALS}
mats = [{'base': 'M262_A', 'prefix': 'M262', 'mask': 'm262_region_mask.png', 'regions': ['flight', 'insert'], 'palettes': PALS, 'ramps': ramps}]
if HM.exists():
    mats.append({'base': 'M262Head_A', 'prefix': 'M262Head', 'mask': 'm262_head_region_mask.png', 'regions': ['flight', 'insert'],
                 'palettes': PALS, 'ramps': ramps})
(T / 'm262_ramps.json').write_text(json.dumps({'variants': list(PALS), 'materials': mats}, indent=1) + '\n')
for k in PALS:
    print('RAMP', k, {k_: [round(x, 3) for x in rr[k_][k]['colors'][8]] for k_ in rr})
# ---------------------------------------------------------------- prop: the Meshy knife (its own maps)
P_ = T / 'props'
sb = np.asarray(Image.open(P_ / 'sword_base_color.png').convert('RGB'), np.float64) / 255
sr = np.asarray(Image.open(P_ / 'sword_roughness.png').convert('L'), np.float64) / 255
sh_, ss_, sv_ = hsv(sb)
s_gold = (sh_ > 25) & (sh_ < 65) & (ss_ > 0.35) & (sv_ > 0.3)
s_grip = ~s_gold & (sv_ < 0.25)
sspec = np.where(s_gold, 1.0, np.where(s_grip, 0.35, 0.9))
SP = 512                                                       # a hand prop: 512 px maps (Meshy returns 2K)
small = lambda im: im.resize((SP, SP), Image.LANCZOS)
small(Image.fromarray((np.stack([sspec, np.clip(sr, 0.15, 1), np.zeros_like(sr)], -1) * 255 + 0.5).astype(np.uint8))).save(T / 'm262_sword_metal_rough.png')
small(Image.open(P_ / 'sword_normal.png').convert('RGB')).save(T / 'm262_sword_normal.png')
small(Image.open(P_ / 'sword_base_color.png').convert('RGB')).save(T / 'm262_sword_basecolor.png')
print('PROPS knife gold texels', int(s_gold.sum()), 'grip', int(s_grip.sum()))
