#!/usr/bin/env python3
"""Textures, region mask and tier ramps for the m430 wight (CLAUDE_CREATURE_TEXTURES.md). Run after uv_raster.py
(UVMap, HeadUV at 1024) and bake_ao_natm.py.

Tiers: descriptors 421 Wight (palette 111, brown robe), 422 Wraith (112, white) and 423 Barrow Wight (113, red)
(mm7_m430 manifest native_group_bindings). The palettes change only the robe in the native frames, so ONE region: the
robe cloth (robe texels of the body piece by colour, and the inner hem). Skin, hair, the waist cord and the dagger keep
their colours.
- Classes per texel from the garment raster (work/uvraster_*.npz) and Meshy's colour: cloth (brown, saturated),
  skin/hair (pale, desaturated), cord (garment 3), hands (garment 2, skin).
- AO (work/ao_*.png) multiplied into the base colour (strength 0.4, floor 0.45). ORM red = per-class specular mask,
  green = roughness, blue 0.
- Ramps per tier: the texture's own luminance (identity over the region's 2nd-98th percentile range) times the tier's
  brightness gain (native median luminance x RAMP_GAIN^2.2 / texel median), with the tier's native chroma (median
  linear colour / luminance of the region pixels; the white tier is nearly neutral). Native region pixels: palette-111
  frames mapped back to their index; the indices whose colour differs between the three palettes.
Writes textures/m430_*."""
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
NATIVE = HERE.parent / 'mm7_m430' / 'native'
N = 1024
RAMP_GAIN = 1.3
PALS = {'m430_a': 111, 'm430_b': 112, 'm430_c': 113}
SPEC = {'skin': 0.35, 'hair': 0.3, 'cloth': 0.15, 'cord': 0.15}
ROUGH = {'skin': 0.6, 'hair': 0.55, 'cloth': 0.9, 'cord': 0.85}
CLASS = {'skin': 1, 'hair': 2, 'cloth': 8, 'cord': 8}


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


def classify(base, gar, cov, head, pos=None):
    hue, sat, val = hsv(base)
    brown = (hue > 10) & (hue < 55) & (sat > 0.22)
    C = {}
    if head:
        C['skin'] = cov & ~((sat < 0.12) & (val > 0.55)); C['hair'] = cov & (sat < 0.12) & (val > 0.55)
        C['cloth'] = np.zeros_like(cov); C['cord'] = np.zeros_like(cov)
    else:
        # skin and hair on the robe piece only above the chest (neck, V opening, the hair down the back) and pale;
        # every other robe texel is cloth, its dark desaturated folds included (they must take the tier ramp)
        pale = cov & (gar == 0) & (pos[..., 2] > 1.15) & (val > 0.4) & (sat < 0.3)
        C['cloth'] = cov & (((gar == 0) & ~pale) | (gar == 4))
        C['cord'] = cov & (gar == 3)
        C['hair'] = pale & (sat < 0.1) & (val > 0.55)
        C['skin'] = (pale & ~C['hair']) | (cov & (gar == 2))
    return C, np.zeros_like(cov)


# ---------------------------------------------------------------- native region colours per tier
pal = lambda n: np.frombuffer((REPO / f'assets_dev/worlds/mm7/textures/pal{n:03d}.act').read_bytes()[:768], np.uint8).reshape(256, 3)
P = {k: pal(p) for k, p in PALS.items()}
lut = {tuple(c): i for i, c in enumerate(pal(111))}
FR = [f'm430sa{i}' for i in range(5)] + [f'm430w{c}0' for c in 'abcdefgh'] + [f'm430a{c}0' for c in 'abcdef'] + ['m430na0', 'm430nb0']
idx = []
for f in FR:
    im = np.asarray(Image.open(NATIVE / f'{f}.png').convert('RGBA'))
    px = im[im[..., 3] > 0][:, :3]
    idx.extend(lut[tuple(c)] for c in px)
