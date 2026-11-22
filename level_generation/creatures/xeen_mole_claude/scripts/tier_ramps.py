#!/usr/bin/env python3
"""Tier ramps of the moles (CLAUDE_CREATURE_TEXTURES.md): one shared graded paint, four regions (R fur, G naked skin of
hands, snout and lids, B claws, A tail; eyeballs and the pink nose tip in none). Xeen draws one mole sprite
(image 11) for all three tiers, so only A is native; B and C are design choices that must read apart at combat
distance (decision D-10): recolours of the graded paint in HSV (texel value detail kept) per region, then the
shader's ramp fitted to them (region_variants.fit_ramps).
  mole_a  Tiger Mole   the native teal-blue fur (the paint, fur x1.3 and skin x1.15 toward the sprite's albedo:
                       native fur median 32,80,88 against the paint's 24,71,75), pale skin, yellow-olive claws
  mole_b  Rock Mole    stone grey-brown fur, greyer skin, dull ochre claws, grey tail
  mole_c  Tunnel Mole  dark earth-brown fur, dusky skin, dark horn-brown claws, dark tail
Writes textures/mole_ramps.json (region_variants.py format) with the fit report."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as RV

base = RV.load_srgb(ROOT / 'textures/mole_basecolor_graded.png', 1024)
mask = Image.open(ROOT / 'textures/mole_region_mask.png')


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


DESIGN = {   # region -> tier -> (hue or None, saturation x, value x)
    'fur':   {'mole_a': (None, 1.0, 1.30), 'mole_b': (34, 0.42, 1.65), 'mole_c': (27, 0.72, 0.98)},
    'skin':  {'mole_a': (None, 1.0, 1.15), 'mole_b': (24, 0.55, 1.10), 'mole_c': (14, 1.4, 0.82)},
    'claws': {'mole_a': (None, 1.0, 1.00), 'mole_b': (42, 0.50, 0.95), 'mole_c': (36, 0.80, 0.55)},
    'tail':  {'mole_a': (None, 1.0, 1.00), 'mole_b': (30, 0.30, 1.00), 'mole_c': (22, 0.45, 0.72)},
}
variants = ['mole_a', 'mole_b', 'mole_c']
ramps = {v: [] for v in variants}; report = {}
for channel, region in zip('RGBA', DESIGN):
    weight = np.asarray(mask.getchannel(channel), np.float64) / 255.0
    tiers = {v: hsv_recolour(base, *DESIGN[region][v]) for v in variants}
    r, rep = RV.fit_ramps(base, tiers, weight)
    for v in variants:
        ramps[v].append(r[v])
    report[region] = rep
out = {'variants': variants,
       'materials': [{'base': 'Mole_A', 'prefix': 'Mole', 'mask': 'mole_region_mask.png', 'ramps': ramps}],
       'regions': ['R fur', 'G naked skin (hands, snout, lids)', 'B claws (hand and hind toe claws)', 'A tail'],
       'design': {reg: {v: list(map(lambda x: x if x is not None else 'kept', d)) for v, d in t.items()}
                  for reg, t in DESIGN.items()},
       'fit_report': report}
json.dump(out, open(ROOT / 'textures/mole_ramps.json', 'w'), indent=1)
print('RAMPS', json.dumps(report))
