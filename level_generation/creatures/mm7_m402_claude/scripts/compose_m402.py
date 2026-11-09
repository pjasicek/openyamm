#!/usr/bin/env python3
"""Textures, region mask and tier ramps for the MM7 spider (CLAUDE_CREATURE_TEXTURES.md; small creature: one atlas,
cephalothorax and fang islands at 2x density). Run after uv_raster.py (1K, 2K) and bake_ao.py.

Tiers: palettes 66 Giant Spider / 67 Venomous Spider / 68 Widowmaker (sprite_frame_data 7m403/m404/7m405). Measured on
the native frames rendered through each palette (scripts/native_palettes.py): only the glossy abdomen changes (dark
green -> dark blue -> dark red); legs, red hair fringes, the skull pattern and the eyes stay. One region: R abdomen.
- Classes: abdomen = body-piece texels on the Abdomen bone; legs/thorax chitin; fringe cards (red hair); fangs and
  small pieces.
- Ramp: hue and saturation from each tier's native abdomen pixels (tier-A green hues; the same pixels in 67/68) at
  the texel's luminance quantile, luminance from the texel scaled so the region mean equals the native mean x
  RAMP_GAIN (manticore rule).
- Base colour 2K graded by the rest-pose AO; normal/ORM/mask 1K; ORM R = specular class (glossy abdomen 1.0), G
  roughness, B 0.
Writes textures/m402_*."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
NATIVE = HERE / 'references' / 'native_variants'
PALS = {'m402_a': 66, 'm402_b': 67, 'm402_c': 68}
RAMP_GAIN = 1.25
SPEC = {'abdomen': 1.0, 'chitin': 0.6, 'hair': 0.1, 'small': 0.7}
ROUGH = {'abdomen': 0.2, 'chitin': 0.35, 'hair': 0.85, 'small': 0.3}
CLS = {'abdomen': 4, 'chitin': 4, 'hair': 2, 'small': 5}


def load(path, n, mode='RGB'):
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


LEGP = {8, 1, 9, 7, 6, 5, 4, 3}                                     # leg pieces (scripts/rig_spider.py LEGS)


def classes(base, piece, bone, bn):
    cov = piece >= 0
    has = lambda *keys: np.isin(bone, [i for i, n in enumerate(bn) if n.startswith(keys)])
    abdomen = cov & (piece == 0) & has('Abdomen')
    small = cov & has('Fang')
    hair = cov & (piece > 0) & ~np.isin(piece, list(LEGP)) & ~small & ~has('Thorax', 'Abdomen')
    chitin = cov & ~abdomen & ~small & ~hair
    return {'abdomen': abdomen, 'chitin': chitin, 'hair': hair, 'small': small}, cov


M = HERE / 'meshy' / 'retexture_v1'
Rz = {n: np.load(HERE / 'work' / f'uvraster_UVMap_{n}.npz') for n in (1024, 2048)}
base2 = load(M / 'texture_urls_0_base_color.png', 2048)
C2, cov2 = classes(base2, Rz[2048]['piece'], Rz[2048]['bone'], list(Rz[2048]['bone_names']))
ao2 = load(HERE / 'work' / 'ao_UVMap.png', 2048, 'L')
f = np.clip(0.6 + 0.4 * np.maximum(ao2, 0.45), 0, 1)
g2 = base2.copy(); g2[cov2] = base2[cov2] * f[cov2][:, None]
save(pad(g2, cov2), T / 'm402_basecolor_2k.png')
base1 = np.asarray(Image.fromarray((np.clip(g2, 0, 1) * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS), np.float64) / 255
C1, cov1 = classes(load(M / 'texture_urls_0_base_color.png', 1024), Rz[1024]['piece'], Rz[1024]['bone'], list(Rz[1024]['bone_names']))
normal = load(M / 'texture_urls_0_normal.png', 1024); rough_m = load(M / 'texture_urls_0_roughness.png', 1024, 'L')
cls = np.zeros((1024, 1024), np.uint8); spec = np.zeros((1024, 1024)); rgh = np.full((1024, 1024), 0.8)
for name, m in C1.items():
    cls[m] = CLS[name]; spec[m] = SPEC[name]
    if m.any():
        rgh[m] = np.clip(ROUGH[name] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
save(pad(normal, cov1), T / 'm402_normal_1k.png')
save(np.stack([pad(spec, cov1), pad(rgh, cov1), np.zeros((1024, 1024))], -1), T / 'm402_metal_rough_1k.png')
Image.fromarray(cls).save(T / 'm402_material_classes.png')
REG = ['abdomen']
masks = [ndimage.gaussian_filter(pad(C1[r].astype(float), cov1), 0.7) for r in REG]
R.write_mask(masks, T / 'm402_region_mask.png', size=1024)
print('CLASSES', {n: int(m.sum()) for n, m in C1.items()}, 'covered', int(cov1.sum()))
for n in REG:
    print('MEDIAN', n, np.round(np.median(base1[C1[n]], 0) * 255))

# ---------------------------------------------------------------- native colours per region and tier
FR = [f'm402sa{v}' for v in range(5)] + [f'm402w{c}{v}' for c in 'abcdefgh' for v in (0, 2)] + \
     [f'm402a{c}{v}' for c in 'aceg' for v in (0, 2)]
nat = {r: {k: [] for k in PALS} for r in REG}
for fr in FR:
    ims = {k: np.asarray(Image.open(NATIVE / f'{fr}_{p}.png').convert('RGBA')).astype(float) / 255 for k, p in PALS.items()}
    a = ims['m402_a']; al = a[..., 3] > 0.5; h, s, v = hsv(a[..., :3])
    rm = {'abdomen': al & (h > 80) & (h < 175) & (s > 0.15)}
    for r in REG:
        for k in PALS:
            nat[r][k].append(ims[k][rm[r]][:, :3])
ramps = {k: [] for k in PALS}
for r in REG:
    m = C1[r]
    lum = R.luminance(base1[m]); lo, hi = np.percentile(lum, [2, 98]); srt = np.sort(lum)
    tex_mean = float(np.mean(lum))                                         # linear luminance (luminance() decodes sRGB)
    for k in PALS:
        Xs = np.concatenate(nat[r][k]); LX = R.luminance(Xs)
        o = np.argsort(LX); X = R.srgb_to_linear(Xs)[o]; LX = LX[o]
        kgain = float(np.mean(LX)) * RAMP_GAIN ** 2.2 / max(tex_mean, 1e-4)
        cols = []
        for i in range(16):
            Li = lo + (hi - lo) * i / 15
            q = np.searchsorted(srt, Li) / len(srt)
            j = int(q * (len(X) - 1)); c = np.median(X[max(0, j - 30):j + 31], 0)
            # colour (hue, saturation) from the palette, luminance from the texel scaled to the native mean:
            # histogram matching copied the sprite's bright end (A came out white) and over-saturated B's tan
            Lt = Li * kgain
            c = c * (Lt / max(float(c @ R.LUMA), 1e-5))
            cols.append([round(float(x), 6) for x in np.clip(c, 0, 1)])
        ramps[k].append({'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols})
    print('RAMP', r, {k: [round(c, 3) for c in ramps[k][-1]['colors'][8]] for k in PALS})
cfg = {'variants': list(PALS),
       'materials': [{'base': 'M402_A', 'prefix': 'M402', 'mask': 'm402_region_mask.png', 'regions': REG,
                      'palettes': PALS, 'ramps': ramps}]}
(T / 'm402_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
