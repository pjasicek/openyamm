#!/usr/bin/env python3
"""Textures, region masks and tier ramps for the Earth Elemental (CLAUDE_CREATURE_TEXTURES.md), from m470's compose.
Run after uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py.

Tiers: the MM8 groups m505/m506/m507 (descriptors 79-81) draw the same frames in palettes 504 (brown), 506
(blue-slate) and 507 (red); the MM7 groups m199/m200/m201 (235-237) all use palette 504 and differ only in size. The
whole creature is stone and every palette entry of the native frames changes between the three palettes, so ONE
region covers every texel of both sets (body and head share the ramps; merge_head_material.py requires that).
- Class: stone everywhere (class 11 'other', README); specular 0.15, roughness 0.85 +- Meshy's variation.
- AO multiplied into the base colour (strength 0.45, floor 0.4): the native frames carry deep crack shading.
- Ramps per tier: the texture's own luminance over its 2nd-98th percentile range, scaled to the tier's native median
  luminance x RAMP_GAIN, with the tier's native chroma at the same luminance rank (m470 rule); tier A (504, the HD
  masters' palette) keeps the texture's own chroma.
Writes textures/m504_*."""
import json, sys, colorsys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
NATIVE = HERE.parent / 'mm7_m198' / 'native'
N = 1024
RAMP_GAIN = 1.35
PALS = {'m504_a': 504, 'm504_b': 506, 'm504_c': 507}
PALFILE = {504: 'pal504.act', 506: 'PAL506.act', 507: 'PAL507.act'}


def load(path, mode='RGB', n=N):
    im = Image.open(path).convert(mode)
    return np.asarray(im.resize((n, n), Image.LANCZOS) if im.size != (n, n) else im, np.float64) / 255


def save(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, optimize=True)


def pad(img, cov):
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    out = img[iy, ix]; out[cov] = img[cov]; return out


def lin(x): return R.srgb_to_linear(x)


def ao_grade(img, ao, cov, strength=0.45, floor=0.4):
    f = np.clip(1 - strength + strength * np.maximum(ao, floor), 0, 1)
    out = img.copy(); out[cov] = img[cov] * f[cov][:, None]; return out


# ---------------------------------------------------------------- native colours per tier
pal = lambda n: np.frombuffer((REPO / 'assets_dev/worlds/mm8/textures' / PALFILE[n]).read_bytes()[:768], np.uint8).reshape(256, 3)
P = {k: pal(p) for k, p in PALS.items()}
lut = {tuple(c): i for i, c in enumerate(pal(504))}
FR = [f'm198sa{i}' for i in range(5)] + [f'm198w{c}0' for c in 'abcdefgh'] + [f'm198a{c}0' for c in 'abcdefg']
idx = []
for f in FR:
    im = np.asarray(Image.open(NATIVE / f'{f}.png').convert('RGBA'))
    idx.extend(lut[tuple(c)] for c in im[im[..., 3] > 0][:, :3] if tuple(c) in lut)
idx = np.array(idx)
native = {}
for k in PALS:
    X = P[k][idx].astype(np.float64) / 255; L = R.luminance(X); keep = L > 0.01
    native[k] = X[keep][np.argsort(L[keep])]
print('NATIVE pixels', len(idx), {k: np.round(np.median(v, 0) * 255).tolist() for k, v in native.items()})


