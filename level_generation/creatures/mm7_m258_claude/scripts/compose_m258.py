#!/usr/bin/env python3
"""Textures, region masks and tier ramps for the Griffin (CLAUDE_CREATURE_TEXTURES.md; small-head route: one atlas,
head islands at 2x density). Run after uv_raster.py (UVMap at 1024 and 2048) and bake_ao.py (work/ao_UVMap.png).

Tiers: palettes 259 Griffin / 260 Hunting Griffin / 261 Royal Griffin (sprite_frame_data m259/m260/m261). Measured
on the native frames rendered through each palette (scripts/native_palettes.py): plumage teal -> blue-grey -> crimson,
flight feathers olive -> grey -> near black, lion fur unchanged in 260 and slightly warmer in 261, gold beak/talons
unchanged in 260 and more saturated in 261. Three regions: R plumage, G flight feathers, B fur; gold is no region
(its native ramp read far brighter than the paint, and only C changes it slightly): the beak and talons keep Meshy's
gold in every tier.
- Classes from Meshy's paint (true HSV) and the dominant bone of each texel: plumage = teal (h 130-230); flight
  feathers = wing-bone texels that are not teal and not gold; gold = saturated yellow (beak, eagle legs); fur =
  brown on body/hind-leg/tail bones; claws/talon tips = dark, low-saturation texels on the paw bones; eyes = head
  texels of the eye pieces.
- Ramps: for each region, the tier-A native pixels of that class (hue rules above) and the SAME pixels in 260/261,
  each tier sorted by its own luminance (sorting B/C by A's order made the grey ramp non-monotonic and too light),
  rank-matched to the region's texel luminance (2nd-98th percentile), gain RAMP_GAIN; unchanged colours included
  (thunderbird lesson: changed-only fits recoloured unchanged browns).
- Base colour 2K graded by the rest-pose AO; normal/ORM/mask 1K; ORM R = specular class, G roughness, B 0.
Writes textures/m258_*."""
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
PALS = {'m258_a': 259, 'm258_b': 260, 'm258_c': 261}
RAMP_GAIN = 1.15   # 1.3 read pastel next to the native deep teal in the viewer
SPEC = {'fur': 0.1, 'plumage': 0.15, 'feather': 0.15, 'gold': 0.5, 'claw': 0.7, 'eye': 0.9, 'skin': 0.3}
ROUGH = {'fur': 0.85, 'plumage': 0.8, 'feather': 0.75, 'gold': 0.45, 'claw': 0.35, 'eye': 0.15, 'skin': 0.6}
CLS = {'skin': 1, 'fur': 2, 'plumage': 2, 'feather': 3, 'gold': 4, 'claw': 4, 'eye': 6}


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


def classes(base, piece, bone, bn):
    h, s, v = hsv(base); cov = piece >= 0
    has = lambda *keys: np.isin(bone, [i for i, n in enumerate(bn) if n.startswith(keys)])
    teal = (h > 130) & (h < 230) & (s > 0.12)
    gold = (h > 28) & (h < 65) & (s > 0.5) & (v > 0.4)
    wing = has('Wing'); paw = has('FrontPaw', 'ForeArm', 'HindPaw')
    eye = cov & (piece >= 1) & has('Head')
    claw = cov & paw & (v < 0.3) & (s < 0.35) & ~eye
    plumage = cov & teal & ~eye
    feather = cov & wing & ~plumage & ~gold
    goldm = cov & gold & has('Head', 'Neck', 'UpperArm', 'ForeArm', 'FrontPaw') & ~eye   # lion fur shares the hue
    fur = cov & ~plumage & ~feather & ~goldm & ~claw & ~eye
    return {'plumage': plumage, 'feather': feather, 'fur': fur, 'gold': goldm, 'claw': claw, 'eye': eye}, cov


