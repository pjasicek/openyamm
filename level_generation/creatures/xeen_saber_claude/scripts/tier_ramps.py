#!/usr/bin/env python3
"""Tier ramps of the sabertooth (CLAUDE_CREATURE_TEXTURES.md): one shared graded paint, four regions (R tawny fur,
G pale fur of muzzle, chin, ruff, belly and inner legs, B fangs and claws, A eyes; the dark red nose and the mouth
cavity in none). Darkside draws one sabertooth (image 44) for both rows that use it (Sabertooth, Kennel Sabertooth),
so there is one skin, saber_a: the native tawny ochre. The paint's coat is already a little lighter than the
sprite's (fur median 161,107,60 against the sprite's 144,92,52; sprites carry painted shading, albedo is about 1.3x),
so tier A keeps the paint's hue and lifts the coat x1.06. Later tiers are ramp numbers only (new DESIGN rows).
Writes textures/saber_ramps.json (region_variants.py format) with the fit report."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as RV

base = RV.load_srgb(ROOT / 'textures/saber_basecolor_graded.png', 1024)
mask = Image.open(ROOT / 'textures/saber_region_mask.png')


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
    'fur':   {'saber_a': (None, 1.0, 1.06)},
    'pale':  {'saber_a': (None, 1.0, 1.02)},
    'teeth': {'saber_a': (None, 1.0, 1.00)},
    'eyes':  {'saber_a': (None, 1.0, 1.00)},
}
variants = ['saber_a']
ramps = {v: [] for v in variants}; report = {}
for channel, region in zip('RGBA', DESIGN):
    weight = np.asarray(mask.getchannel(channel), np.float64) / 255.0
    tiers = {v: hsv_recolour(base, *DESIGN[region][v]) for v in variants}
    r, rep = RV.fit_ramps(base, tiers, weight)
    for v in variants:
        ramps[v].append(r[v])
    report[region] = rep
out = {'variants': variants,
       'materials': [{'base': 'Saber_A', 'prefix': 'Saber', 'mask': 'saber_region_mask.png', 'ramps': ramps}],
       'regions': ['R tawny fur', 'G pale fur (muzzle, chin, ruff, belly, inner legs)', 'B fangs and claws', 'A eyes'],
       'design': {reg: {v: list(map(lambda x: x if x is not None else 'kept', d)) for v, d in t.items()}
                  for reg, t in DESIGN.items()},
       'fit_report': report}
json.dump(out, open(ROOT / 'textures/saber_ramps.json', 'w'), indent=1)
print('RAMPS', json.dumps(report))
