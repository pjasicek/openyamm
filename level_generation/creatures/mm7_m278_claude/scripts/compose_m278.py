#!/usr/bin/env python3
"""Textures, region masks and tier ramps for the Manticore (CLAUDE_CREATURE_TEXTURES.md; small-head route: one atlas,
head islands at 2.5x density). Run after uv_raster.py (UVMap at 1024 and 2048) and bake_ao.py (work/ao_UVMap.png).

Tiers: palettes 279 Minicore / 280 Manticore / 281 Scorpicore (sprite_frame_data m279/m280/m281). Measured on the
native frames rendered through each palette (scripts/native_palettes.py): the mane changes completely (sage and maroon
-> charcoal and dark violet -> crimson and purple), the body fur from greyish tan to warm tan (280, 281), the chitin
tail and the dark details stay. Two regions: R mane, G fur.
- Classes from the mesh pieces and Meshy's paint: mane = the mane shingle pieces plus skin texels painted red/maroon
  on the head/neck/chest bones; chitin = the tail segment pieces and the Tail bones; small pieces (claws, teeth, eyes)
  are no region; fur = the remaining skin.
- Ramps: each region's native pixels (A mane: sage and maroon hues; fur: tan hues) and the SAME pixels in 280/281.
  The stop colour's hue and saturation come from the tier's native pixel at the texel's luminance quantile; its
  luminance is the texel's own, scaled so the region's mean equals the tier's native mean x RAMP_GAIN (cobra / sea
  serpent rule: histogram matching copied the sprite's bright end and tier A came out white).
- Base colour 2K graded by the rest-pose AO; normal/ORM/mask 1K; ORM R = specular class, G roughness, B 0.
Writes textures/m278_*."""
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
PALS = {'m278_a': 279, 'm278_b': 280, 'm278_c': 281}
RAMP_GAIN = 1.05   # pale creature: 1.2 read white in the viewer next to the dark-shaded sprite
SPEC = {'fur': 0.1, 'mane': 0.1, 'chitin': 0.6, 'small': 0.6, 'skin': 0.3}
ROUGH = {'fur': 0.85, 'mane': 0.9, 'chitin': 0.35, 'small': 0.35, 'skin': 0.6}
CLS = {'skin': 1, 'fur': 2, 'mane': 2, 'chitin': 4, 'small': 5}


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
J = json.load(open(HERE / 'work' / 'joints.json'))
TAILP = set(J['tail_pieces'].values())
SMALLP = {int(p) for p in np.unique(MESH['piece']) if p != 0 and p not in TAILP and
          ((MESH['co'][MESH['piece'] == p].max(0) - MESH['co'][MESH['piece'] == p].min(0)).max() < 0.08 or
           MESH['co'][MESH['piece'] == p][:, 2].mean() < 0.3)}                 # teeth, eyes, and the claws (low)


def classes(base, piece, bone, bn):
    h, s, v = hsv(base); cov = piece >= 0
    has = lambda *keys: np.isin(bone, [i for i, n in enumerate(bn) if n.startswith(keys)])
    small = cov & np.isin(piece, list(SMALLP))
    chitin = cov & (np.isin(piece, list(TAILP)) | (has('Tail') & (piece == 0)))
    shingle = cov & (piece > 0) & ~small & ~chitin
    red = ((h < 20) | (h > 320)) & (s > 0.3)
    mane = shingle | (cov & (piece == 0) & has('Head', 'Neck', 'Spine3') & red)
    fur = cov & ~mane & ~chitin & ~small
    return {'mane': mane, 'fur': fur, 'chitin': chitin, 'small': small}, cov


