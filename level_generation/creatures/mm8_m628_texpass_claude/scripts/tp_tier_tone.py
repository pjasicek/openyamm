"""Tier colours as the engine shows them (region ramps applied to the base colour), approved against the pass, at the
same surface points: per tier material of the main primitive and per class (region channel > 0.5, rest, other atlas
primitives), area-weighted mean sRGB and luminance sd. Usage: tp_tier_tone.py <after glb> <approved prefix> <layout npz>"""
import json
import sys

import numpy as np
from PIL import Image

import tp_common as C
from tp_viewer_variants import bake

cfg = C.config()
after, approved, layout_path = sys.argv[1:4]
S = cfg.get('size', 2048)
r = np.load(f'{approved}_raster{S}.npz')
cov = r['tri_id'] >= 0
lay = np.load(layout_path)
before = np.load(C.lod0_path())
w = np.zeros((S, S))
w[cov] = (C.tri_area3(lay['xyz']) / np.maximum(C.tri_area2(lay['uv']), 1e-12))[r['tri_id'][cov]]
prim = np.full((S, S), -1)
prim[cov] = before['prim'][r['tri_id'][cov]]
main = cfg['atlas_prims'][0]
try:
    amask_img = Image.open(f'{approved}_region_mask.png')
    mask = np.stack([np.asarray(ch.resize((S, S), Image.BILINEAR), np.float32)
                     for ch in amask_img.convert('RGBA').split()], -1) / 255
except FileNotFoundError:
    amask_img, mask = None, np.zeros((S, S, 4), np.float32)
appr_base = Image.open(f'{approved}_basecolor.png').convert('RGB')
g = C.Glb(after)
doc = g.doc
mesh = doc['meshes'][C.lod0_mesh_index(doc, cfg['node'])]
L = np.array([0.2126, 0.7152, 0.0722])
n_ramps = len(doc['materials'][mesh['primitives'][main]['material']].get('extras', {}).get('openyamm_region_ramps', []))
mask[..., n_ramps:] = 0
classes = {f'region{k}': cov & (prim == main) & (mask[..., k] > 0.5) for k in range(n_ramps)}
classes['rest'] = cov & (prim == main) & (mask.sum(-1) < 0.5)
for pi in cfg['atlas_prims'][1:]:
    classes[f'prim{pi}'] = cov & (prim == pi)
out = {}
for m in C.primitive_materials(mesh['primitives'][main]):
    mat = doc['materials'][m]
    maps = C.material_maps(mat)
    ramps = mat.get('extras', {}).get('openyamm_region_ramps', [])
    new_base = g.image(doc['textures'][maps['basecolor']]['source']).convert('RGB')
    if ramps:
        A = bake(appr_base, amask_img, ramps).astype(np.float32)
        B = bake(new_base, g.image(doc['textures'][maps['region_mask']]['source']), ramps).astype(np.float32)
    else:
        A, B = np.asarray(appr_base, np.float32), np.asarray(new_base, np.float32)
    out[mat['name']] = {}
    for name, sel in classes.items():
        if w[sel].sum() <= 0:
            continue
        ww = w[sel]
        out[mat['name']][name] = {
            'share': round(float(ww.sum() / w[cov].sum()), 3),
            'approved': [round(float(np.average(A[sel, c], weights=ww)), 1) for c in range(3)],
            'pass': [round(float(np.average(B[sel, c], weights=ww)), 1) for c in range(3)],
            'sd': [round(float(np.sqrt(np.cov(A[sel] @ L, aweights=ww))), 1),
                   round(float(np.sqrt(np.cov(B[sel] @ L, aweights=ww))), 1)]}
print(json.dumps(out, indent=1))
