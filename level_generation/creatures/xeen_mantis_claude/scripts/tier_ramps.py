#!/usr/bin/env python3
"""Skin ramps of the mantis model (CLAUDE_CREATURE_TEXTURES.md): one shared graded paint, four regions: R chitin,
G ball joints, B eyes, A underside + radial mouth (charcoal abdomen front and the yellow petals: luminance keeps them
apart inside one ramp). The red abdomen tip and the dark mouth centre are in no region.
Xeen draws one Mantis Ant sprite (Darkside image 10) for the three mantis tiers and its own Lava Roach (image 33):
  mantis_a     Mantis Ant      native: violet chitin and joints at 1.3x the sprite's purple (median 76,0,128), the
                               sprite's teal eyes, the paint's charcoal underside and yellow mouth
  mantis_b     Mantis Warrior  design: dark bronze-green chitin, polished bronze joints, amber eyes, bronze-brown
                               underside and ochre mouth (a soldier caste in old bronze; reads olive at distance)
  mantis_c     Mantis Queen    design: black-violet chitin, gold joints, crimson eyes, gold mouth (royalty: the
                               darkest silhouette with bright gold points, apart from A's vivid violet)
  mantis_lava  Lava Roach      native colours of image 33: dark grey chitin, dark red joints (they glow, see
                               build_runtime.sh emission), red eyes, dark red underside and mouth
Modes per region: ('mid', sRGB, contrast) sets the region's average shown colour and keeps each texel's luminance
ratio to the region mean (shading and detail survive, the hue becomes uniform, as in the sprites); ('hsv', hue or
None, sat x, value x) keeps the texel's value. Then the shader's ramp is fitted (region_variants.fit_ramps).
Writes textures/mantis_ramps.json with the fit report."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as RV

base = RV.load_srgb(ROOT / 'textures/mantis_basecolor_graded.png', 1024)
mask = Image.open(ROOT / 'textures/mantis_region_mask.png')
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
    'chitin': {'mantis_a': ('mid', (104, 14, 170), 1.0), 'mantis_b': ('mid', (82, 90, 42), 1.0),
               'mantis_c': ('mid', (54, 30, 70), 1.15), 'mantis_lava': ('mid', (76, 72, 72), 1.1)},
    'joints': {'mantis_a': ('mid', (112, 18, 178), 1.0), 'mantis_b': ('mid', (160, 112, 48), 1.1),
               'mantis_c': ('mid', (212, 166, 52), 1.1), 'mantis_lava': ('mid', (120, 34, 16), 1.0)},
    'eyes': {'mantis_a': ('mid', (44, 128, 134), 1.0), 'mantis_b': ('mid', (232, 150, 24), 1.0),
             'mantis_c': ('mid', (220, 30, 52), 1.0), 'mantis_lava': ('mid', (236, 36, 16), 1.0)},
    'under_mouth': {'mantis_a': ('hsv', None, 1.0, 1.0), 'mantis_b': ('hsv', 36, 0.85, 1.0),
                    'mantis_c': ('hsv', 46, 0.95, 1.1), 'mantis_lava': ('hsv', 8, 0.9, 0.8)},
}
variants = ['mantis_a', 'mantis_b', 'mantis_c', 'mantis_lava']
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
       'materials': [{'base': 'Mantis_A', 'prefix': 'Mantis', 'mask': 'mantis_region_mask.png', 'ramps': ramps}],
       'regions': ['R chitin', 'G ball joints', 'B eyes', 'A underside + radial mouth'],
       'design': {reg: {v: [x if x is not None else 'kept' for x in d] for v, d in t.items()}
                  for reg, t in DESIGN.items()},
       'fit_report': report}
json.dump(out, open(ROOT / 'textures/mantis_ramps.json', 'w'), indent=1)
print('RAMPS', json.dumps(report))
