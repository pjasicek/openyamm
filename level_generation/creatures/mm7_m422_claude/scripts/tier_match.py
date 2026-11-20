#!/usr/bin/env python3
"""Tier colour check (adapted from mm7_m294_claude/scripts/tier_match.py): RENDERED viewer shots vs NATIVE frames,
median sRGB luminance and chroma per tier and region, and the ramp gain that would match.
Regions: coat (front shot vs m422sa0, indices 137-169), cape (back shot vs m422sa4, 202-239), hair (head shot vs
m422sa0+sa4, 85-101). Rendered pixels: the same pixels in every tier (same pose and camera), those whose colour
CHANGES between the tier shots (the region recolours; background, skin, gold and boots do not) and that have the
region's hue in the tier-B shot (blue coat, burgundy cape, grey hair). Native pixels: the region's indices in the
indexed bitmap, outline-black pixels (luminance < 0.02 in every palette) left out.
Args: none (shots review/shots/<tier>_tm{front,back,head}.png); reads textures/m422_ramp_gains.json for the current gains."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
H = Path(__file__).resolve().parents[1]; REPO = H.parents[2]
W = np.array([0.2126, 0.7152, 0.0722])
src = json.load(open(H.parent / 'mm7_m422' / 'sources.json'))['sources']
V = {r['name']: r['palette_indices'] for r in json.load(open(H.parent / 'mm7_m422' / 'variants.json'))['regions']}
PAL = {'a': 99, 'b': 104, 'c': 105}
pal = {t: np.frombuffer(open(REPO / f'assets_dev/worlds/mm7/textures/pal{p:03d}.act', 'rb').read()[:768], np.uint8)
       .reshape(256, 3).astype(float) / 255 for t, p in PAL.items()}
G = json.load(open(H / 'textures' / 'm422_ramp_gains.json')) if (H / 'textures' / 'm422_ramp_gains.json').exists() else {}
REG = {'coat': ('blue_coat', ['m422sa0'], 'tmfront', 'robe'), 'cape': ('burgundy_cape', ['m422sa4'], 'tmback', 'cape'),
       'hair': ('hair', ['m422sa0', 'm422sa4'], 'tmhead', 'beard')}


def hsv(rgb):
    h = np.asarray(Image.fromarray(np.clip(rgb * 255, 0, 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    return h[..., 0] * 360, h[..., 1], h[..., 2]


out = {}
for reg, (vname, frames, shot, gkey) in REG.items():
    S = {t: np.asarray(Image.open(H / 'review' / 'shots' / f'm422_{t}_{shot}.png').convert('RGB')).astype(float) / 255
         for t in PAL}
    diff = np.maximum(np.abs(S['a'] - S['b']).max(-1), np.abs(S['c'] - S['b']).max(-1)) > 0.03
    h, s, v = hsv(S['b'])
    hue = {'coat': (h > 190) & (h < 265) & (s > 0.35), 'cape': ((h > 330) | (h < 25)) & (s > 0.25),
           'hair': (s < 0.2) & (v < 0.6)}[reg]
    m = diff & hue & (v > 0.03)
    nat = {t: [] for t in PAL}
    for f in frames:
        ix = np.asarray(Image.open(REPO / src[f]['path']))
        sel = ix[np.isin(ix, V[vname])]
        keep = np.max([pal[t][sel] @ W for t in PAL], 0) > 0.02
        for t in PAL:
            nat[t].append(pal[t][sel][keep])
    out[reg] = {}
    for t in PAL:
        N = np.concatenate(nat[t]); R = S[t][m]
        nl, rl = float(np.median(N @ W)), float(np.median(R @ W))
        nc, rc = float(np.median(N.max(1) - N.min(1))), float(np.median(R.max(1) - R.min(1)))
        g = float(G.get(gkey, {}).get(f'm422_{t}', 1.35))
        out[reg][t] = {'pixels': int(m.sum()), 'native_rgb': np.round(np.median(N, 0) * 255).tolist(),
                       'render_rgb': np.round(np.median(R, 0) * 255).tolist(), 'native_lum': round(nl, 4),
                       'render_lum': round(rl, 4), 'native_chroma': round(nc, 4), 'render_chroma': round(rc, 4),
                       'gain': g, 'gain_to_match': round(g * nl / max(rl, 1e-4), 3)}
        print('MATCH', reg, t, json.dumps(out[reg][t]))
json.dump(out, open(H / 'review' / 'tier_match.json', 'w'), indent=1)
