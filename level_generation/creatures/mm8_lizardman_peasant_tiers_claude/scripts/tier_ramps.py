#!/usr/bin/env python3
"""Lizardman Peasant B (Farmer) and C (Villager) colour tiers for the installed `mm8_lizardman_peasant.glb`, which
shipped with only `m400_a` (user: "add the 2 missing color variants for lizardman villager").

The native tiers use palettes 401 / 402 / 403 on the same sprites. Two regions change: the garment (green -> tan ->
red) and the warm trim, belt and apron bands (orange -> purple -> pale grey); skin, teeth, fringe and the gold shoulder
pieces stay. The model's mask had only the garment (channel R, `m400_a` ramp fitted to reproduce the base). This adds:

- mask channel G: the warm trim (the production `compose.py` classes: warm = r > 1.15 g, g > 1.15 b, without the gold
  shoulder pieces at rest height > 1.05 m and |x| > 0.17 m and without the ivory toe and finger claws, below 0.2 m or
  beyond |x| 0.3 m under 1.0 m), padded into the gutters and blurred like channel R;
- ramps per tier and region from the tier's own palette: native pixels that change between the palettes (all 170
  stored frames, pixel for pixel the same index image) are split into garment and trim by their 401 colour and sorted
  by 401 luminance. Stop k of the tier ramp is the mean tier colour of the native pixels at the luminance quantile of
  the region's texels at stop k, scaled to the luminance of the accepted A stop (the albedo / sprite ratio), so B and C
  keep A's brightness and take their hue and value pattern from their own palette. A's garment ramp stays exactly as
  installed; A's trim ramp is a least-squares fit to the base (region_variants.fit_ramps), so A looks as before.

Materials Lizardman_B / Lizardman_C copy Lizardman_A with their own ramps, and every primitive (colour and shadow
LODs) maps the three variants. Usage: tier_ramps.py <installed.glb> <out.glb>"""
import copy
import glob
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

P = Path(__file__).resolve().parents[1]; REPO = P.parents[2]
sys.path.insert(0, str(REPO / 'tools')); sys.path.insert(0, str(REPO / 'level_generation/creatures/claude_shared'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
import region_variants as R  # noqa: E402

PROD = REPO / 'level_generation/creatures/mm8_m400'
RASTER = PROD / '3d_20261006/claude_20261015/work/uvraster_UVMap.npz'
W = np.array([0.2126, 0.7152, 0.0722])
TIERS = {'m400_b': '402', 'm400_c': '403'}
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = read_glb(src); binary = bytearray(binary)


def image(name):
    i = next(k for k, im in enumerate(doc['images']) if im['name'] == name); v = doc['bufferViews'][doc['images'][i]['bufferView']]
    o = v.get('byteOffset', 0)
    return i, Image.open(io.BytesIO(bytes(binary[o:o + v['byteLength']])))


def put_image(i, im):
    buf = io.BytesIO(); im.save(buf, 'PNG', optimize=True)
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())})
    binary.extend(buf.getvalue()); doc['images'][i]['bufferView'] = len(doc['bufferViews']) - 1


# --- trim mask on the body part of the atlas (the body set is the left 1024 x 1024; head set to the right)
_, baseim = image('Body_basecolor_head_atlas'); mi, maskim = image('body_region_mask_head_atlas')
atlas = np.asarray(baseim.convert('RGB'), np.float64) / 255; mask = np.asarray(maskim).copy()
body = atlas[:, :1024]
raster = np.load(RASTER); cov = raster['piece'] >= 0; pos = raster['pos']
r, g, b = body.transpose(2, 0, 1)
warm = (r > g * 1.15) & (g > b * 1.15)
gold = warm & (pos[..., 2] > 1.05) & (np.abs(pos[..., 0]) > 0.17)
claws = (pos[..., 2] < 0.2) | ((np.abs(pos[..., 0]) > 0.3) & (pos[..., 2] < 1.0))   # toe and finger claws stay ivory
trim = warm & ~gold & ~claws & cov & (mask[:, :1024, 0] < 128)
idx = ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True)
trim_w = ndimage.gaussian_filter(trim.astype(float)[idx[0], idx[1]], 0.7)
mask[:, :1024, 1] = np.uint8(np.clip(trim_w * 255 + 0.5, 0, 255))
put_image(mi, Image.fromarray(mask, maskim.mode))

