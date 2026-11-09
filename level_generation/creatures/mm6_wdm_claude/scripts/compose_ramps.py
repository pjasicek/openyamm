#!/usr/bin/env python3
"""Per-tier skin colour ramps (CLAUDE_CREATURE_TEXTURES.md region masks + ramps; engine extras openyamm_region_mask /
openyamm_region_ramps). Run after compose_hd.py, compose_head.py and grade_basecolor.py.

- Runtime body base colour: the graded 2K master downscaled to 1K (textures/wdm_basecolor_graded_1k.png).
- Each tier's ramp comes from that tier's own native palette (684 A, 685 B, 683 C): the skin pixels of six native
  fly frames (masks_2x red channel), linear, sorted by luminance and averaged into 16 equal-count bins, times one
  albedo factor (sprites carry baked shading). The factor is fitted so tier A reproduces the accepted look (the
  previous single tint: texel luminance x the masked mean chroma) in least squares, then used for B and C too.
- Each material (body, head) gets its own luminance range: 2nd/98th percentile of the masked texels' linear
  luminance on the runtime base colour (the shader normalises luminance into 0..1 over it).
Writes textures/wdm_ramps.json: {materials: {Demon|DemonHead: {range}}, tiers: {a|b|c: {palette, colors}}, ...}."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
T = ROOT / 'textures'
NATIVE = ROOT.parent / 'mm6_wdm'
FRAMES = ['wdmflya0', 'wdmflyd0', 'wdmflya2', 'wdmflyb1', 'wdmflyc1', 'wdmflye1']
PALETTES = {'a': '684', 'b': '685', 'c': '683'}
STOPS = 16
W = np.array([0.2126, 0.7152, 0.0722])
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
MATERIALS = {'Demon': ('wdm_basecolor_graded_1k.png', 'wdm_region_mask.png'),
             'DemonHead': ('wdm_head_basecolor.png', 'wdm_head_region_mask.png')}


def native_skin(palette):
    out = []
    for frame in FRAMES:
        nv = np.asarray(Image.open(NATIVE / 'native_variants' / f'{frame}_{palette}.png').convert('RGBA'),
                        np.float32) / 255
        m = np.asarray(Image.open(NATIVE / 'masks_2x' / f'{frame}.png').convert('RGBA').resize(
            (nv.shape[1], nv.shape[0]), Image.NEAREST), np.float32) / 255
        out.append(nv[(nv[..., 3] > 0.5) & (m[..., 0] > 0.5), :3])
    return lin(np.concatenate(out))


def palette_ramp(colours):
    order = np.argsort(colours @ W)
    return np.array([b.mean(0) for b in np.array_split(colours[order], STOPS)])


def sample(ramp, t):
    x = np.clip(t, 0, 1) * (STOPS - 1); i = np.minimum(x.astype(int), STOPS - 2); f = (x - i)[..., None]
    return ramp[i] * (1 - f) + ramp[i + 1] * f


Image.open(T / 'wdm_basecolor_graded.png').convert('RGB').resize((1024, 1024), Image.LANCZOS).save(
    T / 'wdm_basecolor_graded_1k.png')
materials = {}
for name, (base_file, mask_file) in MATERIALS.items():
    base = lin(np.asarray(Image.open(T / base_file).convert('RGB'), np.float32) / 255)
    mask = np.asarray(Image.open(T / mask_file).convert('RGBA').resize(base.shape[1::-1], Image.BILINEAR),
                      np.float32)[..., 0] / 255
    lum = base @ W
    core = mask > 0.5
    lo, hi = np.percentile(lum[core], [2, 98])
    materials[name] = {'range': [round(float(lo), 5), round(float(hi), 5)], 'lum': lum[core], 'col': base[core]}

ramps = {k: palette_ramp(native_skin(p)) for k, p in PALETTES.items()}
# Accepted A look: texel luminance x the masked mean chroma (the previous openyamm_tint), over body and head texels.
num = den = 0.0
for m in materials.values():
    chroma = m['col'].mean(0) / (m['col'] @ W).mean()
    target = m['lum'][:, None] * chroma
    pred = sample(ramps['a'], (m['lum'] - m['range'][0]) / (m['range'][1] - m['range'][0]))
    num += float((pred * target).sum()); den += float((pred * pred).sum())
albedo = num / den
out = {'region': 'skin (mask channel R)', 'stops': STOPS, 'albedo_factor': round(albedo, 4),
       'luminance_percentiles': [2, 98], 'native_frames': FRAMES,
       'materials': {n: {'mask': MATERIALS[n][1], 'range': m['range']} for n, m in materials.items()},
       'tiers': {k: {'palette': PALETTES[k], 'colors': np.clip(r * albedo, 0, 1).round(5).tolist()}
                 for k, r in ramps.items()}}
json.dump(out, open(T / 'wdm_ramps.json', 'w'), indent=1)
print('RAMPS albedo', round(albedo, 3), 'ranges', {n: m['range'] for n, m in materials.items()},
      'clipped', {k: int((r * albedo > 1).sum()) for k, r in ramps.items()})
