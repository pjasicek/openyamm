#!/usr/bin/env python3
"""Textures, region mask and tier ramps for the m242 ghost (CLAUDE_CREATURE_TEXTURES.md). Run after uv_raster.py
(UVMap, HeadUV at 1024; the 'garment' raster carries the cloth flag) and bake_ao_natm.py.

Tiers (mm7_m242/variants.json: 268 Shade palette 243 grey-white, 269 Specter 244 brown (the native art), 270 Ghost 245
near-black) recolour ONE region, as the native mask does: R = the robe (every cloth texel: hood, cape and shreds).
The yellowed bone, the black sockets and the teeth stay in every tier.
- Classes by PIECE (raster), not by colour: cloth pieces -> cloth, bone pieces -> bone. Meshy projected some paint
  across the two (ivory on shreds in front of the ribs, brown on bones behind the robe): cloth texels in bone colours
  and bone texels in cloth colours are repainted with their class albedo x their own fine shading.
- AO graded into the base colour; ORM red = per-class specular mask (openyamm_specular_mask), green = roughness.
- Ramps per tier from that tier's native pixels of the robe's palette indices (manifest recolour indices 84..250, the
  warm brown entries), rank-matched to the robe texels' luminance (2nd-98th percentile), gain RAMP_GAIN; the mask is
  padded into the gutters.
Writes textures/m242_*."""
import json, os, sys, colorsys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
NATIVE = HERE.parent / 'mm7_m242' / 'native'
PALDIR = HERE.parents[2] / 'assets_dev' / 'worlds' / 'mm7' / 'textures'
N = 1024
RAMP_GAIN = float(os.environ.get('RAMP_GAIN', '1.3'))
PALS = {'m242_a': 243, 'm242_b': 244, 'm242_c': 245}
CLASS = {'cloth': 8, 'bone': 5}
SPEC = {'cloth': 0.15, 'bone': 0.4}
ROUGH = {'cloth': 0.9, 'bone': 0.55}


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


def repaint(img, m, region, albedo, sigma=6.0):
    """texels m take albedo x their fine shading (luminance over its blur within region)"""
    L = R.luminance(img)
    num = ndimage.gaussian_filter(np.where(region, L, 0.0), sigma); den = ndimage.gaussian_filter(region.astype(float), sigma)
    Lb = num / np.maximum(den, 1e-4)
    detail = np.clip(L / np.maximum(Lb, 1e-4), 0.6, 1.4)
    out = img.copy(); out[m] = srgb(np.clip(lin(albedo)[None, :] * detail[m][:, None], 0, 1))
    return out


def ao_grade(img, ao, cov, strength=0.45, floor=0.4):
    f = np.clip(1 - strength + strength * np.maximum(ao, floor), 0, 1)
    out = img.copy(); out[cov] = img[cov] * f[cov][:, None]; return out


def pal(i):
    return np.frombuffer(open(PALDIR / f'pal{i:03d}.act', 'rb').read()[:768], np.uint8).reshape(256, 3).astype(np.float64) / 255


BASEP = (pal(244) * 255).astype(int)                     # the native art is drawn in palette 244
LUT = {tuple(c): i for i, c in enumerate(BASEP)}
MAN = json.load(open(HERE.parent / 'mm7_m242' / 'manifest.json'))['recolor']['native_indices']
_h = np.array([colorsys.rgb_to_hsv(*c) for c in pal(244)])
ROBE_IDX = [i for i in MAN if _h[i, 0] < 0.1 and _h[i, 1] > 0.25]   # warm brown entries (bone ivory is yellow-green)
frames = sorted(p for p in NATIVE.glob('m242*.png') if p.name[4] in 'saw')
IDX = np.concatenate([np.array([LUT.get(tuple(c), -1) for c in np.asarray(Image.open(f).convert('RGBA'))[..., :3][
    np.asarray(Image.open(f).convert('RGBA'))[..., 3] > 0]]) for f in frames])
sel = IDX[np.isin(IDX, ROBE_IDX)]
native = {}
for k, p in PALS.items():
    X = pal(p)[sel]; L = R.luminance(X); keep = L > 0.02
    native[k] = X[keep][np.argsort(L[keep])]
print('REGION robe palette indices', len(ROBE_IDX), 'native pixels', len(sel),
      {k: np.round(np.median(v, 0) * 255).tolist() for k, v in native.items()})


