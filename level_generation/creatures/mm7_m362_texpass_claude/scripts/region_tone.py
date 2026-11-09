"""Doublet and hair colours as the engine shows them (ramps applied) per skin, installed against the pass, at the same
surface points: texels where both the installed mask (carried onto the layout, work/approved_fine_region_mask.png)
and the pass's mask have the region above 0.5. Area-weighted mean sRGB and luminance sd.
Usage: region_tone.py <pass glb> [json out]"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import Glb  # noqa: E402
from viewer_variants import bake  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
S = 2048
LUMA = np.array([0.2126, 0.7152, 0.0722])


def mask(path):
    return np.stack([np.asarray(c.resize((S, S), Image.Resampling.BILINEAR), np.float32) / 255
                     for c in Image.open(path).convert('RGBA').split()], -1)


layout = np.load(HERE / 'work' / 'uv_fine.npz')
r = np.load(HERE / 'work' / f'approved_fine_raster{S}.npz')
tri_id = r['tri_id']
uv, xyz = layout['uv'], layout['xyz']
area3 = np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]), axis=1) / 2
area2 = np.abs((uv[:, 1, 0] - uv[:, 0, 0]) * (uv[:, 2, 1] - uv[:, 0, 1])
               - (uv[:, 2, 0] - uv[:, 0, 0]) * (uv[:, 1, 1] - uv[:, 0, 1])) / 2
weight = np.where(tri_id >= 0, area3[np.maximum(tri_id, 0)] / np.maximum(area2[np.maximum(tri_id, 0)], 1e-12), 0)
states = {'installed': (Glb(HERE / 'work' / 'before_texpass' / 'mm7_m362.glb'), 'work/approved_fine_basecolor.png',
                        'work/approved_fine_region_mask.png'),
          'pass': (Glb(sys.argv[1]), 'textures/m362_tp_basecolor.png', 'textures/m362_tp_region_mask.png')}
masks = {k: mask(HERE / v[2]) for k, v in states.items()}
out = {}
for mi in range(9):
    name = states['pass'][0].doc['materials'][mi]['name']
    row = {}
    for k, (g, base, m) in states.items():
        eng = bake(Image.open(HERE / base).convert('RGB'), Image.open(HERE / m),
                   g.doc['materials'][mi]['extras']['openyamm_region_ramps']).astype(np.float64)
        for c, region in ((0, 'doublet'), (1, 'hair')):
            sel = (masks['installed'][..., c] > 0.5) & (masks['pass'][..., c] > 0.5) & (tri_id >= 0)
            w = weight[sel]
            mean = np.average(eng[sel], 0, w)
            lum = eng[sel] @ LUMA
            sd = np.sqrt(np.average((lum - np.average(lum, weights=w)) ** 2, weights=w))
            row[f'{region} {k}'] = [round(float(x), 1) for x in mean] + [round(float(sd), 1)]
    out[name] = row
    print(name, ' | '.join(f'{k} {v[:3]} sd {v[3]}' for k, v in row.items()))
if len(sys.argv) > 2:
    json.dump(out, open(sys.argv[2], 'w'), indent=1)
