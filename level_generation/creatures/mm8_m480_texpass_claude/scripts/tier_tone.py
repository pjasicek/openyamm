"""Tier colours as the engine shows them (region ramps applied to the base colour), approved against the texture pass,
per region at the same surface points: area-weighted mean sRGB and luminance sd. Usage: tier_tone.py <before glb>
<after glb> <approved prefix on the layout> <layout npz>"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import Glb  # noqa: E402
from viewer_variants import bake  # noqa: E402

before, after, approved, layout_path = sys.argv[1:5]
S = 2048
r = np.load(f'{approved}_raster{S}.npz')
cov = r['tri_id'] >= 0
lay = np.load(layout_path)
uv, xyz = lay['uv'], lay['xyz']
a3 = np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]), axis=1) / 2
a2 = np.abs((uv[:, 1, 0] - uv[:, 0, 0]) * (uv[:, 2, 1] - uv[:, 0, 1]) - (uv[:, 2, 0] - uv[:, 0, 0]) * (uv[:, 1, 1] - uv[:, 0, 1])) / 2
w = np.zeros((S, S))
w[cov] = (a3 / np.maximum(a2, 1e-12))[r['tri_id'][cov]]
mask = np.stack([np.asarray(ch.resize((S, S), Image.BILINEAR), np.float32)
                 for ch in Image.open(f'{approved}_region_mask.png').convert('RGBA').split()], -1) / 255
appr_base = Image.open(f'{approved}_basecolor.png').convert('RGB')
g = Glb(after)
new_base = g.image(g.doc['textures'][g.doc['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index']]['source']).convert('RGB')
new_mask = g.image(g.doc['textures'][g.doc['materials'][0]['extras']['openyamm_region_mask']['index']]['source'])
gb = Glb(before)
out = {}
for mi in range(3):
    ramps_new = g.doc['materials'][mi]['extras']['openyamm_region_ramps']
    ramps_old = gb.doc['materials'][mi]['extras']['openyamm_region_ramps']
    A = bake(appr_base, Image.open(f'{approved}_region_mask.png'), ramps_old).astype(np.float32)
    B = bake(new_base, new_mask, ramps_new).astype(np.float32)
    name = g.doc['materials'][mi]['name']
    out[name] = {}
    for k, region in enumerate(('skin', 'wrap', 'crest', 'back')):
        sel = cov & (mask[..., k] > 0.5)
        ww = w[sel]
        L = np.array([0.2126, 0.7152, 0.0722])
        out[name][region] = {
            'approved': [round(float(np.average(A[sel, c], weights=ww)), 1) for c in range(3)],
            'pass': [round(float(np.average(B[sel, c], weights=ww)), 1) for c in range(3)],
            'sd': [round(float(np.sqrt(np.cov(A[sel] @ L, aweights=ww))), 1),
                   round(float(np.sqrt(np.cov(B[sel] @ L, aweights=ww))), 1)]}
print(json.dumps(out, indent=None))