def ramps_for(texel_lum, texel_rgb, base_tier):
    lo, hi = np.percentile(texel_lum, [2, 98]); tmed = float(np.median(texel_lum)); srt_t = np.sort(texel_lum)
    t_ord = np.argsort(texel_lum); out = {}
    for k in PALS:
        X = native[k]; Ls = R.luminance(X)
        gain = float(np.clip(np.median(Ls) * RAMP_GAIN ** 2.2 / tmed, 0.08, 25.0))
        cols = []
        for i in range(16):
            Li = lo + (hi - lo) * i / 15
            q = np.searchsorted(srt_t, Li) / len(srt_t)
            j0, j1 = int(max(0, q - 0.06) * len(X)), int(min(1, q + 0.06) * len(X)) + 1
            Xw = X[j0:j1]; ch_i = np.mean(lin(Xw) / np.maximum(R.luminance(Xw), 1e-4)[:, None], 0); ch_i /= ch_i @ R.LUMA
            if k == base_tier:
                Tw = texel_rgb[t_ord[int(0.1 * len(t_ord)):int(0.9 * len(t_ord))]]
                ch_i = np.median(lin(Tw) / np.maximum(R.luminance(Tw), 1e-4)[:, None], 0); ch_i /= ch_i @ R.LUMA
            c = ch_i * (tmed * gain) * (max(Li, 1e-4) / tmed) ** 0.75
            c = c / max(1.0, float(c.max()) / 0.92)
            cols.append([round(float(v), 6) for v in c])
        out[k] = [{'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols}]
        print('RAMPFIT', k, 'gain', round(gain, 2), 'native median', np.round(np.median(X, 0) * 255).tolist())
    return out


def compose(base, rough_m, raster, ao_png):
    Rz = np.load(HERE / 'work' / raster); cov = Rz['garment'] >= 0
    g = ao_grade(base, load(HERE / 'work' / ao_png, 'L'), cov)
    cls = np.where(cov, 11, 0).astype(np.uint8)
    spec = np.where(cov, 0.15, 0.0)
    rgh = np.where(cov, np.clip(0.85 + (rough_m - np.median(rough_m[cov])) * 0.5, 0.5, 1), 0.85)
    print('CLASSES stone texels', int(cov.sum()))
    return g, cls, spec, rgh, cov


M = HERE / 'meshy' / 'retexture_v1'
g, cls, spec, rgh, cov = compose(load(M / 'texture_urls_0_base_color.png'), load(M / 'texture_urls_0_roughness.png', 'L'),
                                 'uvraster_UVMap.npz', 'ao_UVMap.png')
HM = HERE / 'meshy' / 'head_retexture_v1'
hg, hcls, hspec, hrgh, hcov = compose(load(HM / 'texture_urls_0_base_color.png'), load(HM / 'texture_urls_0_roughness.png', 'L'),
                                      'uvraster_HeadUV.npz', 'ao_HeadUV.png')
# the head set's stone matched to the body's luminance (one ramp for both: a brighter head would read lighter in every
# tier); gain on the head texels' median
gain_h = float(np.median(R.luminance(g[cov])) / max(np.median(R.luminance(hg[hcov])), 1e-4))
hg[hcov] = np.clip(hg[hcov] * gain_h, 0, 1)
print('HEAD luminance gain', round(gain_h, 3))
trgb = np.concatenate([g[cov], hg[hcov]])
ramps = ramps_for(R.luminance(trgb), trgb, 'm504_a')
save(pad(g, cov), T / 'm504_basecolor_1k.png'); save(pad(load(M / 'texture_urls_0_normal.png'), cov), T / 'm504_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'm504_metal_rough_1k.png')
R.write_mask([np.ones((N, N))], T / 'm504_region_mask.png', size=N)          # all stone: padded gutters included
Image.fromarray(cls).save(T / 'm504_material_classes.png')
save(pad(hg, hcov), T / 'm504_head_basecolor_1k.png'); save(pad(load(HM / 'texture_urls_0_normal.png'), hcov), T / 'm504_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm504_head_metal_rough_1k.png')
R.write_mask([np.ones((N, N))], T / 'm504_head_region_mask.png', size=N)
Image.fromarray(hcls).save(T / 'm504_head_material_classes.png')
cfg = {'variants': list(PALS),
       'materials': [{'base': 'EarthElemental_A', 'prefix': 'EarthElemental', 'mask': 'm504_region_mask.png', 'regions': ['stone'], 'palettes': PALS, 'ramps': ramps},
                     {'base': 'EarthElementalHead_A', 'prefix': 'EarthElementalHead', 'mask': 'm504_head_region_mask.png', 'regions': ['stone'], 'palettes': PALS, 'ramps': ramps}]}
# cap square for rubble.py: the deepest texel of the body coverage, half-size 70 % of its distance to the island edge
dtm = ndimage.distance_transform_edt(cov); iy, ix = np.unravel_index(np.argmax(dtm), dtm.shape)
cs = {'u': (ix + 0.5) / N, 'v': 1 - (iy + 0.5) / N, 'half': 0.7 * float(dtm[iy, ix]) / N}
(HERE / 'work' / 'cap_square.json').write_text(json.dumps(cs) + '\n'); print('CAPSQUARE', cs)
(T / 'm504_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
for k in PALS:
    print('RAMP', k, 'mid', [round(x, 3) for x in ramps[k][0]['colors'][8]], 'range', ramps[k][0]['range'])
