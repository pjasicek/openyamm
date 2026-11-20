#!/usr/bin/env python3
"""Textures, region masks and tier ramps for m246 (CLAUDE_CREATURE_TEXTURES.md). Run after uv_raster.py (UVMap,
HeadUV at 1024) and bake_ao_natm.py. Head set only when meshy/head_texture_v1 exists.

Tiers (mm7_m246/variants.json: 271 Goblin palette 247 olive, 272 Hobgoblin 248 blue = the art's own palette, 273
Goblin Lord 249 red/brown) recolour TWO regions, as the native masks do: R = the vest (native palette indices
156..180), G = the navy scaled cloth: trousers, right bracer and the left sleeve (indices 181..254). Green skin, hair,
gold/brass, boots and leather stay.
- Classes per texel by colour within pieces (uv_raster.py): vest = piece 3 that is not gold/dark trim; navy = blue hue on
  the body skin shell, bracers and arm plate; skin = green hue on the body shell and hands; gold = saturated yellow;
  hair = the hair and goatee pieces; eyes = pieces 12/13; leather = the rest (boots, belt leather, straps).
- Skin repainted (natm): one albedo (the median of Meshy's skin) x Meshy's fine shading, removing patch-level blotches.
- AO graded into the base colour; ORM red = per-class specular mask (openyamm_specular_mask), green = roughness.
- Ramps per tier from that tier's native pixels of the region's palette indices (stand, walk, attack, all views),
  rank-matched to the region's texel luminance (2nd-98th percentile), gain RAMP_GAIN; mask padded into the gutters.
PREVIEW=1 also writes work/classes_body.png / classes_head.png (class colours in the UV layouts) for render_tex.py.
Writes textures/m246_*."""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
NATIVE = HERE.parent / 'mm7_m246' / 'native'
PALDIR = HERE.parents[2] / 'assets_dev' / 'worlds' / 'mm7' / 'textures'
N = 1024
SKIN_MIX = 0.85; RAMP_GAIN = {'vest': 1.0, 'navy': 1.0}
PALS = {'m246_a': 247, 'm246_b': 248, 'm246_c': 249}
REGION_IDX = None   # m246: the palette entries that differ between the three tiers (green cloth only)
CLASS = {'skin': 1, 'hair': 2, 'vest': 8, 'leather': 8, 'navy': 8, 'gold': 9, 'eye': 6}
SPEC = {'skin': 0.45, 'hair': 0.3, 'vest': 0.3, 'leather': 0.35, 'navy': 0.5, 'gold': 1.0, 'eye': 0.9}
ROUGH = {'skin': 0.5, 'hair': 0.6, 'vest': 0.7, 'leather': 0.6, 'navy': 0.45, 'gold': 0.3, 'eye': 0.2}
PREVIEW_COL = {'skin': (60, 200, 60), 'hair': (150, 40, 20), 'vest': (20, 200, 220), 'leather': (90, 50, 20),
               'navy': (30, 30, 160), 'gold': (250, 210, 0), 'eye': (255, 0, 255)}


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
    """m246: vest = the vest piece (3) without its gold trim and dark edging; navy = blue hue on the body shell (trousers,
    left sleeve), the bracers (7/8) and the left upper-arm plate (11); skin = green hue on the body shell and hands
    (pieces 0, 4, 5); hair = hair and goatee (2, 22); eyes = 12/13; gold = saturated yellow; leather = the rest."""
    h, s, v = hsv(base)
    C = {}
    C['eye'] = cov & np.isin(piece, [12, 13])
    C['gold'] = cov & (h > 28) & (h < 66) & (s > 0.4) & (v > 0.33) & ~C['eye']
    C['hair'] = cov & np.isin(piece, [2, 22]) & ~C['gold']
    C['vest'] = cov & (piece == 3) & ~C['gold']        # the dark scale lines and edging are vest too
    # the chest/back skin under the vest's open sides and V is painted teal by Meshy: teal texels of the body shell
    # above the belt are vest too
    C['vest'] |= cov & (piece == 0) & (h > 160) & (h < 205) & (s > 0.2) & (pos[..., 2] > 0.95) & ~C['gold']
    C['navy'] = cov & np.isin(piece, [0, 7, 8, 11]) & (h >= 205) & (h < 280) & (s > 0.15) & ~C['gold'] & ~C['vest']
    C['skin'] = cov & np.isin(piece, [0, 4, 5]) & (h > 55) & (h < 160) & (s > 0.12) & (v > 0.12) & ~C['gold'] & ~C['navy']
    C['leather'] = cov & ~np.any([m for m in C.values()], axis=0)
    return C


