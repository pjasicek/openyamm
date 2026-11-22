#!/usr/bin/env python3
"""Tier ramps of the Electrapede (CLAUDE_CREATURE_TEXTURES.md): one shared graded paint, four regions (R the green
plates and head, G legs, antennae and leg sockets, B the compound eyes, A the slate underside). Xeen draws the
Electrapede with one palette, so the one skin `electrapede_a` reproduces the native sprite's colours: per region the
COLOUR comes from the native pixels of that region (band-averaged chroma by luminance percentile, 15th-95th), the
texel keeps its own luminance, scaled so the region's mean is the native mean x 1.3 (sprites carry baked shading),
then the shader's ramp is fitted (region_variants.fit_ramps). The quadruped playbook's snake note: full histogram
matching would copy the sprite's painted shading range into speckles. Later tiers (other crawler colours) are new
ramp numbers on the same mask.
Native region pixels (Darkside 007.mon frames 0-3, mm4.pal): green hue 90-140 sat > 0.4; legs magenta hue 280-320,
value <= 0.75; eyes magenta value > 0.6 and saturation > 0.6 (the white-pink glints left out); underside slate hue 170-205.
Writes textures/pede_ramps.json (region_variants.py format) with the fit report."""
import colorsys, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as RV

base = RV.load_srgb(ROOT / 'textures/pede_basecolor_graded.png', 1024)
mask = Image.open(ROOT / 'textures/pede_region_mask.png')
px = []
for f in ('mon_0000', 'mon_0001', 'mon_0002', 'mon_0003'):
    a = np.asarray(Image.open(ROOT / 'native' / f'{f}.png').convert('RGBA'))
    px.append(a[a[..., 3] > 0][:, :3])
nat = np.concatenate(px).astype(np.float64) / 255.0
hsv = np.array([colorsys.rgb_to_hsv(*c) for c in nat]); H = hsv[:, 0] * 360; S = hsv[:, 1]; V = hsv[:, 2]
NATIVE = {'green': (H > 90) & (H < 140) & (S > 0.4),
          'legs': (H > 280) & (H < 320) & (S > 0.4) & (V <= 0.75),
          'eyes': (H > 280) & (H < 320) & (V > 0.6) & (S > 0.6),
          'under': (H > 170) & (H < 205) & (S > 0.3)}
GAIN = {'green': 1.3, 'legs': 1.3, 'eyes': 1.0, 'under': 1.3}


def target_for(region, weight):
    nlin = RV.srgb_to_linear(nat[NATIVE[region]]); nl = nlin @ RV.LUMA
    order = np.argsort(nl); nlin, nl = nlin[order], nl[order]
    chroma = nlin / np.maximum(nl, 1e-4)[:, None]
    lum = RV.luminance(base)
    sel = weight > 0.05
    q = np.zeros_like(lum)
    vals = lum[sel]; ranks = np.argsort(np.argsort(vals))
    q[sel] = ranks / max(1, len(vals) - 1)
    qq = np.clip(q, 0.15, 0.95)
    # band-averaged native chroma at the texel's percentile
    nq = np.linspace(0, 1, len(nl))
    grid = np.linspace(0.15, 0.95, 33)
    table = np.array([chroma[(nq >= g - 0.1) & (nq <= g + 0.1)].mean(0) for g in grid])
    c = np.stack([np.interp(qq, grid, table[:, k]) for k in range(3)], -1)
    k = GAIN[region] * nl.mean() / max(vals.mean(), 1e-4)
    out_lin = np.clip(c * (lum * k)[..., None], 0, 1)
    enc = np.where(out_lin <= 0.0031308, out_lin * 12.92, 1.055 * out_lin ** (1 / 2.4) - 0.055)
    return np.where(sel[..., None], enc, base), dict(native_px=int(NATIVE[region].sum()), gain=round(float(k), 3),
                                                   native_mean_srgb=(np.median(nat[NATIVE[region]], 0) * 255).round().tolist())


variants = ['electrapede_a']
ramps = {v: [] for v in variants}; report = {}; native = {}
for channel, region in zip('RGBA', ('green', 'legs', 'eyes', 'under')):
    weight = np.asarray(mask.getchannel(channel), np.float64) / 255.0
    tgt, info = target_for(region, weight)
    r, rep = RV.fit_ramps(base, {'electrapede_a': tgt}, weight)
    for v in variants:
        ramps[v].append(r[v])
    report[region] = rep; native[region] = info
    if region == 'green':
        Image.fromarray((np.clip(tgt, 0, 1) * 255 + 0.5).astype(np.uint8)).save(ROOT / 'work' / 'tier_a_target_green.png')
out = {'variants': variants,
       'materials': [{'base': 'Pede_A', 'prefix': 'Pede', 'mask': 'pede_region_mask.png', 'ramps': ramps}],
       'regions': ['R green plates and head', 'G legs, antennae, leg sockets (magenta-violet)', 'B compound eyes (magenta)',
                   'A slate underside'],
       'native': native, 'fit_report': report}
json.dump(out, open(ROOT / 'textures/pede_ramps.json', 'w'), indent=1)
print('RAMPS', json.dumps(report))
print('NATIVE', json.dumps(native))