def build(meshy_dir, raster, ao_png, tag, alb=None):
    base = load(meshy_dir / 'texture_urls_0_base_color.png'); normal = load(meshy_dir / 'texture_urls_0_normal.png')
    rough_m = load(meshy_dir / 'texture_urls_0_roughness.png', 'L')
    Rz = np.load(HERE / 'work' / raster); gar = Rz['garment']; cov = gar >= 0
    C = {'cloth': cov & (gar == 1), 'bone': cov & (gar == 0)}
    h, s, v = hsv(base)
    ivory = (h > 28) & (h < 70) & (s < 0.55) & (v > 0.5)
    brown = ((h < 28) | (h > 330)) & (s > 0.3) & (v < 0.45) & (v > 0.2)          # the black sockets stay
    if alb is None:
        alb = {'cloth': np.median(base[C['cloth'] & ~ivory], 0), 'bone': np.median(base[C['bone'] & ivory], 0)}
    g = repaint(base, C['cloth'] & ivory, C['cloth'], alb['cloth'])
    g = repaint(g, C['bone'] & brown, C['bone'], alb['bone'])
    g = ao_grade(g, load(HERE / 'work' / ao_png, 'L'), cov)
    print('CLASSES', tag, {k: int(m.sum()) for k, m in C.items()}, 'repainted cloth', int((C['cloth'] & ivory).sum()),
          'bone', int((C['bone'] & brown).sum()), 'albedo', {k: np.round(a * 255).tolist() for k, a in alb.items()})
    cls = np.zeros((N, N), np.uint8); spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8)
    for k, m in C.items():
        cls[m] = CLASS[k]; spec[m] = SPEC[k]; rgh[m] = np.clip(ROUGH[k] + (rough_m[m] - np.median(rough_m[m])) * 0.4, 0.1, 1)
    return g, normal, spec, rgh, cls, C, cov, alb


def ramps_for(texel_lum):
    lo, hi = np.percentile(texel_lum, [2, 98]); srt = np.sort(texel_lum)
    out = {}
    for k in PALS:
        X = native[k]; cols = []
        for i in range(16):
            Li = lo + (hi - lo) * i / 15
            q = np.searchsorted(srt, Li) / len(srt)
            c = X[min(len(X) - 1, int(q * (len(X) - 1)))]
            cols.append([round(float(v), 6) for v in np.clip(lin(np.clip(c * RAMP_GAIN, 0, 1)), 0, 1)])
        out[k] = {'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols}
    return out


mask = lambda m, cov: ndimage.gaussian_filter(pad(m.astype(float), cov), 0.7)
g, normal, spec, rgh, cls, C, cov, ALB = build(HERE / 'meshy' / 'retexture_v1', 'uvraster_UVMap.npz', 'ao_UVMap.png', 'body')
lums = [R.luminance(g)[C['cloth']]]
save(pad(g, cov), T / 'm242_basecolor_1k.png'); save(pad(normal, cov), T / 'm242_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'm242_metal_rough_1k.png')
R.write_mask([mask(C['cloth'], cov)], T / 'm242_region_mask.png', size=N)
Image.fromarray(cls).save(T / 'm242_material_classes.png')
HM = HERE / 'meshy' / 'head_retexture_v1'
hg, hn, hspec, hrgh, hcls, HC, hcov, _ = build(HM, 'uvraster_HeadUV.npz', 'ao_HeadUV.png', 'head', ALB)   # one albedo: no neck seam
lums.append(R.luminance(hg)[HC['cloth']])
# black hollow sockets and nasal opening (native): Smart Topology closed them with lid-like bumps that the head
# retexture painted grey. Located on the skull's front depth map (work: z 1.690 for the eyes, 3 cm either side of the
# midline x -0.008; the nose bump at z 1.655), painted as soft dark ellipses on the skull's front texels.
Hz = np.load(HERE / 'work' / 'uvraster_HeadUV.npz'); hp, hpos = Hz['piece'], Hz['pos']
front = (hp == 0) & (hpos[..., 1] < -0.19)
dark = np.zeros((N, N))
for cx, cz, rx, rz in ((-0.038, 1.687, 0.021, 0.019), (0.022, 1.687, 0.021, 0.019), (-0.008, 1.652, 0.009, 0.014)):
    d = np.sqrt(((hpos[..., 0] - cx) / rx) ** 2 + ((hpos[..., 2] - cz) / rz) ** 2)
    dark = np.maximum(dark, np.clip(1.4 - d, 0, 1) * front)
hg = hg * (1 - 0.96 * dark[..., None])
print('SOCKETS painted texels', int((dark > 0.5).sum()))
save(pad(hg, hcov), T / 'm242_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'm242_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm242_head_metal_rough_1k.png')
R.write_mask([mask(HC['cloth'], hcov)], T / 'm242_head_region_mask.png', size=N)
Image.fromarray(hcls).save(T / 'm242_head_material_classes.png')
rr = ramps_for(np.concatenate(lums))
ramps = {k: [rr[k]] for k in PALS}
mats = [{'base': 'M242_A', 'prefix': 'M242', 'mask': 'm242_region_mask.png', 'regions': ['robe'], 'palettes': PALS, 'ramps': ramps},
        {'base': 'M242Head_A', 'prefix': 'M242Head', 'mask': 'm242_head_region_mask.png', 'regions': ['robe'], 'palettes': PALS,
         'ramps': ramps}]
(T / 'm242_ramps.json').write_text(json.dumps({'variants': list(PALS), 'materials': mats}, indent=1) + '\n')
for k in PALS:
    print('RAMP', k, 'robe mid', [round(x, 3) for x in rr[k]['colors'][8]])