# ---------------------------------------------------------------- native region colours per tier
def pal(i):
    return np.frombuffer(open(PALDIR / f'pal{i:03d}.act', 'rb').read()[:768], np.uint8).reshape(256, 3).astype(np.float64) / 255


BASEP = (pal(248) * 255).astype(int)              # m246: the native sprites are drawn in palette 248 (tier B)
LUT = {tuple(c): i for i, c in enumerate(BASEP)}
frames = sorted(p for p in NATIVE.glob('m246*.png') if p.name[4] in 'saw')
idx_pixels = []
for f in frames:
    a = np.asarray(Image.open(f).convert('RGBA'))
    m = a[..., 3] > 0
    idx_pixels.append(np.array([LUT.get(tuple(c), -1) for c in a[m][:, :3]]))
IDX = np.concatenate(idx_pixels)
REGION_IDX = {'vest': list(range(156, 181)), 'navy': list(range(181, 255))}   # mm7_m246/variants.json regions
native = {}
for reg, ids in REGION_IDX.items():
    sel = IDX[np.isin(IDX, ids)]
    for k, p in PALS.items():
        X = pal(p)[sel]; L = R.luminance(X); keep = L > 0.035
        o = np.argsort(L[keep]); native[(reg, k)] = X[keep][o]
    print('NATIVE', reg, 'pixels', len(sel), {k: np.round(np.median(native[(reg, k)], 0) * 255).tolist() for k in PALS})


