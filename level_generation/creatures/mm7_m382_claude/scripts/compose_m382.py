#!/usr/bin/env python3
"""Textures, region masks and tier ramps for the MM7 rat (CLAUDE_CREATURE_TEXTURES.md; small creature: one atlas, head
islands at 2.5x). Run after uv_raster.py (1K, 2K) and bake_ao.py.

Tiers: palettes 383 Giant Rat / 384 Lightning Rat / 385 Fire Rat (sprite_frame_data m383/m384/m385). Measured on the
native frames rendered through each palette (scripts/native_palettes.py): the bare skin of head, ears, legs and tail
changes (mint green -> pale blue -> pink) and the eyes (black -> amber -> red); the grey fur stays. Two regions:
R skin, G eyes.
- Classes from Meshy's paint and the mesh: skin = pale mint texels (true HSV hue 55-170, s > 0.08, v > 0.3); eyes =
  dark texels in the eye area of the head piece; teeth, whiskers and claws = the small pieces; fur = the rest.
- Ramps: skin takes one chroma per tier (the median of that palette's skin pixels; the change is a tint) at the
  texel's own luminance scaled to the native mean x RAMP_GAIN (manticore rule); eyes take the tier's native eye colour
  at its own luminance (black, amber, red) for every stop.
- Base colour 2K graded by the rest-pose AO; normal/ORM/mask 1K; ORM R = specular class, G roughness, B 0.
Writes textures/m382_*."""
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
PALS = {'m382_a': 383, 'm382_b': 384, 'm382_c': 385}
RAMP_GAIN = 1.1
SPEC = {'fur': 0.1, 'skin': 0.35, 'eye': 0.9, 'small': 0.6}
ROUGH = {'fur': 0.85, 'skin': 0.55, 'eye': 0.15, 'small': 0.35}
CLS = {'skin': 1, 'fur': 2, 'eye': 6, 'small': 5}


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


MESH = np.load(HERE / 'work' / 'step1_mesh.npz')
SMALL = {int(p) for p in np.unique(MESH['piece']) if p != 0 and (MESH['piece'] == p).sum() <= 150}   # teeth, whiskers, claws
POS = {n: np.load(HERE / 'work' / f'uvraster_UVMap_{n}.npz')['pos'] for n in (1024, 2048)}


def classes(base, piece, bone, bn):
    h, s, v = hsv(base); cov = piece >= 0
    pos = POS[base.shape[0]]
    # eyes are painted on the head piece: dark glossy texels in the eye area (the round pieces in the face are teeth)
    eye = cov & (piece == 0) & (v < 0.2) & (pos[..., 1] > -0.9) & (pos[..., 1] < -0.68) & (pos[..., 2] > 0.42)
    small = cov & np.isin(piece, list(SMALL))
    skin = cov & ~eye & ~small & (h > 55) & (h < 170) & (s > 0.08) & (v > 0.3)
    fur = cov & ~eye & ~small & ~skin
    return {'skin': skin, 'eye': eye, 'fur': fur, 'small': small}, cov


M = HERE / 'meshy' / 'retexture_v1'
Rz = {n: np.load(HERE / 'work' / f'uvraster_UVMap_{n}.npz') for n in (1024, 2048)}
base2 = load(M / 'texture_urls_0_base_color.png', 2048)
C2, cov2 = classes(base2, Rz[2048]['piece'], Rz[2048]['bone'], list(Rz[2048]['bone_names']))
ao2 = load(HERE / 'work' / 'ao_UVMap.png', 2048, 'L')
f = np.clip(0.6 + 0.4 * np.maximum(ao2, 0.45), 0, 1)
g2 = base2.copy(); g2[cov2] = base2[cov2] * f[cov2][:, None]
save(pad(g2, cov2), T / 'm382_basecolor_2k.png')
base1 = np.asarray(Image.fromarray((np.clip(g2, 0, 1) * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS), np.float64) / 255
C1, cov1 = classes(load(M / 'texture_urls_0_base_color.png', 1024), Rz[1024]['piece'], Rz[1024]['bone'], list(Rz[1024]['bone_names']))
normal = load(M / 'texture_urls_0_normal.png', 1024); rough_m = load(M / 'texture_urls_0_roughness.png', 1024, 'L')
cls = np.zeros((1024, 1024), np.uint8); spec = np.zeros((1024, 1024)); rgh = np.full((1024, 1024), 0.8)
for name, m in C1.items():
    cls[m] = CLS[name]; spec[m] = SPEC[name]
    if m.any():
        rgh[m] = np.clip(ROUGH[name] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
save(pad(normal, cov1), T / 'm382_normal_1k.png')
save(np.stack([pad(spec, cov1), pad(rgh, cov1), np.zeros((1024, 1024))], -1), T / 'm382_metal_rough_1k.png')
Image.fromarray(cls).save(T / 'm382_material_classes.png')
REG = ['skin', 'eye']
masks = [ndimage.gaussian_filter(pad(C1[r].astype(float), cov1), 0.7) for r in REG]
R.write_mask(masks, T / 'm382_region_mask.png', size=1024)
print('CLASSES', {n: int(m.sum()) for n, m in C1.items()}, 'covered', int(cov1.sum()))
for n in REG:
    print('MEDIAN', n, np.round(np.median(base1[C1[n]], 0) * 255))

# ---------------------------------------------------------------- native colours per region and tier
FR = [f'm382sa{v}' for v in range(5)] + [f'm382w{c}{v}' for c in 'abcdefgh' for v in (0, 2)] + \
     [f'm382a{c}{v}' for c in 'aceg' for v in (0, 2)]
nat = {r: {k: [] for k in PALS} for r in REG}
for fr in FR:
    ims = {k: np.asarray(Image.open(NATIVE / f'{fr}_{p}.png').convert('RGBA')).astype(float) / 255 for k, p in PALS.items()}
    a = ims['m382_a']; al = a[..., 3] > 0.5; h, s, v = hsv(a[..., :3])
    hb, sb, vb = hsv(ims['m382_b'][..., :3])
    rm = {'skin': al & (h > 55) & (h < 170) & (s > 0.08) & (v > 0.25),
          'eye': al & (hb > 15) & (hb < 60) & (sb > 0.5) & (vb > 0.35) & (v < 0.35)}
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
            c = np.median(X, 0)                                        # one chroma per tier
            # colour (hue, saturation) from the palette, luminance from the texel scaled to the native mean:
            # histogram matching copied the sprite's bright end (A came out white) and over-saturated B's tan
            Lt = Li * kgain
            if r == 'eye':                                             # eyes: the native colour as it is
                Lt = float(np.median(LX)) * RAMP_GAIN ** 2.2
            c = c * (Lt / max(float(c @ R.LUMA), 1e-5))
            cols.append([round(float(x), 6) for x in np.clip(c, 0, 1)])
        ramps[k].append({'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols})
    print('RAMP', r, {k: [round(c, 3) for c in ramps[k][-1]['colors'][8]] for k in PALS})
cfg = {'variants': list(PALS),
       'materials': [{'base': 'M382_A', 'prefix': 'M382', 'mask': 'm382_region_mask.png', 'regions': REG,
                      'palettes': PALS, 'ramps': ramps}]}
(T / 'm382_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
