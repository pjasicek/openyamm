#!/usr/bin/env python3
"""Colour tiers on the shared sets: region masks + ramps. All three MM9 rows use the one skin DWARF.dtx, so MM9 tells them apart only by name: tier A is the paint; B and C are a restrained darker and a darkest leather, a blued steel, the beard darker and grey, so that the rows can be told apart in play (deviation, README). Regions: torso and limbs R leather, G steel, B gold; head R beard, G steel.
Writes textures/dwarf_{torso,limbs,head}_region_mask.png, textures/dwarf_ramps.json. Project folder."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, '../claude_shared'); sys.path.insert(0, 'scripts')
import region_variants as RV
import project_lib as PL
TX = Path('textures')
F = np.load('work/faces.npz')
S = 1024
names_ = ('dwarf_a', 'dwarf_b', 'dwarf_c')
def hsv(rgb):
    mx, mn = rgb.max(2), rgb.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360, sat, mx
def soft(m, s=1.0): return np.clip(ndimage.gaussian_filter(m.astype(np.float32), s) * 1.2, 0, 1)
def clean(m): return ndimage.binary_opening(ndimage.binary_closing(m, iterations=1), iterations=1)
LEATHER = {'dwarf_a': (0.84, 0.74, 0.72), 'dwarf_b': (0.62, 0.55, 0.56), 'dwarf_c': (0.44, 0.36, 0.38)}
STEEL = {'dwarf_a': (0.80, 0.80, 0.82), 'dwarf_b': (0.68, 0.72, 0.80), 'dwarf_c': (0.88, 0.89, 0.93)}
GOLD = {'dwarf_a': (0.92, 0.86, 0.72), 'dwarf_b': (0.76, 0.72, 0.62), 'dwarf_c': (1.02, 0.96, 0.78)}
YOKE = {'dwarf_a': (0.74, 0.64, 0.50), 'dwarf_b': (0.60, 0.54, 0.46), 'dwarf_c': (0.46, 0.40, 0.36)}
BEARD = {'dwarf_a': (0.92, 0.84, 0.80), 'dwarf_b': (0.56, 0.48, 0.48), 'dwarf_c': None}
entries = []
for mat, setname, basef, maskf in ((1, 'DwarfTorso', 'dwarf_torso_a_final.png', 'dwarf_torso_region_mask.png'), (0, 'DwarfLimbs', 'dwarf_limbs_a_final.png', 'dwarf_limbs_region_mask.png'), (2, 'DwarfHead', 'dwarf_head_a_final.png', 'dwarf_head_region_mask.png')):
    im = Image.open(TX / basef).convert('RGB')
    base = np.asarray(im.resize((S, S), Image.LANCZOS), np.float32) / 255
    sel = F['mat'] == mat
    pos, nor, cov, bar, fid = PL.raster(F['uv'][sel], F['co'][sel], S)
    parts = F['part'][sel][fid]
    h, s, v = hsv(base)
    if mat == 2:
        ax = np.abs(pos[..., 0])                      # the beard by place, not colour: below the nose, rising to the sideburns, a soft 3D edge that charts cannot break
        wb = np.clip((0.437 + 0.75 * np.maximum(ax - 0.035, 0) + 0.006 - pos[..., 2]) / 0.012, 0, 1) * ((parts == 20) & cov)
        wb = wb * wb * (3 - 2 * wb)
        steel = (parts == 21) & (s < 0.28) & cov
        masks = [np.asarray(wb, np.float32), soft(clean(steel))]
        kinds = [BEARD, STEEL]
    else:
        gold = (h > 34) & (h < 62) & (s > 0.42) & (v > 0.38) & cov
        steel = (s < 0.22) & cov
        skin = (h < 32) & (s > 0.25) & (s < 0.62) & (v > 0.58) & cov & (parts == 1) & (np.abs(pos[..., 0]) > 0.23) & (pos[..., 2] < 0.1)
        leather = (h < 36) & (v < 0.72) & (s > 0.3) & cov & ~skin & ~gold
        masks = [soft(clean(leather)), soft(clean(steel)), soft(clean(gold))]
        kinds = [LEATHER, STEEL, GOLD]
        if mat == 1:                                  # the tan yoke of cloth, not gold: a broad calm area round the neck
            lum = RV.luminance(base); mu = ndimage.uniform_filter(lum, 9); sd = np.sqrt(np.maximum(ndimage.uniform_filter(lum * lum, 9) - mu * mu, 0))
            yoke = (h > 28) & (h < 62) & (s > 0.3) & cov & (pos[..., 2] > 0.2) & (np.abs(pos[..., 0]) < 0.17) & (sd < 0.11) & (v < 0.84)
            yoke = ndimage.binary_opening(yoke, iterations=1)
            masks.append(soft(yoke, 1.5)); kinds.append(YOKE)
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    masks = [m[iy, ix] for m in masks]
    print(setname, 'share', [round(float((m > 0.5).sum() / cov.sum()), 3) for m in masks])
    RV.write_mask(masks, TX / maskf, 1024)
    ramps = {k: [] for k in names_}
    for m, kind in zip(masks, kinds):
        tt = {}
        for k in names_:
            if kind[k] is None:                       # grey beard: the beard's luminance, cool
                l = RV.luminance(base)[..., None]
                tt[k] = np.clip(np.power(l, 0.62) * np.array([0.94, 0.94, 0.98]), 0, 1)
            else: tt[k] = np.clip(base * np.array(kind[k], np.float32), 0, 1)
        r, rep = RV.fit_ramps(base, tt, m)
        print(setname, rep)
        for k in names_: ramps[k].append(r[k])
    entries.append({'base': setname, 'prefix': setname, 'mask': maskf, 'ramps': ramps})
json.dump({'variants': list(names_), 'materials': entries}, open(TX / 'dwarf_ramps.json', 'w'))
print('RAMPS')
