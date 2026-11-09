#!/usr/bin/env python3
"""Skin colour proposal (MONSTERS.md "Kreegan skin colours", user decision 2026-10-24: the Nobles' own hue family, three
clearly different tier hues, C the darkest; each Court member and the Gatekeeper its own colour; none of the caste
tier colours). Bakes preview textures per candidate: the body/head skin region (mask R) re-coloured by an authored
ramp around the candidate's mid-tone (tier_ramps.authored), the carapace by its tier's fitted ramps; the renders come
from proposal_render.py. Writes work/proposal/<key>_{body,head,plate}.png and work/proposal/candidates.json.
Args: none"""
import json, os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'claude_shared'))
import region_variants as rv
T = os.path.join(HERE, 'textures'); O = os.path.join(HERE, 'work', 'proposal'); os.makedirs(O, exist_ok=True)
lin = rv.srgb_to_linear; LUMA = np.array([0.2126, 0.7152, 0.0722])
enc = lambda x: np.where(x <= 0.0031308, x * 12.92, 1.055 * np.maximum(x, 0) ** (1 / 2.4) - 0.055)
hexc = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
CANDIDATES = [   # key, label, skin mid-tone (sRGB, 70 % of the ramp as the swatch sheet), carapace tier
    ('noble_a', 'Noble A: jade', '#3f8a64', 'nb_a'),
    ('noble_b', 'Noble Duellist B: garnet', '#8c2c48', 'nb_b'),
    ('noble_c', 'Court Noble C: midnight sapphire', '#1e2a5a', 'nb_c'),
    ('ssekh', 'Lady Ssekh: rose tourmaline', '#b0527c', 'nb_c'),
    ('mraal', 'Lord Mraal: obsidian iron', '#3c4652', 'nb_c'),
    ('xith', 'Lord Xith: amethyst', '#6a3fb0', 'nb_c'),
    ('gatekeeper', 'The Gatekeeper: steel turquoise', '#2d7f8c', 'nb_c'),
]


def ramp_apply(img, w, ramp):
    lum = lin(img) @ LUMA; lo, hi = ramp['range']; C = np.array(ramp['colors'])
    t = np.clip((lum - lo) / max(hi - lo, 1e-6), 0, 1) * (len(C) - 1)
    i = np.minimum(t.astype(int), len(C) - 2); f = (t - i)[..., None]
    col = C[i] * (1 - f) + C[i + 1] * f
    return enc(lin(img) * (1 - w[..., None]) + col * w[..., None])


def authored(lum, w, anchors, gain):       # as tier_ramps.authored
    core = w > 0.9; lo, hi = np.percentile(lum[core], 0.5), np.percentile(lum[core], 99.5)
    a = [lin(np.array(c) / 255.0) for c in anchors]
    stops = []
    for i in range(16):
        t = i / 15
        c = a[0] * (1 - 2 * t) + a[1] * 2 * t if t < 0.5 else a[1] * (2 - 2 * t) + a[2] * (2 * t - 1)
        L = (lo + t * (hi - lo)) * gain
        stops.append(np.clip(c * L / max(c @ LUMA, 1e-6), 0, 1))
    return {'range': [float(lo), float(hi)], 'colors': np.array(stops).tolist()}


def authored_from_mid(lum, w, mid):
    m = np.array(hexc(mid)) / 255.0
    shadow = np.clip(m * 0.38, 0, 1); high = np.clip(m * 1.45 + 0.12, 0, 1)
    return authored(lum, w, [tuple(shadow * 255), tuple(m * 255), tuple(high * 255)], 1.1)


ramps = json.load(open(os.path.join(T, 'nb_ramps.json')))
plate_r = next(x for x in ramps['materials'] if x['base'] == 'NB_Plate')['ramps']
plate = rv.load_srgb(os.path.join(T, 'nb_carapace_basecolor.png'))
pm = np.asarray(Image.open(os.path.join(T, 'nb_carapace_region_mask.png')).convert('RGB')) / 255.0
srcs = {}
for part, src, mask in (('body', 'nb_body_basecolor_source.png', 'winged_body_region_mask.png'),
                        ('head', 'nb_head_basecolor_source.png', 'winged_head_region_mask.png')):
    img = rv.load_srgb(os.path.join(T, src))
    m = np.asarray(Image.open(os.path.join(T, mask)).convert('RGB').resize(img.shape[1::-1], Image.BILINEAR))[..., 0] / 255.0
    srcs[part] = (img, m, lin(img) @ LUMA)
out = []
for key, label, mid, tier in CANDIDATES:
    for part, (img, m, lum) in srcs.items():
        res = ramp_apply(img, m, authored_from_mid(lum, m, mid))
        Image.fromarray((np.clip(res, 0, 1) * 255).astype(np.uint8)).save(os.path.join(O, f'{key}_{part}.png'))
    res = ramp_apply(ramp_apply(plate, pm[..., 0], plate_r[tier][0]), pm[..., 1], plate_r[tier][1])
    Image.fromarray((np.clip(res, 0, 1) * 255).astype(np.uint8)).save(os.path.join(O, f'{key}_plate.png'))
    out.append({'key': key, 'label': label, 'mid': mid, 'tier': tier})
json.dump(out, open(os.path.join(O, 'candidates.json'), 'w'), indent=1)
print('PROPOSAL', [c[0] for c in CANDIDATES])
