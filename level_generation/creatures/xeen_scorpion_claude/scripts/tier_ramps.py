#!/usr/bin/env python3
"""Skin ramps of the scorpion model (CLAUDE_CREATURE_TEXTURES.md): one shared graded paint, four regions: R carapace
(body, tail segments, chelicerae), G legs and pincers, B stinger (bulb and sting), A eyes. Xeen draws one Giant
Scorpion sprite (Clouds image 19) for tier A; tiers B and C of the family are other models, but the mask allows later
recolours of this one by numbers only.
  scorpion_a   Scorpion   native: the sprite's dark glossy brown at about 1.35x its median (sprites carry baked
                          shading): carapace 76,48,28 -> 103,65,38, legs and claws 64,44,28 -> 90,59,37, the lighter
                          tan stinger bulb 120,76,40 -> 156,99,52; the eyes keep the paint
Modes per region: ('mid', sRGB, contrast) sets the region's average shown colour and keeps each texel's luminance
ratio to the region mean (shading and gloss survive, the hue becomes uniform, as in the sprite); ('hsv', hue or
None, sat x, value x) keeps the texel's value. Then the shader's ramp is fitted (region_variants.fit_ramps).
Writes textures/scorpion_ramps.json with the fit report."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as RV

base = RV.load_srgb(ROOT / 'textures/scorpion_basecolor_graded.png', 1024)
mask = Image.open(ROOT / 'textures/scorpion_region_mask.png')
LW = np.array([0.2126, 0.7152, 0.0722])


def lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def enc(c):
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def mid_recolour(rgb, weight, colour, contrast=1.0):
    lum = lin(rgb) @ LW
    core = weight >= 0.9
    mean = float(lum[core].mean())
    ratio = np.clip(lum / max(mean, 1e-4), 0, 8) ** contrast
    target = lin(np.array(colour, np.float64) / 255.0)
    return np.clip(enc(target[None, None, :] * ratio[..., None]), 0, 1)


def hsv_recolour(rgb, hue_deg=None, sat_k=1.0, val_k=1.0):
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


DESIGN = {
    'carapace': {'scorpion_a': ('mid', (103, 65, 38), 1.1)},
    'limbs': {'scorpion_a': ('mid', (90, 59, 37), 1.1)},
    'stinger': {'scorpion_a': ('mid', (156, 99, 52), 1.05)},
    'eyes': {'scorpion_a': ('hsv', None, 1.0, 1.0)},
}
variants = ['scorpion_a']
ramps = {v: [] for v in variants}; report = {}
for channel, region in zip('RGBA', DESIGN):
    weight = np.asarray(mask.getchannel(channel), np.float64) / 255.0
    tiers = {}
    for v in variants:
        spec = DESIGN[region][v]
        tiers[v] = mid_recolour(base, weight, spec[1], spec[2]) if spec[0] == 'mid' else hsv_recolour(base, *spec[1:])
    r, rep = RV.fit_ramps(base, tiers, weight)
    for v in variants:
        ramps[v].append(r[v])
    report[region] = rep
out = {'variants': variants,
       'materials': [{'base': 'Scorpion_A', 'prefix': 'Scorpion', 'mask': 'scorpion_region_mask.png', 'ramps': ramps}],
       'regions': ['R carapace', 'G legs and pincers', 'B stinger', 'A eyes'],
       'design': {reg: {v: [x if x is not None else 'kept' for x in d] for v, d in t.items()}
                  for reg, t in DESIGN.items()},
       'fit_report': report}
json.dump(out, open(ROOT / 'textures/scorpion_ramps.json', 'w'), indent=1)
print('RAMPS', json.dumps(report))
