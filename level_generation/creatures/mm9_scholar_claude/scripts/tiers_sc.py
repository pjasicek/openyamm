#!/usr/bin/env python3
"""Tier ramps on the one body paint (Bembridge Scholar; after the Wyrde's tiers_wy.py). MM9's two skins are one design: the Scholar (row 274,
scholar1) a dark navy robe, the Master Scholar (row 275, scholar3) a mid-blue robe; the charcoal stole, its gold chain and medallion, the brown
belt, the grey cuff and hem bands, hands and shoes are the same and keep the paint. Faces, hair, beard and cap are the per-tier head sets.
Region R robe: our paint's blue cloth texels (hue 190-255, saturation > SATMIN) on the robe part, padded into the gutters, softened 1 px.
Ramps map our luminance quantiles (linear) onto MM9's own blue texels of each tier's skin (the same ramp() as the Wyrde's).
Writes textures/sc_body_mask.png, textures/sc_ramps.json, review/tier_mask_preview.png. Project folder."""
import json, os
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ni
T = Path('textures'); STOPS = 16
SATMIN = float(os.environ.get('SATMIN', '0.35'))
def load(p): return np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
def lin(a): return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
LUMA = np.array([0.2126, 0.7152, 0.0722])
base = load(T / ('sc_body_tone.png' if (T / 'sc_body_tone.png').exists() else 'sc_body_final.png')); W = base.shape[0]
part = np.load('work/texel_part.npy'); names = [str(x) for x in np.load('work/asm.npz')['names']]
if part.shape[0] != W: part = np.asarray(Image.fromarray(part.astype(np.int16)).resize((W, W), Image.NEAREST))
hsv = np.asarray(Image.fromarray((base * 255).astype('u1')).convert('HSV'), np.float32) / 255
h, s, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
robe = (part == names.index('robe')) & (h > 190) & (h < 255) & (s > SATMIN)
robe = ni.binary_opening(robe, iterations=1)
cov = part >= 0
# pad into the gutters (nearest chart texel's label), soften 1 px, zero outside the robe's own charts' neighbourhood
idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True)
m = robe[idx[0], idx[1]].astype(np.float32)
m = ni.gaussian_filter(m, 1.0)
BT = lin(base)
def ramp(weight, target):
    l = BT @ LUMA; w = weight > 0.5
    lv = np.sort(l[w]); lo, hi = float(np.percentile(lv, 0.5)), float(np.percentile(lv, 99.5)); hi = max(hi, lo + 0.02)
    lt = target @ LUMA; order = np.argsort(lt); ts = target[order]; n = len(ts)
    stops = lo + (hi - lo) * np.arange(STOPS) / (STOPS - 1); cols = []
    for x in stops:
        q = np.searchsorted(lv, x) / len(lv); a = int(np.clip(q - 0.04, 0, 1) * n); b = max(a + 1, int(np.clip(q + 0.04, 0, 1) * n)); cols.append(ts[a:b].mean(0))
    return {'range': [lo, hi], 'colors': np.clip(np.array(cols), 0, 1).tolist()}
def mm9_blues(png):
    sk = load(png); kh = np.asarray(Image.fromarray((sk * 255).astype('u1')).convert('HSV'), np.float32) / 255
    sel = (kh[..., 0] * 360 > 190) & (kh[..., 0] * 360 < 255) & (kh[..., 1] > 0.25) & (kh[..., 2] > 0.08)
    print(png, 'blue texels', int(sel.sum()), 'median', (np.median(sk[sel], 0) * 255).round(0))
    return lin(sk[sel])
VAR = {'sc_a': 'source/mm9/scholar/skins/scholar.png', 'sc_b': 'source/mm9/scholar_SCHOLAR3/skins/scholar_SCHOLAR3.png'}
ramps = {k: [ramp(m, mm9_blues(p))] for k, p in VAR.items()}
mask = np.zeros((W, W, 3), np.uint8); mask[..., 0] = (np.clip(m, 0, 1) * 255 + 0.5).astype('u1')
Image.fromarray(mask, 'RGB').resize((1024, 1024), Image.BILINEAR).save(T / 'sc_body_mask.png')      # RGB: an RGBA with A = 0 lost R in the resize
json.dump({'variants': list(VAR), 'materials': [{'base': 'Scholar', 'prefix': 'Scholar', 'mask': 'sc_body_mask.png', 'ramps': ramps}]}, open(T / 'sc_ramps.json', 'w'))
pv = (base * 255).astype('u1').copy(); pv[m > 0.5] = (pv[m > 0.5] * 0.4 + np.array([255, 0, 0]) * 0.6).astype('u1')
Path('review').mkdir(exist_ok=True); Image.fromarray(pv).resize((1024, 1024)).save('review/tier_mask_preview.png')
print('TIERS robe texels', int(robe.sum()), {k: [round(x, 4) for x in r[0]['range']] for k, r in ramps.items()})
