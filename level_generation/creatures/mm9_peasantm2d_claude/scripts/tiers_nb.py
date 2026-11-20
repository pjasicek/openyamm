#!/usr/bin/env python3
"""Shared limbs set: region R = the breeches. Each tier's ramp is fitted from that tier's own Meshy paint on the same layout (so the breeches' tone sits with its torso), tier A keeps our paint through a fit to itself.
Shoes and hands are in no region: MM9's shoes and hands are the same in all three skins. Writes textures/nb_limbs_mask.png, textures/nb_ramps.json. Project folder."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
sys.path.insert(0, '../claude_shared')
import region_variants as RV
T = Path('textures'); S = 896
Z = np.load('work/faces.npz'); UV, MAT, PART = Z['uv'], Z['mat'], Z['part']
im = Image.new('L', (S, S)); d = ImageDraw.Draw(im)
pv = np.array(PART)
# `part` here is per face; the hands carry 0 or 4, the shoes 6
for t, m, p in zip(UV, MAT, PART):
    if m == 0 and p == 5: d.polygon([(x * S, (1 - y) * S) for x, y in t], fill=255)
w = np.asarray(im, np.float32) / 255
cov = Image.new('L', (S, S)); d = ImageDraw.Draw(cov)
for t, m in zip(UV, MAT):
    if m == 0: d.polygon([(x * S, (1 - y) * S) for x, y in t], fill=255)
cov = np.asarray(cov) > 0
idx = ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True)
wp = w[idx[0], idx[1]]
base = np.asarray(Image.open(T / 'nb_limbs_a_raw_graded.png').convert('RGB').resize((S, S), Image.LANCZOS), np.float32) / 255
tier = {'nb_a': base}
for t in 'bc':
    tier['nb_' + t] = np.asarray(Image.open(T / f'nb_limbs_{t}_raw_graded.png').convert('RGB').resize((S, S), Image.LANCZOS), np.float32) / 255
core = ndimage.binary_erosion(w > 0.5, iterations=3).astype(np.float32)
ramps, rep = RV.fit_ramps(base, tier, core)
print('RAMPS', rep)
RV.write_mask([wp], T / 'nb_limbs_mask.png', 1024)
json.dump({'variants': ['nb_a', 'nb_b', 'nb_c'], 'materials': [{'base': 'Nobleman', 'prefix': 'Nobleman', 'mask': 'nb_limbs_mask.png', 'ramps': {v: [ramps[v]] for v in ramps}}]}, open(T / 'nb_ramps.json', 'w'), indent=0)