def ramps_for(reg, texel_lum, gain=None):
    lo, hi = np.percentile(texel_lum, [2, 98]); srt = np.sort(texel_lum)
    g_ = RAMP_GAIN[reg] if gain is None else gain
    out = {}
    for k in PALS:
        X = native[(reg, k)]; cols = []
        for i in range(16):
            Li = lo + (hi - lo) * i / 15
            q = np.searchsorted(srt, Li) / len(srt)
            c = X[min(len(X) - 1, int(q * (len(X) - 1)))]
            cols.append([round(float(v), 6) for v in np.clip(lin(np.clip(c * g_, 0, 1)), 0, 1)])
        out[k] = {'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols}
    return out


def ramp_mean_lum(r, texel_lum):
    lo, hi = r['range']; c = np.array(r['colors']) @ R.LUMA
    t = np.clip((texel_lum - lo) / (hi - lo), 0, 1) * 15; i = np.minimum(t.astype(int), 14); f = t - i
    return float((c[i] * (1 - f) + c[i + 1] * f).mean())


def calibrated_gain(reg, texel_lum, ref='m246_b'):
    """m246: the HD art (and so the base texture) is the art palette's own tier (248 = B): choose the gain so that tier
    B's ramp keeps the region's mean linear luminance (a fixed 1.3 made the dark navy cloth read pale grey-blue)."""
    a, b = 0.5, 2.0
    for _ in range(30):
        m = (a + b) / 2
        if ramp_mean_lum(ramps_for(reg, texel_lum, m)[ref], texel_lum) > texel_lum.mean():
            b = m
        else:
            a = m
    return (a + b) / 2


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


REGS = ['vest', 'navy']
g, normal, spec, rgh, cls, C, cov, ALB = build(HERE / 'meshy' / 'body_texture_v1', 'uvraster_UVMap.npz', 'ao_UVMap.png', False, 'body')
lum = R.luminance(g)
reg_l = {r: [lum[C[r]]] for r in REGS}
save(pad(g, cov), T / 'm246_basecolor_1k.png'); save(pad(normal, cov), T / 'm246_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'm246_metal_rough_1k.png')
mask = lambda m: ndimage.gaussian_filter(pad(m.astype(float), cov), 0.7)
R.write_mask([mask(C[r]) for r in REGS], T / 'm246_region_mask.png', size=N)
Image.fromarray(cls).save(T / 'm246_material_classes.png')
HM = HERE / 'meshy' / 'head_texture_v1'
if HM.exists():
    hg, hn, hspec, hrgh, hcls, HC, hcov, _ = build(HM, 'uvraster_HeadUV.npz', 'ao_HeadUV.png', True, 'head', ALB)
    hl = R.luminance(hg)
    save(pad(hg, hcov), T / 'm246_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'm246_head_normal_1k.png')
    save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm246_head_metal_rough_1k.png')
    hmask = lambda m: ndimage.gaussian_filter(pad(m.astype(float), hcov), 0.7)
    R.write_mask([hmask(HC[r]) for r in REGS], T / 'm246_head_region_mask.png', size=N)
    Image.fromarray(hcls).save(T / 'm246_head_material_classes.png')
# m246: RAMP_GAIN 1.0 (the native colours as they are). The guide's 1.3x made the dark scaled navy read pale grey-blue
# in the viewer next to the native; the Meshy base itself is darker still (calibrated_gain, matching tier B to the base,
# gives 0.61 vest / 0.52 navy - too dark against the sprite). Reported, not used.
GAIN = {r: RAMP_GAIN[r] for r in REGS}
print('GAIN used', GAIN, 'base-matched (reference only)', {r: round(calibrated_gain(r, np.concatenate(reg_l[r])), 3) for r in REGS})
rr = {r: ramps_for(r, np.concatenate(reg_l[r]), GAIN[r]) for r in REGS}
ramps = {k: [rr[r][k] for r in REGS] for k in PALS}
mats = [{'base': 'M246_A', 'prefix': 'M246', 'mask': 'm246_region_mask.png', 'regions': REGS, 'palettes': PALS, 'ramps': ramps}]
if HM.exists():
    mats.append({'base': 'M246Head_A', 'prefix': 'M246Head', 'mask': 'm246_head_region_mask.png', 'regions': REGS,
                 'palettes': PALS, 'ramps': ramps})
(T / 'm246_ramps.json').write_text(json.dumps({'variants': list(PALS), 'materials': mats}, indent=1) + '\n')
for k in PALS:
    print('RAMP', k, {r: [round(x, 3) for x in rr[r][k]['colors'][8]] for r in REGS})
# ---------------------------------------------------------------- sword surface maps (its own material, no tier region)
sb = np.asarray(Image.open(T / 'props' / 'sword_basecolor.png').convert('RGB'), np.float64) / 255
sh_, ss_, sv_ = hsv(sb)
s_gold = (sh_ > 30) & (sh_ < 65) & (ss_ > 0.4) & (sv_ > 0.35)
s_grip = ~s_gold & (ss_ > 0.25) & (sv_ < 0.5)
sspec = np.where(s_gold, 1.0, np.where(s_grip, 0.35, 0.85)); srgh = np.where(s_gold, 0.3, np.where(s_grip, 0.65, 0.28))
save(np.stack([sspec, srgh, np.zeros_like(srgh)], -1), T / 'm246_sword_metal_rough.png')
save(np.dstack([np.full(sb.shape[:2], 0.5), np.full(sb.shape[:2], 0.5), np.ones(sb.shape[:2])]), T / 'm246_sword_normal.png')
Image.fromarray((sb * 255 + 0.5).astype(np.uint8)).save(T / 'm246_sword_basecolor.png')
print('SWORD maps: gold texels', int(s_gold.sum()), 'grip', int(s_grip.sum()))
