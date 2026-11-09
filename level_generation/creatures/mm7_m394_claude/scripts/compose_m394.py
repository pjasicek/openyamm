#!/usr/bin/env python3
"""Textures, region mask and tier ramps for the MM7 Sea Monster (CLAUDE_CREATURE_TEXTURES.md; one atlas, Meshy's UVs).
Run after uv_raster.py (UVMap at 2048 and 1024) and bake_ao.py.

Tiers: palettes 395 Giant Shark (teal-blue skin), 396 Piranha Shark (lavender), 397 Dragon Shark (red)
(sprite_frames m395/m396/m397). The restoration package's region 'blue_skin' is palette entries 80-177: the back and
flanks and the fins; the white belly, the mouth, teeth and eyes keep their colours in every tier. ONE region:
- skin = texels of the main shell (piece 0, not the mouth cavity) whose true HSV hue is 165-250 deg with saturation
  >= 0.10, or dark (value < 0.35) and not reddish: the teal back, its dark mottling and the fins. White belly (low
  saturation, bright), gums/tongue (red-pink) and teeth (pieces 1-36) stay out. Feathered 1 texel, padded into the
  gutters (gob2 rule) and zeroed on the teeth again.
- Classes: skin 1, tooth 5 (pieces 1-36), eye 6 (small dark texels on the head sides), mouth 7 (cavity fans and
  red-pink texels near the mouth).
- Ramps: m394_a keeps the texture's chroma; B and C take their palette's skin chroma at the same luminance rank,
  every tier at its own native brightness x RAMP_GAIN (Earth Elemental / m470 rule).
- Base colour 2K graded by the rest-pose AO (strength 0.35); normal/ORM/mask 1K; ORM R = specular class, G roughness.
Writes textures/m394_*."""
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
NATIVE = HERE.parent / 'mm7_m394' / 'native'
PALS = {'m394_a': 395, 'm394_b': 396, 'm394_c': 397}
RAMP_GAIN = 1.3
SKIN_IDX = range(80, 178)
SPEC = {'skin': 0.35, 'belly': 0.3, 'tooth': 0.6, 'eye': 0.9, 'mouth': 0.4}
ROUGH = {'skin': 0.5, 'belly': 0.55, 'tooth': 0.35, 'eye': 0.15, 'mouth': 0.45}
CLS = {'skin': 1, 'belly': 1, 'tooth': 5, 'eye': 6, 'mouth': 7}


def load(path, n, mode='RGB'):
    im = Image.open(path).convert(mode)
    return np.asarray(im.resize((n, n), Image.LANCZOS) if im.size != (n, n) else im, np.float64) / 255


def save(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, optimize=True)


def pad(img, cov):
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    out = img[iy, ix]; out[cov] = img[cov]; return out


def hsv(rgb):
    h = np.asarray(Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    return h[..., 0] * 360, h[..., 1], h[..., 2]


lin = R.srgb_to_linear
# ---------------------------------------------------------------- native skin colours per tier
pal = lambda n: np.frombuffer((REPO / f'assets_dev/worlds/mm7/textures/pal{n}.act').read_bytes()[:768], np.uint8).reshape(256, 3)
P = {k: pal(p) for k, p in PALS.items()}
lut = {tuple(c): i for i, c in enumerate(pal(395))}
FR = [f'm394sa{i}' for i in range(5)] + [f'm394w{c}2' for c in 'abcdefghij'] + [f'm394f{c}0' for c in 'abcdefg']
idx = []
for f in FR:
    im = np.asarray(Image.open(NATIVE / f'{f}.png').convert('RGBA'))
    idx.extend(lut[tuple(c)] for c in im[im[..., 3] > 0][:, :3] if tuple(c) in lut)
idx = np.array(idx); idx = idx[np.isin(idx, list(SKIN_IDX))]
native = {}
for k in PALS:
    X = P[k][idx].astype(np.float64) / 255; L = R.luminance(X); keep = L > 0.01
    native[k] = X[keep][np.argsort(L[keep])]
print('NATIVE skin pixels', len(idx), {k: np.round(np.median(v, 0) * 255).tolist() for k, v in native.items()})


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


def classes(n):
    Rz = np.load(HERE / 'work' / f'uvraster_UVMap_{n}.npz'); pc = Rz['piece']; cov = pc >= 0; pos = Rz['pos']
    mouth = Rz['mouth'] > 0
    base = load(HERE / 'meshy' / 'retexture_v1' / 'texture_urls_0_base_color.png', n)
    h, s, v = hsv(base)
    shell = cov & (pc == 0) & ~mouth
    head = pos[..., 1] < -0.55
    C = {}
    C['tooth'] = cov & (pc > 0)
    C['mouth'] = cov & (mouth | (shell & head & (pos[..., 1] < -0.78) & ((h < 30) | (h > 320)) & (s > 0.25)))
    C['eye'] = shell & head & ~C['mouth'] & (v < 0.16) & (pos[..., 1] > -0.92) & (pos[..., 1] < -0.70) & (pos[..., 2] > 0.30)
    skin = shell & ~C['mouth'] & ~C['eye'] & ((((h >= 165) & (h <= 250)) & (s >= 0.10)) | ((v < 0.35) & ~((h < 40) | (h > 300))))
    C['skin'] = skin
    C['belly'] = shell & ~skin & ~C['mouth'] & ~C['eye']
    return C, cov, base


C2, cov2, base2 = classes(2048)
C1, cov1, _ = classes(1024)
ao = load(HERE / 'work' / 'ao_UVMap.png', 2048, 'L')
f = np.clip(1 - 0.35 + 0.35 * np.maximum(ao, 0.45), 0, 1)
g = base2.copy(); g[cov2] = base2[cov2] * f[cov2][:, None]
trgb = g[C2['skin']]
ramps = ramps_for(R.luminance(trgb), trgb, 'm394_a')
save(pad(g, cov2), T / 'm394_basecolor_2k.png')
save(pad(load(HERE / 'meshy' / 'retexture_v1' / 'texture_urls_0_normal.png', 1024), cov1), T / 'm394_normal_1k.png')
rough_m = load(HERE / 'meshy' / 'retexture_v1' / 'texture_urls_0_roughness.png', 1024, 'L')
cls = np.zeros((1024, 1024), np.uint8); spec = np.zeros((1024, 1024)); rgh = np.full((1024, 1024), 0.6)
for name, m in C1.items():
    cls[m] = CLS[name]; spec[m] = SPEC[name]
    if m.any():
        rgh[m] = np.clip(ROUGH[name] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
save(np.stack([pad(spec, cov1), pad(rgh, cov1), np.zeros((1024, 1024))], -1), T / 'm394_metal_rough_1k.png')
Image.fromarray(cls).save(T / 'm394_material_classes.png')
mask = ndimage.gaussian_filter(C1['skin'].astype(float), 0.7)
mask = pad(mask, cov1); mask[C1['tooth'] | C1['mouth'] | C1['eye']] = 0
R.write_mask([mask], T / 'm394_region_mask.png', size=1024)
cfg = {'variants': list(PALS),
       'materials': [{'base': 'M394_A', 'prefix': 'M394', 'mask': 'm394_region_mask.png', 'regions': ['skin'], 'palettes': PALS, 'ramps': ramps}]}
(T / 'm394_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
print('CLASSES', {n: int(m.sum()) for n, m in C1.items()}, 'covered', int(cov1.sum()))
for k in PALS:
    print('RAMP', k, 'mid', [round(x, 3) for x in ramps[k][0]['colors'][8]], 'range', ramps[k][0]['range'])
