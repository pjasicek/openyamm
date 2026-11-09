#!/usr/bin/env python3
"""Textures, region mask and tier ramps for the m398 skeleton warrior (CLAUDE_CREATURE_TEXTURES.md). Run after
uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py.

Tiers: descriptors 397 Skeleton (palette 399), 398 Skeleton Warrior (63) and 399 Skeleton Lord (64)
(mm7_m398 manifest native_group_bindings). The three palettes differ only in indices 174-247, which the native frames
use for the breeches (green / blue-violet / brown-red), so ONE region: the breeches cloth. Bone, steel, brass, the
rust streaks on the cloth and the props keep their colours.
- Classes per texel from the garment raster (work/uvraster_*.npz) and Meshy's colour: bone, steel, brass (hue 25-62,
  saturated), cloth (breeches; red rust streaks on it stay out of the mask), teeth.
- AO (work/ao_*.png) multiplied into the base colour (strength 0.4, floor 0.45). Steel darkened toward the native's
  gunmetal (x STEEL_GAIN). ORM red = per-class specular mask (openyamm_specular_mask), green = roughness, blue 0.
- Ramps per tier from the native frames (stand, walk, attack, hit): palette-63 pixels mapped back to their index; the
  index-174..247 pixels take each tier palette's colour; near-black outline pixels dropped; rank-matched to the
  region's texel luminance (2nd-98th percentile range), gain RAMP_GAIN (sprites carry baked shading).
Writes textures/m398_*."""
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
NATIVE = HERE.parent / 'mm7_m398' / 'native'
N = 1024
RAMP_GAIN = 1.3; STEEL_GAIN = 0.82
PALS = {'m398_a': 399, 'm398_b': 63, 'm398_c': 64}
SPEC = {'bone': 0.35, 'steel': 0.85, 'brass': 1.0, 'cloth': 0.2, 'tooth': 0.5}
ROUGH = {'bone': 0.6, 'steel': 0.35, 'brass': 0.3, 'cloth': 0.85, 'tooth': 0.45}
CLASS = {'bone': 5, 'steel': 9, 'brass': 9, 'cloth': 8, 'tooth': 5}


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


def ao_grade(img, ao, cov, strength=0.4, floor=0.45):
    f = np.clip(1 - strength + strength * np.maximum(ao, floor), 0, 1)
    out = img.copy(); out[cov] = img[cov] * f[cov][:, None]; return out


def classify(base, gar, cov, head):
    hue, sat, val = hsv(base)
    brass = (hue > 25) & (hue < 62) & (sat > 0.35) & (val > 0.3)
    red = ((hue < 20) | (hue > 330)) & (sat > 0.35)
    C = {}
    if head:
        C['bone'] = cov & (gar == 5); C['tooth'] = cov & (gar == 7) & ~brass
        metal = cov & ((gar == 6) | ((gar == 7) & brass))
    else:
        C['bone'] = cov & (gar == 0); C['tooth'] = np.zeros_like(cov)
        metal = cov & np.isin(gar, [1, 2, 4, 8])
    C['cloth'] = cov & (gar == 3)
    C['brass'] = metal & brass; C['steel'] = metal & ~brass
    return C, red


# ---------------------------------------------------------------- native region colours per tier
pal = lambda n: np.frombuffer((REPO / f'assets_dev/worlds/mm7/textures/pal{n:03d}.act').read_bytes()[:768], np.uint8).reshape(256, 3)
P = {k: pal(p) for k, p in PALS.items()}
lut = {tuple(c): i for i, c in enumerate(pal(63))}
FR = [f'm398sa{i}' for i in range(5)] + [f'm398w{c}0' for c in 'abcdefgh'] + [f'm398a{c}0' for c in 'abcdef'] + ['m398na0', 'm398nb0']
idx = []
for f in FR:
    im = np.asarray(Image.open(NATIVE / f'{f}.png').convert('RGBA'))
    px = im[im[..., 3] > 0][:, :3]
    idx.extend(lut[tuple(c)] for c in px)
idx = np.array(idx)
# only the entries that really change between the tier palettes (a few of 174-247 are equal in all three: pale
# highlights and fletching, which pulled the ramps' top half to white)
CHG = np.array([any((P[k][i] != P['m398_b'][i]).any() for k in PALS) for i in range(256)])
reg = idx[CHG[idx]]
native = {}
for k in PALS:
    X = P[k][reg].astype(np.float64) / 255; L = R.luminance(X); keep = L > 0.02
    o = np.argsort(L[keep]); native[k] = X[keep][o]
print('NATIVE region pixels', len(reg), 'of', len(idx), {k: np.round(np.median(v, 0) * 255).tolist() for k, v in native.items()})


