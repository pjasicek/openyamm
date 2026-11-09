#!/usr/bin/env python3
"""Tunic colour check per tier: RENDERED (viewer shots) vs NATIVE (standing frames m294sa0-4) median luminance and
chroma, sRGB. Same pixels across tiers on both sides: the native pixels are the region indices (188-232) whose
palette-295 colour is purple (hue > 270 or < 20, S > 0.35, V > 0.08), the rendered pixels are those purple in the
tier-A shot (same pose and camera in every tier). Prints the ratio rendered/native and the gain that would match.
Args: <shot name stem, e.g. 1 for review/shots/{a,b,c}1.png> [current gains a,b,c]"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
H = Path(__file__).resolve().parents[1]; REPO = H.parents[2]
W = np.array([0.2126, 0.7152, 0.0722])
stem = sys.argv[1]; gains = [float(x) for x in (sys.argv[2] if len(sys.argv) > 2 else '1,1,1').split(',')]
src = json.load(open(H.parent / 'mm7_m294' / 'sources.json'))['sources']
IDX = json.load(open(H.parent / 'mm7_m294' / 'variants.json'))['regions'][0]['palette_indices']
pal = {p: np.frombuffer(open(REPO / f'assets_dev/worlds/mm7/textures/pal{p}.act', 'rb').read()[:768], np.uint8).reshape(256, 3)
       for p in (295, 296, 297)}


def purple(rgb):
    hsv = np.asarray(Image.fromarray(rgb.astype(np.uint8)).convert('HSV'), np.float64) / 255
    h = hsv[..., 0] * 360
    return ((h > 270) | (h < 20)) & (hsv[..., 1] > 0.35) & (hsv[..., 2] > 0.08)


nat = {p: [] for p in pal}
for v in range(5):
    ix = np.asarray(Image.open(REPO / src[f'm294sa{v}']['path']))
    m = np.isin(ix, IDX) & purple(pal[295][ix])
    for p in pal:
        nat[p].append(pal[p][ix][m] / 255)
shots = {t: np.asarray(Image.open(H / 'review' / 'shots' / f'{t}{stem}.png').convert('RGB')) for t in 'abc'}
rm = purple(shots['a'])
out = {}
for (t, p), g in zip(zip('abc', (295, 296, 297)), gains):
    N = np.concatenate(nat[p]); Rr = shots[t][rm] / 255
    nl, rl = np.median(N @ W), np.median(Rr @ W)
    nc, rc = np.median(N.max(1) - N.min(1)), np.median(Rr.max(1) - Rr.min(1))
    out[t] = {'native_lum': round(float(nl), 4), 'render_lum': round(float(rl), 4), 'native_chroma': round(float(nc), 4),
              'render_chroma': round(float(rc), 4), 'native_rgb': np.round(np.median(N, 0) * 255).tolist(),
              'render_rgb': np.round(np.median(Rr, 0) * 255).tolist(), 'gain': g, 'gain_to_match': round(g * nl / max(rl, 1e-4), 3)}
    print('MATCH', t, json.dumps(out[t]))
json.dump(out, open(H / 'review' / f'tier_match_{stem}.json', 'w'), indent=1)
