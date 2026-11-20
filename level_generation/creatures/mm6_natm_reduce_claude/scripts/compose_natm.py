#!/usr/bin/env python3
"""Textures, region masks and tier ramps for natm (CLAUDE_CREATURE_TEXTURES.md). Run after uv_raster.py (UVMap,
HeadUV at 1024) and bake_ao_natm.py.

Tiers (palettes 795 Cannibal grey / 796 Head Hunter olive / 797 Witch Doctor red; dsft.bin palette ids) recolour ONE region, as the native
shared R8 mask does: the loincloth panels and belt, the arm bands, the olive bindings on the leg guards, the spear's
bindings and the buckler's painted leather. Skin, feathers, bone beads, the gold collar, wood and steel stay.
- Skin (body + head): Meshy painted face-sized patches from salmon to dark brown (codex model: too dark and plastic).
  Every skin texel is repainted with one albedo SKIN (between the native sprite skin x1.35 and the HD masters) times
  Meshy's fine shading: luminance / its masked blur (6 px), so patch-level brightness goes and pores, muscles and
  creases stay; mixed 85 % over Meshy's colour. Body and head use the same albedo, so the neck seam matches.
- Gold collar: skin texels at the neck base in gold hues are kept as painted.
- AO (work/ao_*.png) multiplied into every base colour (strength 0.5, floor 0.4) and written to ORM red is NOT done:
  the runtime reads ORM red as a per-class specular mask (openyamm_specular_mask), so R = specular class value.
- Ramps per tier from the native frames (stand, walk, attack; pixels that differ between the three palettes = the
  recolour region; near-black outline pixels dropped), rank-matched to each material's region texel luminance
  (2nd-98th percentile range), gain RAMP_GAIN (sprites carry baked shading).
Writes textures/natm_*."""
import json, os, sys, colorsys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
NATIVE = HERE.parent / 'mm6_natm' / 'native_variants'
N = 1024
SKIN = np.array([134, 86, 52]) / 255           # sRGB albedo
SKIN_MIX = 0.85; RAMP_GAIN = 1.25
PALS = {'natm_a': 795, 'natm_b': 796, 'natm_c': 797}   # dsft.bin: natmsta 795, nBtmsta 796, nCtmsta 797
SPEC = {'skin': 0.45, 'feather': 0.12, 'cloth': 0.25, 'gold': 1.0, 'bead': 0.55, 'eye': 0.9}
ROUGH = {'skin': 0.55, 'feather': 0.9, 'cloth': 0.85, 'gold': 0.3, 'bead': 0.5, 'eye': 0.2}


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


def repaint_skin(img, m, sigma=6.0):
    """One albedo x fine shading (luminance over its masked blur) on the texels m, mixed SKIN_MIX over the original."""
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


# ---------------------------------------------------------------- native recolour colours per tier
FR = ['natmsta0', 'natmsta1', 'natmsta2', 'natmsta3', 'natmsta4', 'natmata0', 'natmatc0', 'natmatd0', 'natmwaa0', 'natmwac0']
native = {k: [] for k in PALS}
for f in FR:
    ims = {k: np.asarray(Image.open(NATIVE / f'{f}_{p}.png').convert('RGBA')).astype(np.float64) / 255 for k, p in PALS.items()}
    al = ims['natm_a'][..., 3] > 0.5
    d = (np.abs(ims['natm_a'][..., :3] - ims['natm_b'][..., :3]).sum(-1) > 0.02) | (np.abs(ims['natm_a'][..., :3] - ims['natm_c'][..., :3]).sum(-1) > 0.02)
    for k in PALS:
        native[k].append(ims[k][al & d][:, :3])
for k in PALS:
    X = np.concatenate(native[k]); L = R.luminance(X); X, L = X[L > 0.035], L[L > 0.035]
    o = np.argsort(L); native[k] = (X[o], L[o])