# --- native pixel pairs per region
A, T = [], {t: [] for t in TIERS}
for f in sorted(glob.glob(str(PROD / 'native_variants/*_401.png'))):
    a = np.asarray(Image.open(f).convert('RGBA')).reshape(-1, 4).astype(int)
    tiers = {t: np.asarray(Image.open(f.replace('_401', f'_{p}')).convert('RGBA')).reshape(-1, 4).astype(int) for t, p in TIERS.items()}
    changed = (a[:, 3] > 0) & np.any([np.abs(a[:, :3] - x[:, :3]).max(1) > 6 for x in tiers.values()], 0)
    A.append(a[changed, :3])
    for t in TIERS:
        T[t].append(tiers[t][changed, :3])
A = R.srgb_to_linear(np.concatenate(A) / 255); T = {t: R.srgb_to_linear(np.concatenate(v) / 255) for t, v in T.items()}
nat_warm = (A[:, 0] > A[:, 1] * 1.12) & (A[:, 1] >= A[:, 2])

material = next(m for m in doc['materials'] if m['name'] == 'Lizardman_A')
garment_a = material['extras']['openyamm_region_ramps'][0]
trim_ramps, trim_fit = R.fit_ramps(body, {'m400_a': body}, trim_w)
ramps = {'m400_a': [garment_a, trim_ramps['m400_a']]}
lum = R.luminance(body); report = {'trim_texels': int((trim_w > 0.9).sum()), 'trim_fit_a': trim_fit}
for t in TIERS:
    ramps[t] = []
for region, (ramp_a, weight, sel) in enumerate([(garment_a, mask[:, :1024, 0] / 255, ~nat_warm), (ramps['m400_a'][1], trim_w, nat_warm)]):
    lo, hi = ramp_a['range']; stops_a = np.array(ramp_a['colors'])
    tex = np.sort(lum[weight > 0.9])
    nat_l = A[sel] @ W; order = np.argsort(nat_l); n = len(order); half = max(50, n // 60)
    for t in TIERS:
        cols = []
        for k in range(16):
            q = np.searchsorted(tex, lo + (hi - lo) * k / 15) / len(tex)
            i = int(np.clip(q, 0.005, 0.995) * n); w = order[max(0, i - half):i + half]
            nat_a, nat_t = A[sel][w].mean(0), T[t][sel][w].mean(0)
            cols.append(np.clip(nat_t * (stops_a[k] @ W) / max(nat_a @ W, 1e-4), 0, 1))
        ramps[t].append({'range': [lo, hi], 'colors': np.round(cols, 6).tolist()})
    report[f'region{region}_native_pixels'] = int(sel.sum())

# --- materials and variant mappings
base = doc['materials'].index(material)
material['extras']['openyamm_region_ramps'] = ramps['m400_a']
index = {'m400_a': base}
for t in TIERS:
    m = copy.deepcopy(material); m['name'] = f"Lizardman_{t[-1].upper()}"; m['extras']['openyamm_region_ramps'] = ramps[t]
    doc['materials'].append(m); index[t] = len(doc['materials']) - 1
names = ['m400_a', *TIERS]
doc['extensions']['KHR_materials_variants'] = {'variants': [{'name': v} for v in names]}
mapped = 0
for mesh in doc['meshes']:
    for p in mesh['primitives']:
        if p.get('material') == base:
            p.setdefault('extensions', {})['KHR_materials_variants'] = {
                'mappings': [{'material': index[v], 'variants': [k]} for k, v in enumerate(names)]}
            mapped += 1
write_glb(dst, doc, bytes(binary))
(P / 'textures').mkdir(exist_ok=True)
(P / 'textures/ramps.json').write_text(json.dumps({'variants': names, 'palettes': {'m400_a': 401, 'm400_b': 402, 'm400_c': 403},
                                                   'regions': ['garment', 'trim'], 'ramps': ramps, 'report': report}, indent=1) + '\n')
print('TIERS', mapped, 'primitives;', json.dumps(report))