idx = np.array(idx)
# only the entries that really change between the tier palettes (a few of 174-247 are equal in all three: pale
# highlights and fletching, which pulled the ramps' top half to white)
CHG = np.array([any((P[k][i] != P['m430_a'][i]).any() for k in PALS) for i in range(256)])
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
        sat = hsvx[:, 1] > (0.15 if np.median(hsvx[:, 1]) > 0.15 else -1)   # the white tier: all pixels
        chroma = np.median(lin(X[sat]) / Ls[sat][:, None], 0); chroma /= chroma @ R.LUMA
        gain = float(np.clip(np.median(Ls) * RAMP_GAIN ** 2.2 / tmed, 0.6, 25.0))
        cols = []
        for i in range(16):
            c = chroma * (lo + (hi - lo) * i / 15) * gain
            c = c / max(1.0, float(c.max()) / 0.92)          # keep the hue at the top (no channel clipping)
            cols.append([round(float(v), 6) for v in c])
        out[k] = [{'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols}]
        print('RAMPFIT', k, 'chroma', np.round(chroma, 3).tolist(), 'gain', round(gain, 2), 'saturated px', int(sat.sum()))
    return out


def compose(base, normal, rough_m, raster, ao_png, head):
    Rz = np.load(HERE / 'work' / raster); gar = Rz['garment']; cov = gar >= 0
    C, red = classify(base, gar, cov, head, Rz['pos'])
    g = base.copy()
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
M = HERE / 'texturing' / 'rebake_v2' / 'body' if (HERE / 'texturing' / 'rebake_v2' / 'body').exists() else HERE / 'meshy' / 'retexture_v1'
base = load(M / 'texture_urls_0_base_color.png')
g, cls, spec, rgh, cov, C, red = compose(base, None, load(M / 'texture_urls_0_roughness.png', 'L'), 'uvraster_UVMap.npz', 'ao_UVMap.png', False)
cloth = C['cloth']
cloth_ramps = ramps_for(R.luminance(g[cloth]))
print('MEDIANS body', {n: np.round(np.median(g[m], 0) * 255).tolist() for n, m in C.items() if m.any()})
save(pad(g, cov), T / 'm430_basecolor_1k.png'); save(pad(load(M / 'texture_urls_0_normal.png'), cov), T / 'm430_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'm430_metal_rough_1k.png')
# the mask is padded like the colour (nearest island texel into the gutters) before the blur (gob2 review 3)
R.write_mask([ndimage.gaussian_filter(pad(cloth.astype(float), cov), 0.7)], T / 'm430_region_mask.png', size=N)
Image.fromarray(cls).save(T / 'm430_material_classes.png')
# ---------------------------------------------------------------- head set (no recolour region)
# second triangle cut (reduce_textured.py): the maps rebaked onto the new UV layout (rebake_uv.py)
HM = HERE / 'texturing' / 'rebake_v2' / 'head' if (HERE / 'texturing' / 'rebake_v2' / 'head').exists() else HERE / 'meshy' / 'head_retexture_v1'
hb = load(HM / 'texture_urls_0_base_color.png')
hg, hcls, hspec, hrgh, hcov, _, _ = compose(hb, None, load(HM / 'texture_urls_0_roughness.png', 'L'), 'uvraster_HeadUV.npz', 'ao_HeadUV.png', True)
save(pad(hg, hcov), T / 'm430_head_basecolor_1k.png'); save(pad(load(HM / 'texture_urls_0_normal.png'), hcov), T / 'm430_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm430_head_metal_rough_1k.png')
Image.fromarray(hcls).save(T / 'm430_head_material_classes.png')
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Wight_A', 'prefix': 'Wight', 'mask': 'm430_region_mask.png', 'regions': ['robe'],
                      'palettes': PALS, 'ramps': cloth_ramps}]}
(T / 'm430_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
for k in PALS:
    print('RAMP', k, 'mid', [round(x, 3) for x in cloth_ramps[k][0]['colors'][8]], 'range', cloth_ramps[k][0]['range'])