def ramps_for(texel_lum):
    lo, hi = np.percentile(texel_lum, [2, 98]); srt = np.sort(texel_lum)
    out = {}
    for k in PALS:
        X, _ = native[k]; cols = []
        for i in range(16):
            Li = lo + (hi - lo) * i / 15
            q = np.searchsorted(srt, Li) / len(srt)
            c = X[min(len(X) - 1, int(q * (len(X) - 1)))]
            cols.append([round(float(v), 6) for v in np.clip(lin(np.clip(c * RAMP_GAIN, 0, 1)), 0, 1)])
        out[k] = [{'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols}]
    return out


# ---------------------------------------------------------------- body set
M = HERE / os.environ.get('BODY_JOB', 'meshy/body_retexture_r55')   # reduce project: job dirs by env
base = load(M / 'texture_urls_0_base_color.png'); normal = load(M / 'texture_urls_0_normal.png')
rough_m = load(M / 'texture_urls_0_roughness.png', 'L')
Rz = np.load(HERE / 'work' / 'uvraster_UVMap.npz'); gar, pos = Rz['garment'], Rz['pos']; cov = gar >= 0
hue, sat, val = hsv(base)
olive = (hue > 40) & (hue < 110) & (sat > 0.22) & (val > 0.12)
skin = cov & (gar == 0)
gold = skin & (pos[..., 2] > 1.30) & (pos[..., 2] < 1.47) & (hue > 28) & (hue < 62) & (sat > 0.3) & (val > 0.35)
gold = ndimage.binary_dilation(gold, iterations=1) & skin & (pos[..., 2] > 1.30) & (pos[..., 2] < 1.47)
skin &= ~gold
# pendants: the Smart Topology mesh fused the necklace and hip-trim pendants to the skin piece, so garments.py labels
# them skin and the repaint turned Meshy's ivory bone into pale skin strips (h65 review). Skin texels Meshy painted
# ivory (sat < 0.3, val > 0.55, components >= 6 texels) become bead: below the chest (z < 1.30, also covers feather paint
# hidden under the hip trim and leg guards) and in a narrow box over the chest pendants. Ivory paint at the mantle edge
# stays skin (paint bleed on visible shoulders).
ivory = skin & (sat < 0.3) & (val > 0.55)
lab_, n_ = ndimage.label(ivory); sz_ = ndimage.sum(ivory, lab_, range(1, n_ + 1))
ivory = np.isin(lab_, np.where(sz_ >= 6)[0] + 1)
px, py, pz = pos[..., 0], pos[..., 1], pos[..., 2]
ivory &= (pz < 1.30) | ((pz < 1.43) & (np.abs(px) < 0.11) & (py < -0.05))
ivory = ndimage.binary_dilation(ivory, iterations=1) & skin & (sat < 0.4)
skin &= ~ivory
print('IVORY skin texels kept as bead', int(ivory.sum()))
cloth = cov & (np.isin(gar, [5, 6, 7]) | (np.isin(gar, [2, 3, 4]) & olive))
feather = cov & np.isin(gar, [1, 2, 3, 4]) & ~cloth
bead = (cov & np.isin(gar, [8, 9])) | ivory
g = repaint_skin(base, skin)
ao = load(HERE / 'work' / 'ao_UVMap.png', 'L')
g = ao_grade(g, ao, cov)
print('CLASSES body texels', {n: int(m.sum()) for n, m in (('skin', skin), ('gold', gold), ('cloth', cloth), ('feather', feather), ('bead', bead), ('covered', cov))})
print('MEDIANS body: feather', np.round(np.median(base[feather], 0) * 255), 'cloth', np.round(np.median(base[cloth], 0) * 255),
      'skin before', np.round(np.median(base[skin], 0) * 255), 'after', np.round(np.median(g[skin], 0) * 255))
cls = np.zeros((N, N), np.uint8); spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8)
for name, m, c in (('skin', skin, 1), ('gold', gold, 9), ('cloth', cloth, 8), ('feather', feather, 2), ('bead', bead, 5)):
    cls[m] = c; spec[m] = SPEC[name]; rgh[m] = np.clip(ROUGH[name] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
cloth_ramps = ramps_for(R.luminance(g[cloth]))
save(pad(g, cov), T / 'natm_basecolor_1k.png'); save(pad(normal, cov), T / 'natm_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'natm_metal_rough_1k.png')
R.write_mask([ndimage.gaussian_filter(pad(cloth.astype(float), cov), 0.7)], T / 'natm_region_mask.png', size=N)
Image.fromarray(cls).save(T / 'natm_material_classes.png')
# ---------------------------------------------------------------- head set
HM = HERE / os.environ.get('HEAD_JOB', 'meshy/head_retexture_r55')
hb = load(HM / 'texture_urls_0_base_color.png'); hn = load(HM / 'texture_urls_0_normal.png'); hr_m = load(HM / 'texture_urls_0_roughness.png', 'L')
Rh = np.load(HERE / 'work' / 'uvraster_HeadUV.npz'); hg_, hpos = Rh['garment'], Rh['pos']; hcov = hg_ >= 0
hh, hs, hv = hsv(hb)
eye = hcov & (hg_ == 9)
hskin = hcov & (hg_ == 0) & (hs > 0.18) & ((hh < 45) | (hh > 340)) & (hv > 0.08)
hgr = ao_grade(repaint_skin(hb, hskin), load(HERE / 'work' / 'ao_HeadUV.png', 'L'), hcov, strength=0.4)
print('CLASSES head texels', {'skin': int(hskin.sum()), 'eye': int(eye.sum()), 'covered': int(hcov.sum())},
      'skin before', np.round(np.median(hb[hskin], 0) * 255), 'after', np.round(np.median(hgr[hskin], 0) * 255))
hspec = np.where(hskin, SPEC['skin'], 0.3); hspec[eye] = SPEC['eye']
hrgh = np.where(hskin, ROUGH['skin'], 0.6); hrgh[eye] = ROUGH['eye']
save(pad(hgr, hcov), T / 'natm_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'natm_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'natm_head_metal_rough_1k.png')
hc = np.zeros((N, N), np.uint8); hc[hcov] = 11; hc[hskin] = 1; hc[eye] = 6
Image.fromarray(hc).save(T / 'natm_head_material_classes.png')
# ---------------------------------------------------------------- props (own textures, same ramps by their own luminance)
P = HERE / 'textures' / 'props'
sp = np.asarray(Image.open(P / 'spear.png').convert('RGB'), np.float64) / 255
sh, ss, sv = hsv(sp)
sp_mask = (sh > 40) & (sh < 110) & (ss > 0.25) & (sv > 0.12)
bk = np.asarray(Image.open(P / 'buckler_atlas.png').convert('RGB'), np.float64) / 255
bh, bs, bv = hsv(bk)
bk_mask = (bh > 35) & (bh < 110) & (bs > 0.2) & (np.arange(bk.shape[1])[None, :] < bk.shape[1] // 2)
save(sp, T / 'natm_spear_basecolor.png'); save(bk, T / 'natm_buckler_basecolor.png')
R.write_mask([ndimage.gaussian_filter(sp_mask.astype(float), 0.7)], T / 'natm_spear_region_mask.png', size=None) if False else None
Image.fromarray((ndimage.gaussian_filter(sp_mask.astype(float), 0.7) * 255).astype(np.uint8)).convert('RGBA').save(T / 'natm_spear_region_mask.png')
mk = np.zeros(bk.shape[:2] + (4,), np.uint8); mk[..., 0] = (ndimage.gaussian_filter(bk_mask.astype(float), 0.7) * 255).astype(np.uint8)
Image.fromarray(mk).save(T / 'natm_buckler_region_mask.png')
mk = np.zeros(sp.shape[:2] + (4,), np.uint8); mk[..., 0] = (ndimage.gaussian_filter(sp_mask.astype(float), 0.7) * 255).astype(np.uint8)
Image.fromarray(mk).save(T / 'natm_spear_region_mask.png')
spear_ramps = ramps_for(R.luminance(sp[sp_mask])); buck_ramps = ramps_for(R.luminance(bk[bk_mask]))
print('PROPS mask texels spear', int(sp_mask.sum()), 'buckler', int(bk_mask.sum()))
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Natm_A', 'prefix': 'Natm', 'mask': 'natm_region_mask.png', 'regions': ['cloth'], 'palettes': PALS, 'ramps': cloth_ramps},
                     {'base': 'Spear_A', 'prefix': 'Spear', 'mask': 'natm_spear_region_mask.png', 'regions': ['bindings'], 'palettes': PALS, 'ramps': spear_ramps},
                     {'base': 'Buckler_A', 'prefix': 'Buckler', 'mask': 'natm_buckler_region_mask.png', 'regions': ['paint'], 'palettes': PALS, 'ramps': buck_ramps}]}
(T / 'natm_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
for k in PALS:
    print('RAMP', k, 'cloth', [round(x, 3) for x in cloth_ramps[k][0]['colors'][8]], 'range', cloth_ramps[k][0]['range'])
