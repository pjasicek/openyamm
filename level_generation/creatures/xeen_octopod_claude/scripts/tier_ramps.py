#!/usr/bin/env python3
"""Tier ramps of the octopods (CLAUDE_CREATURE_TEXTURES.md): one shared graded paint, three regions (R skin: head,
tentacles and the flesh round the eyes; G suckers; B irises; the pupils in none). Xeen draws all three with one sprite
(Darkside 041), so only A is native; B and C are design recolours of the whole body (D-10: whole-body tiers that read
apart at combat distance):
  octopod_a  Octopod        the native colours: per region the COLOUR comes from the native pixels of that region in
                            041.mon (band-averaged chroma by luminance percentile, 15th-95th), the texel keeps its own
                            luminance scaled so the region's mean is the native mean x GAIN (sprites carry baked shading),
                            then the shader's ramp is fitted (the sand worm's and electrapede's route)
  octopod_b  Great Octopod  deep violet-purple skin (hue 285, saturation x0.9, value x0.82), pale gold suckers (hue 46,
                            saturation x0.62), amber eyes (hue 40)
  octopod_c  Kraken         dark sea-green / slate skin (hue 165, saturation x0.45, value x0.6), pale bone suckers (hue 50,
                            saturation x0.28), red-orange eyes (hue 10): the old, deep-water giant
Native region pixels (mm4.pal, 041.mon frames): skin red (hue < 15 or > 345, saturation > 0.5, value > 0.25); suckers
yellow-olive (hue 40-75, saturation > 0.4); irises blue (hue 200-245, saturation > 0.45, value > 0.45; the lake's teal
is hue 180-195).
Writes textures/octopod_ramps.json (region_variants.py format) with the fit report."""
import colorsys, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as RV

base = RV.load_srgb(ROOT / 'textures/octopod_basecolor_graded.png', 1024)
mask = Image.open(ROOT / 'textures/octopod_region_mask.png')
px = []
for f in ('mon_0000', 'mon_0001', 'mon_0002', 'mon_0003', 'mon_0004', 'mon_0005', 'mon_0006', 'mon_0007'):
    a = np.asarray(Image.open(ROOT / 'native' / f'{f}.png').convert('RGBA'))
    px.append(a[a[..., 3] > 0][:, :3])
nat = np.concatenate(px).astype(np.float64) / 255.0
hsv = np.array([colorsys.rgb_to_hsv(*c) for c in nat]); H = hsv[:, 0] * 360; S = hsv[:, 1]; V = hsv[:, 2]
NATIVE = {'skin': ((H < 15) | (H > 345)) & (S > 0.5) & (V > 0.25),
          'suckers': (H >= 40) & (H <= 75) & (S > 0.4),
          'iris': (H >= 200) & (H <= 245) & (S > 0.45) & (V > 0.45)}
GAIN = {'skin': 1.2, 'suckers': 1.2, 'iris': 1.15}


def target_native(region, weight):
    nlin = RV.srgb_to_linear(nat[NATIVE[region]]); nl = nlin @ RV.LUMA
    order = np.argsort(nl); nlin, nl = nlin[order], nl[order]
    chroma = nlin / np.maximum(nl, 1e-4)[:, None]
    lum = RV.luminance(base)
    sel = weight > 0.05
    q = np.zeros_like(lum)
    vals = lum[sel]; ranks = np.argsort(np.argsort(vals))
    q[sel] = ranks / max(1, len(vals) - 1)
    qq = np.clip(q, 0.15, 0.95)
    nq = np.linspace(0, 1, len(nl))
    grid = np.linspace(0.15, 0.95, 33)
    table = np.array([chroma[(nq >= g - 0.1) & (nq <= g + 0.1)].mean(0) for g in grid])
    c = np.stack([np.interp(qq, grid, table[:, k]) for k in range(3)], -1)
    k = GAIN[region] * nl.mean() / max(vals.mean(), 1e-4)
    out_lin = np.clip(c * (lum * k)[..., None], 0, 1)
    enc = np.where(out_lin <= 0.0031308, out_lin * 12.92, 1.055 * out_lin ** (1 / 2.4) - 0.055)
    return np.where(sel[..., None], enc, base), dict(native_px=int(NATIVE[region].sum()), gain=round(float(k), 3),
                                                   native_median_srgb=(np.median(nat[NATIVE[region]], 0) * 255).round().tolist())


def hsv_recolour(rgb, hue_deg=None, sat_k=1.0, val_k=1.0):
    """Keep each texel's value (scaled); set its hue (or keep it when None) and scale its saturation."""
    rgb = np.clip(rgb, 0, 1)
    mx = rgb.max(-1); mn = rgb.min(-1); c = mx - mn
    s = np.clip(np.where(mx > 1e-6, c / np.maximum(mx, 1e-6), 0) * sat_k, 0, 1)
    v = np.clip(mx * val_k, 0, 1)
    if hue_deg is None:
        h = np.zeros_like(mx)
        r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        m = c > 1e-6
        hr = m & (mx == r); hg = m & (mx == g) & ~hr; hb = m & ~hr & ~hg
        h[hr] = ((g - b)[hr] / c[hr]) % 6; h[hg] = (b - r)[hg] / c[hg] + 2; h[hb] = (r - g)[hb] / c[hb] + 4
    else:
        h = np.full_like(mx, (hue_deg / 60.0) % 6)
    i = np.floor(h).astype(int) % 6; f = h - np.floor(h)
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    out = np.zeros_like(rgb)
    for k, (a, b2, c2) in enumerate(((v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q))):
        sel = i == k
        out[sel] = np.stack([a[sel], b2[sel], c2[sel]], -1)
    return out


DESIGN = {'octopod_b': {'skin': (285, 0.9, 0.82), 'suckers': (46, 0.62, 1.05), 'iris': (40, 1.0, 1.1)},
          'octopod_c': {'skin': (165, 0.45, 0.6), 'suckers': (50, 0.28, 1.0), 'iris': (10, 1.0, 1.15)}}
variants = ['octopod_a', 'octopod_b', 'octopod_c']
ramps = {v: [] for v in variants}; report = {}; native = {}
for channel, region in zip('RGB', ('skin', 'suckers', 'iris')):
    weight = np.asarray(mask.getchannel(channel), np.float64) / 255.0
    ta, info = target_native(region, weight)
    tiers = {'octopod_a': ta}
    for v in ('octopod_b', 'octopod_c'):
        tiers[v] = hsv_recolour(ta, *DESIGN[v][region])
    native[region] = info
    r, rep = RV.fit_ramps(base, tiers, weight)
    for v in variants:
        ramps[v].append(r[v])
    report[region] = rep
    for v in variants:
        Image.fromarray((np.clip(tiers[v], 0, 1) * 255 + 0.5).astype(np.uint8)).save(
            ROOT / 'work' / f'tier_target_{v}_{region}.png')
out = {'variants': variants,
       'materials': [{'base': 'Octopod_A', 'prefix': 'Octopod', 'mask': 'octopod_region_mask.png', 'ramps': ramps}],
       'regions': ['R skin (head, tentacles, the flesh round the eyes)', 'G suckers (pieces and painted rings)',
                   'B irises (the pupils in none)'],
       'design': {v: {k: list(x) for k, x in d.items()} for v, d in DESIGN.items()},
       'native': native, 'fit_report': report}
json.dump(out, open(ROOT / 'textures/octopod_ramps.json', 'w'), indent=1)
print('RAMPS', json.dumps(report))
print('NATIVE', json.dumps(native))