M = HERE / 'meshy' / 'retexture_v1'
Rz = {n: np.load(HERE / 'work' / f'uvraster_UVMap_{n}.npz') for n in (1024, 2048)}
base2 = load(M / 'texture_urls_0_base_color.png', 2048)
C2, cov2 = classes(base2, Rz[2048]['piece'], Rz[2048]['bone'], list(Rz[2048]['bone_names']))
ao2 = load(HERE / 'work' / 'ao_UVMap.png', 2048, 'L')
f = np.clip(0.6 + 0.4 * np.maximum(ao2, 0.45), 0, 1)
g2 = base2.copy(); g2[cov2] = base2[cov2] * f[cov2][:, None]
save(pad(g2, cov2), T / 'm278_basecolor_2k.png')
base1 = np.asarray(Image.fromarray((np.clip(g2, 0, 1) * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS), np.float64) / 255
C1, cov1 = classes(load(M / 'texture_urls_0_base_color.png', 1024), Rz[1024]['piece'], Rz[1024]['bone'], list(Rz[1024]['bone_names']))
normal = load(M / 'texture_urls_0_normal.png', 1024); rough_m = load(M / 'texture_urls_0_roughness.png', 1024, 'L')
cls = np.zeros((1024, 1024), np.uint8); spec = np.zeros((1024, 1024)); rgh = np.full((1024, 1024), 0.8)
for name, m in C1.items():
    cls[m] = CLS[name]; spec[m] = SPEC[name]
    if m.any():
        rgh[m] = np.clip(ROUGH[name] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
save(pad(normal, cov1), T / 'm278_normal_1k.png')
save(np.stack([pad(spec, cov1), pad(rgh, cov1), np.zeros((1024, 1024))], -1), T / 'm278_metal_rough_1k.png')
Image.fromarray(cls).save(T / 'm278_material_classes.png')
REG = ['mane', 'fur']
masks = [ndimage.gaussian_filter(pad(C1[r].astype(float), cov1), 0.7) for r in REG]
R.write_mask(masks, T / 'm278_region_mask.png', size=1024)
print('CLASSES', {n: int(m.sum()) for n, m in C1.items()}, 'covered', int(cov1.sum()))
for n in REG:
    print('MEDIAN', n, np.round(np.median(base1[C1[n]], 0) * 255))

# ---------------------------------------------------------------- native colours per region and tier
FR = [f'm278sa{v}' for v in range(5)] + [f'm278w{c}{v}' for c in 'abcdefgh' for v in (0, 2)] + \
     [f'm278a{c}{v}' for c in 'aceg' for v in (0, 2)]
nat = {r: {k: [] for k in PALS} for r in REG}
nat_group = {}                                                    # per mane pixel: maroon (True) or sage
for fr in FR:
    ims = {k: np.asarray(Image.open(NATIVE / f'{fr}_{p}.png').convert('RGBA')).astype(float) / 255 for k, p in PALS.items()}
    a = ims['m278_a']; al = a[..., 3] > 0.5; h, s, v = hsv(a[..., :3])
    rm = {'mane': al & (((h > 45) & (h < 120) & (s > 0.08)) | (((h > 300) | (h < 15)) & (s > 0.25))),
          'fur': al & (h >= 15) & (h <= 45) & (s > 0.15)}
    maroon = al & ((h > 300) | (h < 15)) & (s > 0.25)
    for k in PALS:
        nat_group.setdefault(k, []).append(maroon[rm['mane']])
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
        if r == 'mane':
            # the darkest share of the texels takes the maroon colours, the rest the sage ones (mid-luminance native
            # pixels mix both hue groups and averaged to a muddy pink); same pixels in every palette
            g = np.concatenate(nat_group[k]); A = np.concatenate(nat[r]['m278_a'])
            ga = np.argsort(R.luminance(A)[g]); gs = np.argsort(R.luminance(A)[~g])
            X = R.srgb_to_linear(np.concatenate([Xs[g][ga], Xs[~g][gs]])); LX = R.luminance(np.concatenate([Xs[g][ga], Xs[~g][gs]]))
            n_maroon = int(g.sum())
        else:
            o = np.argsort(LX); X = R.srgb_to_linear(Xs)[o]; LX = LX[o]
        kgain = float(np.mean(LX)) * RAMP_GAIN ** 2.2 / max(tex_mean, 1e-4)
        cols = []
        for i in range(16):
            Li = lo + (hi - lo) * i / 15
            q = np.searchsorted(srt, Li) / len(srt)
            j = int(q * (len(X) - 1)); c = np.median(X[max(0, j - 30):j + 31], 0)
            if r == 'fur':                                             # fur only changes tint: one chroma per tier
                c = np.median(X, 0)
            # colour (hue, saturation) from the palette, luminance from the texel scaled to the native mean:
            # histogram matching copied the sprite's bright end (A came out white) and over-saturated B's tan
            Lt = Li * kgain
            if r == 'mane' and j < n_maroon:                           # maroon keeps its own (dark) luminance:
                Lt = float(np.median(LX[max(0, j - 30):j + 31])) * RAMP_GAIN ** 2.2   # scaled, it read pink
            c = c * (Lt / max(float(c @ R.LUMA), 1e-5))
            cols.append([round(float(x), 6) for x in np.clip(c, 0, 1)])
        ramps[k].append({'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols})
    print('RAMP', r, {k: [round(c, 3) for c in ramps[k][-1]['colors'][8]] for k in PALS})
cfg = {'variants': list(PALS),
       'materials': [{'base': 'M278_A', 'prefix': 'M278', 'mask': 'm278_region_mask.png', 'regions': REG,
                      'palettes': PALS, 'ramps': ramps}]}
(T / 'm278_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
