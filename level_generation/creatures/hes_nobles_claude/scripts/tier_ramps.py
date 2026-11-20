#!/usr/bin/env python3
"""The Nobles' tiers (one shared texture set per material + region masks + ramps, CLAUDE_CREATURE_TEXTURES.md). No
native palette (a Hesper creature): the colours come from the approved fam_nobles.png / CODEX_BRIEF_NOBLES.md table.
- Skin (NB_Body, NB_Head: the winged body's own base colour, hes_overseer_codex's region masks, R = skin): authored
  ramps, 16 stops over the region's luminance range, each stop the variant's colour (shadow -> mid -> highlight around
  the approved mid-tone, SKIN_MID) scaled to the stop's luminance x GAIN, so the painted scales and shading stay.
  Seven variants: the Noble tiers A-C and the four named rows (MONSTERS.md "Kreegan skin colours"). Horns, claws and wing membranes keep their native colours (no region).
- Carapace (NB_Plate, textures/nb_carapace_*: R gold, G ivory insert and spikes, B painted glow): region_variants
  .fit_ramps against target images made from the base: A antique gold with bone inserts, B warm bronze-gold with
  scorched ivory, C pale rich gold with ivory.
Writes textures/nb_ramps.json. Args: none"""
import json, os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'claude_shared'))
import region_variants as rv
T = os.path.join(HERE, 'textures')
lin = rv.srgb_to_linear
LUMA = np.array([0.2126, 0.7152, 0.0722])
enc = lambda x: np.where(x <= 0.0031308, x * 12.92, 1.055 * np.maximum(x, 0) ** (1 / 2.4) - 0.055)


def authored(lum, w, anchors, gain):
    core = w > 0.9; lo, hi = np.percentile(lum[core], 0.5), np.percentile(lum[core], 99.5)
    a = [lin(np.array(c) / 255.0) for c in anchors]
    stops = []
    for i in range(16):
        t = i / 15
        c = a[0] * (1 - 2 * t) + a[1] * 2 * t if t < 0.5 else a[1] * (2 - 2 * t) + a[2] * (2 * t - 1)
        L = (lo + t * (hi - lo)) * gain
        stops.append(np.clip(c * L / max(c @ LUMA, 1e-6), 0, 1))
    return {'range': [round(float(lo), 6), round(float(hi), 6)], 'colors': np.round(np.array(stops), 6).tolist()}


# skin mid-tones (sRGB), user-approved 2026-10-24 (review/proposal/sheet.png): the Nobles' own jewel family, C the
# darkest; each Court member and the Gatekeeper its own colour; carapace tier per row (the Court and the Gatekeeper
# wear the Court Noble's pale gold). gain < 1 darkens a ramp toward its swatch.
SKIN_MID = {'nb_a': ('#3f8a64', 1.05), 'nb_b': ('#8c2c48', 1.0), 'nb_c': ('#1e2a5a', 0.5),
            'nb_ssekh': ('#c25a8e', 1.05), 'nb_mraal': ('#3c4652', 0.95), 'nb_xith': ('#6a3fb0', 1.0),
            'nb_gatekeeper': ('#2d7f8c', 1.0)}
PLATE_TIER = {'nb_a': 'nb_a', 'nb_b': 'nb_b', 'nb_c': 'nb_c', 'nb_ssekh': 'nb_c', 'nb_mraal': 'nb_c', 'nb_xith': 'nb_c',
              'nb_gatekeeper': 'nb_c'}
VAR = list(SKIN_MID)


def mid_anchors(h):
    m = np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)]) / 255.0
    return [tuple(np.clip(m * 0.38, 0, 1) * 255), tuple(m * 255), tuple(np.clip(m * 1.45 + 0.12, 0, 1) * 255)]


SKIN = {v: (mid_anchors(h), g * 1.1) for v, (h, g) in SKIN_MID.items()}
mats = []
for base, src, mask in (('NB_Body', 'nb_body_basecolor_source.png', 'winged_body_region_mask.png'),
                        ('NB_Head', 'nb_head_basecolor_source.png', 'winged_head_region_mask.png')):
    img = rv.load_srgb(os.path.join(T, src))
    m = np.asarray(Image.open(os.path.join(T, mask)).convert('RGB').resize(img.shape[1::-1], Image.BILINEAR)) / 255.0
    lum = lin(img) @ LUMA
    mats.append({'base': base, 'prefix': base, 'mask': mask, 'ramps': {v: [authored(lum, m[..., 0], *SKIN[v])] for v in VAR}})
arm = rv.load_srgb(os.path.join(T, 'nb_carapace_basecolor.png'))
am = np.asarray(Image.open(os.path.join(T, 'nb_carapace_region_mask.png')).convert('RGB')) / 255.0
alum = lin(arm) @ LUMA


def recolour(region, rgb, gain=1.0):
    """the base's own relative luminance in the region, carried by a new colour"""
    rel = (alum / max(np.median(alum[am[..., region] > 0.9]), 1e-6))[..., None]
    return enc(np.clip(lin(np.array(rgb) / 255) * rel * gain, 0, 1))


targets_gold = {'nb_a': recolour(0, (196, 150, 70)), 'nb_b': recolour(0, (178, 112, 52)), 'nb_c': recolour(0, (232, 196, 110), 1.08)}
targets_iv = {'nb_a': recolour(1, (222, 206, 172)), 'nb_b': recolour(1, (190, 162, 128)), 'nb_c': recolour(1, (236, 228, 206), 1.04)}
rg, rep_g = rv.fit_ramps(arm, targets_gold, am[..., 0])
ri, rep_i = rv.fit_ramps(arm, targets_iv, am[..., 1])
rg = {v: rg[PLATE_TIER[v]] for v in VAR}; ri = {v: ri[PLATE_TIER[v]] for v in VAR}
mats.append({'base': 'NB_Plate', 'prefix': 'NB_Plate', 'mask': 'nb_carapace_region_mask.png',
             'ramps': {v: [rg[v], ri[v]] for v in VAR}})   # (B, painted glow, is unused: the seams are NB_Glow geometry)
json.dump({'variants': VAR, 'materials': mats}, open(os.path.join(T, 'nb_ramps.json'), 'w'), indent=1)
print('RAMPS', VAR, 'fit', {k: v for k, v in (('gold', rep_g), ('ivory', rep_i))})