M = HERE / 'meshy' / 'retexture_v1'
Rz = {n: np.load(HERE / 'work' / f'uvraster_UVMap_{n}.npz') for n in (1024, 2048)}
base2 = load(M / 'texture_urls_0_base_color.png', 2048)
C2, cov2 = classes(base2, Rz[2048]['piece'], Rz[2048]['bone'], list(Rz[2048]['bone_names']))
ao2 = load(HERE / 'work' / 'ao_UVMap.png', 2048, 'L')
f = np.clip(0.6 + 0.4 * np.maximum(ao2, 0.45), 0, 1)
g2 = base2.copy(); g2[cov2] = base2[cov2] * f[cov2][:, None]
save(pad(g2, cov2), T / 'm258_basecolor_2k.png')
base1 = np.asarray(Image.fromarray((np.clip(g2, 0, 1) * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS), np.float64) / 255
C1, cov1 = classes(load(M / 'texture_urls_0_base_color.png', 1024), Rz[1024]['piece'], Rz[1024]['bone'], list(Rz[1024]['bone_names']))
normal = load(M / 'texture_urls_0_normal.png', 1024); rough_m = load(M / 'texture_urls_0_roughness.png', 1024, 'L')
cls = np.zeros((1024, 1024), np.uint8); spec = np.zeros((1024, 1024)); rgh = np.full((1024, 1024), 0.8)
for name, m in C1.items():
    cls[m] = CLS[name]; spec[m] = SPEC[name]
    if m.any():
        rgh[m] = np.clip(ROUGH[name] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
save(pad(normal, cov1), T / 'm258_normal_1k.png')
save(np.stack([pad(spec, cov1), pad(rgh, cov1), np.zeros((1024, 1024))], -1), T / 'm258_metal_rough_1k.png')
Image.fromarray(cls).save(T / 'm258_material_classes.png')
REG = ['plumage', 'feather', 'fur']
masks = [ndimage.gaussian_filter(pad(C1[r].astype(float), cov1), 0.7) for r in REG]
R.write_mask(masks, T / 'm258_region_mask.png', size=1024)
print('CLASSES', {n: int(m.sum()) for n, m in C1.items()}, 'covered', int(cov1.sum()))
for n in REG:
    print('MEDIAN', n, np.round(np.median(base1[C1[n]], 0) * 255))

# ---------------------------------------------------------------- native colours per region and tier
FR = [f'm258sa{v}' for v in range(5)] + [f'm258w{c}{v}' for c in 'abcdefg' for v in (0, 2)] + \
     [f'm258a{c}{v}' for c in 'aceg' for v in (0, 2)]
nat = {r: {k: [] for k in PALS} for r in REG}
for fr in FR:
    ims = {k: np.asarray(Image.open(NATIVE / f'{fr}_{p}.png').convert('RGBA')).astype(float) / 255 for k, p in PALS.items()}
    a = ims['m258_a']; al = a[..., 3] > 0.5; h, s, v = hsv(a[..., :3])
    rm = {'plumage': al & (h > 130) & (h < 230) & (s > 0.15), 'gold': al & (h > 30) & (h < 62) & (s > 0.55) & (v > 0.45),
          'feather': al & (h > 30) & (h < 80) & (s <= 0.55) & (s > 0.12), 'fur': al & (h < 30) & (s > 0.3)}
    for r in REG:
        for k in PALS:
            nat[r][k].append(ims[k][rm[r]][:, :3])
ramps = {k: [] for k in PALS}
for r, m in zip(REG, C1.values() if False else [C1[x] for x in REG]):
    lum = R.luminance(base1[m]); lo, hi = np.percentile(lum, [2, 98]); srt = np.sort(lum)
    for k in PALS:
        X = np.concatenate(nat[r][k]); X = X[np.argsort(R.luminance(X))]; cols = []   # each tier by its own luminance
        for i in range(16):
            q = np.searchsorted(srt, lo + (hi - lo) * i / 15) / len(srt)
            j = int(q * (len(X) - 1)); w = X[max(0, j - 30):j + 31].mean(0)
            cols.append([round(float(c), 6) for c in np.clip(R.srgb_to_linear(np.clip(w * RAMP_GAIN, 0, 1)), 0, 1)])
        ramps[k].append({'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols})
    print('RAMP', r, {k: [round(c, 3) for c in ramps[k][-1]['colors'][8]] for k in PALS})
cfg = {'variants': list(PALS),
       'materials': [{'base': 'M258_A', 'prefix': 'M258', 'mask': 'm258_region_mask.png', 'regions': REG,
                      'palettes': PALS, 'ramps': ramps}]}
(T / 'm258_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