def ramps_for(texel_lum):
    """Per tier: the ramp keeps the texture's own luminance (identity over the region's 2nd-98th percentile range)
    scaled by GAIN = native median luminance x RAMP_GAIN / texel median luminance (each tier's own brightness), with
    the tier's native chroma (median linear colour / luminance of its saturated region pixels). Rank-matching the
    native pixels copied the sprite's baked white highlights into the top third of the ramp (grey cloth; gob2 lesson)."""
    lo, hi = np.percentile(texel_lum, [2, 98]); tmed = float(np.median(texel_lum))
    out = {}
    for k in PALS:
        X = native[k]; Ls = R.luminance(X); hsvx = np.array([__import__('colorsys').rgb_to_hsv(*c) for c in X])
        sat = hsvx[:, 1] > 0.15
        chroma = np.median(lin(X[sat]) / Ls[sat][:, None], 0); chroma /= chroma @ R.LUMA
        gain = float(np.clip(np.median(Ls) * RAMP_GAIN ** 2.2 / tmed, 0.6, 3.0))
        cols = [[round(float(v), 6) for v in np.clip(chroma * (lo + (hi - lo) * i / 15) * gain, 0, 1)] for i in range(16)]
        out[k] = [{'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols}]
        print('RAMPFIT', k, 'chroma', np.round(chroma, 3).tolist(), 'gain', round(gain, 2), 'saturated px', int(sat.sum()))
    return out


def compose(base, normal, rough_m, raster, ao_png, head):
    Rz = np.load(HERE / 'work' / raster); gar = Rz['garment']; cov = gar >= 0
    C, red = classify(base, gar, cov, head)
    g = base.copy()
    g[C['steel']] *= STEEL_GAIN
    g = ao_grade(g, load(HERE / 'work' / ao_png, 'L'), cov)
    cls = np.zeros((N, N), np.uint8); spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8)
    for name, m in C.items():
        if m.any():
            cls[m] = CLASS[name]; spec[m] = SPEC[name]
            rgh[m] = np.clip(ROUGH[name] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
    print('CLASSES', 'head' if head else 'body', {n: int(m.sum()) for n, m in C.items()}, 'covered', int(cov.sum()))
    return g, cls, spec, rgh, cov, C, red


# ---------------------------------------------------------------- body set
# second triangle cut (reduce_textured.py): the maps rebaked onto the new UV layout (rebake_uv.py)
M = HERE / 'texturing' / 'rebake_v2' / 'body' if (HERE / 'texturing' / 'rebake_v2' / 'body').exists() else HERE / 'meshy' / 'retexture_v2'
base = load(M / 'texture_urls_0_base_color.png')
g, cls, spec, rgh, cov, C, red = compose(base, None, load(M / 'texture_urls_0_roughness.png', 'L'), 'uvraster_UVMap.npz', 'ao_UVMap.png', False)
cloth = C['cloth'] & ~red
cloth_ramps = ramps_for(R.luminance(g[cloth]))
print('MEDIANS body', {n: np.round(np.median(g[m], 0) * 255).tolist() for n, m in C.items() if m.any()})
save(pad(g, cov), T / 'm398_basecolor_1k.png'); save(pad(load(M / 'texture_urls_0_normal.png'), cov), T / 'm398_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'm398_metal_rough_1k.png')
# the mask is padded like the colour (nearest island texel into the gutters) before the blur (gob2 review 3)
R.write_mask([ndimage.gaussian_filter(pad(cloth.astype(float), cov), 0.7)], T / 'm398_region_mask.png', size=N)
Image.fromarray(cls).save(T / 'm398_material_classes.png')
# ---------------------------------------------------------------- head set (no recolour region)
# second triangle cut (reduce_textured.py): the maps rebaked onto the new UV layout (rebake_uv.py)
HM = HERE / 'texturing' / 'rebake_v2' / 'head' if (HERE / 'texturing' / 'rebake_v2' / 'head').exists() else HERE / 'meshy' / 'head_retexture_v1'
hb = load(HM / 'texture_urls_0_base_color.png')
hg, hcls, hspec, hrgh, hcov, _, _ = compose(hb, None, load(HM / 'texture_urls_0_roughness.png', 'L'), 'uvraster_HeadUV.npz', 'ao_HeadUV.png', True)
save(pad(hg, hcov), T / 'm398_head_basecolor_1k.png'); save(pad(load(HM / 'texture_urls_0_normal.png'), hcov), T / 'm398_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm398_head_metal_rough_1k.png')
Image.fromarray(hcls).save(T / 'm398_head_material_classes.png')
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Skeleton_A', 'prefix': 'Skeleton', 'mask': 'm398_region_mask.png', 'regions': ['breeches'],
                      'palettes': PALS, 'ramps': cloth_ramps}]}
(T / 'm398_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
for k in PALS:
    print('RAMP', k, 'mid', [round(x, 3) for x in cloth_ramps[k][0]['colors'][8]], 'range', cloth_ramps[k][0]['range'])
