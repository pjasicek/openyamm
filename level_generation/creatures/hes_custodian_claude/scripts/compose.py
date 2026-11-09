#!/usr/bin/env python3
"""The Custodian's runtime textures from its Meshy retexture (meshy/custodian_retexture_v1/), as
hes_turrets_claude/scripts/compose.py.

- Base colour 2048: Meshy's, islands dilated 8 texels into their gutters. (The added glow geometry of build.py has
  its own untextured materials: the packed atlas has no free square for swatches.)
- Normal 1024: Meshy's, measured with tools/normal_map_convention.measure and flipped to glTF (+y up) when needed.
- ORM 1024 (glTF: R = 1, G roughness, B metallic): metallic binarised (Meshy >= 0.5 -> 0.85, the gold trim and saw
  steel; else 0), roughness Meshy's, at least 0.45 on the ceramic (glazed ceramic read like plastic on the turrets).
Also finds the vents Meshy painted under the sphere (amber texels on downward faces) -> textures/cust_glow.json with
the vent centres and radii (metres, rest pose). Usage: compose.py"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE / 'scripts'))
sys.path.insert(0, str(REPO / 'tools'))
from raster import dilate, rasterise  # noqa: E402
import normal_map_convention  # noqa: E402

RES = 2048
SRC = HERE / 'meshy' / 'custodian_retexture_v1'
OUT = HERE / 'textures'
OUT.mkdir(exist_ok=True)


def load(kind):
    return np.array(Image.open(SRC / f'texture_urls_0_{kind}.png').convert('RGB').resize((RES, RES), Image.LANCZOS)
                    ).astype(np.float32) / 255.0


d = np.load(HERE / 'work' / 'tris.npz')
tri, pos = rasterise(d['uv'], d['co'], d['n'], RES)
covered = tri >= 0
part = np.where(covered, d['part'][np.maximum(tri, 0)], -1)
nz = np.where(covered, d['n'][np.maximum(tri, 0)][..., 2], 0)
base, metal, rough, nrm = load('base_color'), load('metallic'), load('roughness'), load('normal')

# the painted vents: amber texels on downward faces of the body, merged into blobs in 3D
r, g, b = base[..., 0], base[..., 1], base[..., 2]
amber = covered & (part == 1) & (nz < -0.3) & (r > 0.7) & (g > 0.45) & (b < 0.35) & (r - b > 0.4)
amber &= pos[..., 2] < 0.8
lab, n = ndimage.label(amber)
blobs = []
for k in range(1, n + 1):
    m = lab == k
    if m.sum() >= 40:
        blobs.append((pos[m].mean(0), pos[m], int(m.sum())))
vents = []
for c, pts, w in sorted(blobs, key=lambda x: -x[2]):
    for v in vents:
        if np.linalg.norm(v['c'] / v['w'] - c) < 0.12:
            v['c'] += c * w; v['w'] += w; v['pts'].append(pts); break
    else:
        vents.append({'c': c * w, 'w': w, 'pts': [pts]})
VENTS = []
for v in vents:
    c = v['c'] / v['w']
    pts = np.concatenate(v['pts'])
    rad = float(np.percentile(np.hypot(pts[:, 0] - c[0], pts[:, 1] - c[1]), 90))
    VENTS.append({'centre': c.round(4).tolist(), 'radius': round(min(max(rad, 0.05), 0.11), 4)})
print('VENTS', len(VENTS), [v['centre'] for v in VENTS])

base = dilate(base, covered, 8); metal = dilate(metal, covered, 8)
rough = dilate(rough, covered, 8); nrm = dilate(nrm, covered, 8)
# Meshy's metallic map marks almost all the ceramic as metal (96 % of the cream texels); metal is taken from the
# colour instead: gold trim = yellow hues (25-65 deg) saturated over ~0.5 (the cream ceramic peaks at 0.35, the gold
# at 0.5-0.7), and the saw discs' grey steel (low saturation on the disc parts). Everything else is non-metal.
mx, mn = base.max(-1), base.min(-1)
sat = (mx - mn) / np.maximum(mx, 1e-4)
hue = np.zeros_like(mx)
rr_, gg_, bb_ = base[..., 0], base[..., 1], base[..., 2]
cmax = np.argmax(base, -1)
dlt = np.maximum(mx - mn, 1e-4)
hue = np.where(cmax == 0, ((gg_ - bb_) / dlt) % 6, np.where(cmax == 1, (bb_ - rr_) / dlt + 2, (rr_ - gg_) / dlt + 4)) * 60
gold = np.clip((sat - 0.45) / 0.1, 0, 1) * ((hue > 25) & (hue < 65) & (mx > 0.3))
partn = np.where(covered, d['part'][np.maximum(tri, 0)], -1)
part_d = dilate(partn.astype(np.float32), partn >= 0, 8)
steel = np.isin(np.round(part_d), (5, 8)) & (sat < 0.25) & (mx > 0.25)
metallic = 0.85 * np.maximum(gold, steel)
roughness = np.where(metallic > 0.4, rough[..., 0], np.maximum(rough[..., 0], 0.45))
orm = np.stack([np.ones_like(roughness), roughness, metallic], -1)
correlation = normal_map_convention.measure((nrm * 255).astype(np.uint8))
if correlation <= -0.15:
    nrm[..., 1] = 1.0 - nrm[..., 1]
print('normal correlation', round(float(correlation), 3), 'flipped' if correlation <= -0.15 else 'kept',
      'metallic share', round(float((metallic > 0.4)[covered].mean()), 3))


def save(img, size, kind):
    im = Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))
    im.resize(size, Image.LANCZOS).save(OUT / f'cust_{kind}.png')


save(base, (2048, 2048), 'basecolor'); save(nrm, (1024, 1024), 'normal'); save(orm, (1024, 1024), 'orm')
json.dump({'vents': VENTS}, open(OUT / 'cust_glow.json', 'w'), indent=1)
print('COMPOSED')
