#!/usr/bin/env python3
"""Textures, region masks and tier ramps for the Behemoth (CLAUDE_CREATURE_TEXTURES.md). Run after uv_raster.py (UVMap,
HeadUV at 1024) and bake_ao_natm.py (work/ao_*.png).

Tiers (palettes 163 Young Behemoth green / 164 Behemoth blue-violet / 165 Ancient Behemoth red; sprite_frame_data
m163/m164/m165) recolour ONE region, as the native package's mask_r: the mane (crown, back, shoulders) and the chin
beard. Hide, claws, teeth, mouth and eyes stay.
- Region: every mane shingle (garment 1) plus any texel Meshy painted green (true HSV hue 65-175, s > 0.15):
  the beard and the scalp under the shingles. Padded into the gutters before the 0.7 px blur (gob2 lesson).
- Base colour: Meshy's paint, graded by the rest-pose AO (strength 0.4, floor 0.45), body and head 1K.
- ORM: R = per-class specular mask (openyamm_specular_mask), G roughness by class (+ half of Meshy's variation), B 0.
- Material classes (1 skin, 2 fur, 4 claw, 5 tooth, 6 eye) in textures/m162_material_classes.png and
  m162_head_material_classes.png. Claws: hand-dominant texels, pale ivory (s < 0.35, v > 0.5) or rust tips.
- Ramps per tier from the native frames: green tier-A pixels that change strongly in 164/165 = the recolour region
  (stand, walk, attack, hit views), rank-matched to the mane texels' luminance (2nd-98th percentile) of both sets
  together (one ramp set for body and head, so the seam matches), gain RAMP_GAIN (sprites carry baked shading).
Writes textures/m162_*."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
NATIVE = HERE.parent / 'mm7_m162' / 'native_variants'
N = 1024
RAMP_GAIN = 1.15   # 1.35 read pastel next to the native deep green in the viewer
PALS = {'m162_a': 163, 'm162_b': 164, 'm162_c': 165}
SPEC = {'skin': 0.3, 'fur': 0.1, 'claw': 0.8, 'tooth': 0.6, 'eye': 0.9}
ROUGH = {'skin': 0.62, 'fur': 0.85, 'claw': 0.35, 'tooth': 0.4, 'eye': 0.15}
CLS = {'skin': 1, 'fur': 2, 'claw': 4, 'tooth': 5, 'eye': 6}


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


def classes(base, gar, bone, bone_names):
    hue, sat, val = hsv(base)
    cov = gar >= 0
    green = (hue > 65) & (hue < 175) & (sat > 0.15) & (val > 0.06)
    fur = cov & ((gar == 1) | green)
    hand = np.isin(bone, [i for i, n in enumerate(bone_names) if n.endswith('_Hand')])
    claw = cov & (gar == 0) & hand & ~fur & (((sat < 0.35) & (val > 0.5)) | ((hue < 25) | (hue > 340)) & (sat > 0.35))
    eye = cov & (gar == 9) & (hue > 5) & (hue < 45) & (sat > 0.55) & (val > 0.45)
    tooth = cov & (gar == 9) & ~eye & ~fur & (sat < 0.45) & (val > 0.4)
    skin = cov & ~fur & ~claw & ~eye & ~tooth
    return {'skin': skin, 'fur': fur, 'claw': claw, 'tooth': tooth, 'eye': eye}, cov


def build(meshy_dir, raster, ao_png, prefix):
    base = load(meshy_dir / 'texture_urls_0_base_color.png'); normal = load(meshy_dir / 'texture_urls_0_normal.png')
    rough_m = load(meshy_dir / 'texture_urls_0_roughness.png', 'L')
    Rz = np.load(raster); gar, bone, bn = Rz['garment'], Rz['bone'], list(Rz['bone_names'])
    C, cov = classes(base, gar, bone, bn)
    g = ao_grade(base, load(ao_png, 'L'), cov)
    cls = np.zeros((N, N), np.uint8); spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8)
    for name, m in C.items():
        cls[m] = CLS[name]; spec[m] = SPEC[name]
        if m.any():
            rgh[m] = np.clip(ROUGH[name] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
    save(pad(g, cov), T / f'{prefix}_basecolor_1k.png'); save(pad(normal, cov), T / f'{prefix}_normal_1k.png')
    save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / f'{prefix}_metal_rough_1k.png')
    Image.fromarray(cls).save(T / f'{prefix}_material_classes.png')
    mask = ndimage.gaussian_filter(pad(C['fur'].astype(float), cov), 0.7)
    R.write_mask([mask], T / f'{prefix}_region_mask.png', size=N)
    print('CLASSES', prefix, {n: int(m.sum()) for n, m in C.items()}, 'covered', int(cov.sum()),
          'fur median', np.round(np.median(base[C['fur']], 0) * 255), 'skin median', np.round(np.median(base[C['skin']], 0) * 255))
    return R.luminance(g[C['fur']])


lum_body = build(HERE / 'meshy' / 'retexture_v1', HERE / 'work' / 'uvraster_UVMap.npz', HERE / 'work' / 'ao_UVMap.png', 'm162')
lum_head = build(HERE / 'meshy' / 'head_retexture_v1', HERE / 'work' / 'uvraster_HeadUV.npz', HERE / 'work' / 'ao_HeadUV.png',
                 'm162_head')

# ---------------------------------------------------------------- native recolour colours per tier
FR = [f'm162sa{v}' for v in range(5)] + [f'm162w{f}{v}' for f in 'aceg' for v in (0, 2)] + \
     [f'm162a{f}{v}' for f in 'aceg' for v in (0, 2)] + ['m162na0', 'm162nb0']
native = {k: [] for k in PALS}
for f in FR:
    ims = {k: np.asarray(Image.open(NATIVE / f'{f}_{p}.png').convert('RGBA')).astype(np.float64) / 255 for k, p in PALS.items()}
    al = ims['m162_a'][..., 3] > 0.5
    # strong change on green tier-A pixels: the hide's palette entries also shift a little between 163/164/165, and
    # a 0.02 threshold pulled grey hide into the B/C ramps
    ha, sa, _ = hsv(ims['m162_a'][..., :3])
    d = ((np.abs(ims['m162_a'][..., :3] - ims['m162_b'][..., :3]).sum(-1) > 0.12) |
         (np.abs(ims['m162_a'][..., :3] - ims['m162_c'][..., :3]).sum(-1) > 0.12)) & (ha > 65) & (ha < 175) & (sa > 0.12)
    for k in PALS:
        native[k].append(ims[k][al & d][:, :3])
for k in PALS:
    X = np.concatenate(native[k]); L = R.luminance(X); X, L = X[L > 0.02], L[L > 0.02]
    o = np.argsort(L); native[k] = (X[o], L[o])
    print('NATIVE', k, 'region pixels', len(X), 'median sRGB', np.round(np.median(X, 0) * 255))


def ramps_for(texel_lum):
    lo, hi = np.percentile(texel_lum, [2, 98]); srt = np.sort(texel_lum)
    out = {}
    for k in PALS:
        X, _ = native[k]; cols = []
        for i in range(16):
            Li = lo + (hi - lo) * i / 15
            q = np.searchsorted(srt, Li) / len(srt)
            # a small window around the quantile (single native pixels are noisy)
            j = int(q * (len(X) - 1)); w = X[max(0, j - 40):j + 41].mean(0)
            cols.append([round(float(v), 6) for v in np.clip(lin(np.clip(w * RAMP_GAIN, 0, 1)), 0, 1)])
        out[k] = [{'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols}]
    return out


ramps = ramps_for(np.concatenate([lum_body, lum_head]))
cfg = {'variants': list(PALS),
       'materials': [{'base': 'M162_A', 'prefix': 'M162', 'mask': 'm162_region_mask.png', 'regions': ['mane'],
                      'palettes': PALS, 'ramps': ramps},
                     {'base': 'M162Head_A', 'prefix': 'M162Head', 'mask': 'm162_head_region_mask.png',
                      'regions': ['mane'], 'palettes': PALS, 'ramps': ramps}]}
(T / 'm162_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
for k in PALS:
    print('RAMP', k, 'mid', [round(x, 3) for x in ramps[k][0]['colors'][8]], 'range', ramps[k][0]['range'])
