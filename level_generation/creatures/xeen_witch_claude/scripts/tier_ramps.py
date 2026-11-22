#!/usr/bin/env python3
"""Witch skins: one shared body set, region R = the robe (red coat-robe, its tatters and the red right wrist wrap, by
the paint's hue; mask, skin, hair, panel, cord, beads, boots outside it). Ramps follow CLAUDE_CREATURE_TEXTURES.md:
each tier's palette entries sorted by luminance and resampled to 16 stops, mapped onto the region's texel luminance
percentiles (2-98), albedo x1.35 the native colour (the sprite carries baked shading).
Xeen draws Wicked Witch, Witch and Head Witch with one sprite and one palette (image 76), so only A is native:
  witch_a  Wicked Witch  the native blood-red robe: (88,0,0) (108,0,0) (128,0,0) (148,0,0) (168,0,0) (212,68,68)
  witch_b  Witch         deep violet-purple robe (design choice): the A shades turned to hue 282, saturation x0.85
  witch_c  Head Witch    black robe (design choice; the gold mask stays gold, so C reads as the leader): near-black
                         shades with a faint wine undertone, (14,10,12) .. (78,64,72)
Writes textures/witch_ramps.json (region_variants.py format) with the palette sources and the fit report."""
import colorsys, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as RV

NATIVE_A = [(88, 0, 0), (108, 0, 0), (128, 0, 0), (148, 0, 0), (168, 0, 0), (212, 68, 68)]


def shades_b():
    out = []
    for c in NATIVE_A:
        h, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in c))
        r, g, b = colorsys.hsv_to_rgb(282 / 360, min(1, s * 0.85), v * 0.95)
        out.append((r * 255, g * 255, b * 255))
    return out


SHADES_C = [(14, 10, 12), (24, 18, 21), (34, 26, 30), (46, 36, 41), (60, 48, 54), (78, 64, 72)]
TIERS = {'witch_a': NATIVE_A, 'witch_b': shades_b(), 'witch_c': SHADES_C}
GAIN = 1.35


def ramp(shades, lum, core):
    lin = RV.srgb_to_linear(np.clip(np.array(shades, float) * GAIN / 255.0, 0, 1))
    order = np.argsort(lin @ RV.LUMA); lin = lin[order]
    pos = np.linspace(0, 1, len(lin)); t = np.linspace(0, 1, 16)
    cols = np.stack([np.interp(t, pos, lin[:, k]) for k in range(3)], -1)
    lo, hi = np.percentile(lum[core], 2), np.percentile(lum[core], 98)
    return {'range': [round(float(lo), 5), round(float(max(hi, lo + 1e-3)), 5)], 'colors': np.round(cols, 5).tolist()}


base = RV.load_srgb(ROOT / 'textures/witch_basecolor_graded.png', 1024)
weight = np.asarray(Image.open(ROOT / 'textures/witch_region_mask.png').getchannel('R').resize((1024, 1024)), np.float64) / 255
lum = RV.luminance(base); core = weight > 0.9
ramps = {v: [ramp(s, lum, core)] for v, s in TIERS.items()}
# report: tier A ramp against the shared base inside the region (mean 8-bit error of the luminance-mapped colour)
r = ramps['witch_a'][0]; t = np.clip((lum[core] - r['range'][0]) / (r['range'][1] - r['range'][0]), 0, 1)
cols = np.array(r['colors']); x = t * 15; i0 = np.minimum(x.astype(int), 14); f = (x - i0)[:, None]
pred = cols[i0] * (1 - f) + cols[i0 + 1] * f
err = np.abs(RV.linear_to_srgb(pred) - base[core]).mean() * 255 if hasattr(RV, 'linear_to_srgb') else None
report = {'region_texels_1k': int(core.sum()), 'tier_a_vs_paint_mean_8bit': None if err is None else round(float(err), 1),
          'palettes': {k: [[round(c, 1) for c in s] for s in v] for k, v in TIERS.items()}, 'gain': GAIN}
json.dump({'variants': list(TIERS), 'materials': [{'base': 'Witch_A', 'prefix': 'Witch', 'mask': 'witch_region_mask.png',
           'ramps': ramps}], 'fit_report': report}, open(ROOT / 'textures/witch_ramps.json', 'w'), indent=1)
print('RAMPS', json.dumps(report)[:400])
