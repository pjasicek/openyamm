#!/usr/bin/env python3
"""Region ramps of the armadillo (CLAUDE_CREATURE_TEXTURES.md): one shared graded paint, four regions (R red armour
and hide incl. the tail ball and spikes, G pale skin, B claws, A eyes + tongue; the dark mouth and nostrils in none).
One skin, `armadillo_a` (Xeen Sand Worm B = Armadillo, Darkside image 5): the native colours. The Meshy paint already
matches them (paint red median 200,56,50 against the sprite's 204,48,48; pale 236,160,160 in both; claws grey; the
sprite's orange-yellow eyes and green tongue), so each region keeps the paint's hue and only a gentle per-region value
and saturation trim toward the sprite (claws to the sprite's mid grey 132, eyes toward the sprite's orange). Then the
shader's ramp is fitted (region_variants.fit_ramps). The DESIGN table is where later tiers (other monsters on this
model) add their recolours.
Writes textures/dillo_ramps.json (region_variants.py format) with the fit report."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as RV

base = RV.load_srgb(ROOT / 'textures/dillo_basecolor_graded.png', 1024)
mask = Image.open(ROOT / 'textures/dillo_region_mask.png')


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
    'armour': {'armadillo_a': (None, 1.0, 1.0)},
    'pale':   {'armadillo_a': (None, 1.0, 1.0)},
    'claws':  {'armadillo_a': (None, 0.6, 0.95)},
    'eyes':   {'armadillo_a': (32, 1.0, 1.0)},
}
variants = ['armadillo_a']
ramps = {v: [] for v in variants}; report = {}
for channel, region in zip('RGBA', DESIGN):
    weight = np.asarray(mask.getchannel(channel), np.float64) / 255.0
    tiers = {v: hsv_recolour(base, *DESIGN[region][v]) for v in variants}
    if region == 'eyes':      # the tongue shares channel A: keep its own green (the eye hue applies to the eyes only)
        tiers = {v: np.where((base[..., 1] > base[..., 0])[..., None], base, tiers[v]) for v in variants}
    r, rep = RV.fit_ramps(base, tiers, weight)
    for v in variants:
        ramps[v].append(r[v])
    report[region] = rep
out = {'variants': variants,
       'materials': [{'base': 'Dillo_A', 'prefix': 'Dillo', 'mask': 'dillo_region_mask.png', 'ramps': ramps}],
       'regions': ['R red armour and hide (shell, head, legs, tail, ball, spikes)', 'G pale skin (belly bands)',
                   'B claws', 'A eyes and tongue'],
       'design': {reg: {v: list(map(lambda x: x if x is not None else 'kept', d)) for v, d in t.items()}
                  for reg, t in DESIGN.items()},
       'fit_report': report}
json.dump(out, open(ROOT / 'textures/dillo_ramps.json', 'w'), indent=1)
print('RAMPS', json.dumps(report))
