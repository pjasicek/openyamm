#!/usr/bin/env python3
"""Ivory regions on the main surface (horns, frill spikes, claws, spurs): faces whose UV centroid samples ivory
(both ramp masks low, bright, low saturation) in the unified GLB's textures, grouped by shared vertices.
Prints each region; writes work/ivory_faces.npz (face -> region id, -1 for skin). Usage: ivory_regions.py"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent)); import glb_raster as G  # noqa: E402
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
d = np.load(HERE / 'work/pieces.npz'); doc, b = G.read_glb(HERE / 'export/mm6_cdr1_unified.glb')
mats = {m['name']: m for m in doc['materials']}
fp, fm, fuv, fc = d['fpiece'], d['fmat'], d['fuv'], d['fc']
ivory = np.zeros(len(fp), bool)
for i, name in enumerate(d['mats']):
    m = mats[name]
    base = np.asarray(G.image(doc, b, m['pbrMetallicRoughness']['baseColorTexture']['index']).convert('RGB'), np.float32) / 255
    mask = np.asarray(G.image(doc, b, m['extras']['openyamm_region_mask']['index']).convert('RGBA').resize(base.shape[1::-1]), np.float32) / 255
    N = base.shape[0]; sel = fm == i
    u = np.clip((fuv[sel, 0] % 1) * N, 0, N - 1).astype(int); v = np.clip((1 - fuv[sel, 1] % 1) * N, 0, N - 1).astype(int)
    c = base[v, u]; mk = mask[v, u]; sat = (c.max(1) - c.min(1)) / np.maximum(c.max(1), 1e-3)
    ivory[sel] = (mk[:, 0] < .35) & (mk[:, 1] < .35) & (c.max(1) > .5) & (sat < .35)
ivory &= fp == np.bincount(fp).argmax()            # main surface only (teeth are separate pieces)
# faces -> regions via the faces.npz connectivity (vertices shared): rebuild from the dump's face vertex lists
fv = np.load(HERE / 'work/face_verts.npy', allow_pickle=True)
idx = np.flatnonzero(ivory); rows, cols = [], []
owner = {}
for k, f in enumerate(idx):
    for v in fv[f]:
        owner.setdefault(v, []).append(k)
for lst in owner.values():
    for a in lst[1:]:
        rows.append(lst[0]); cols.append(a)
n, lab = connected_components(coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(idx), len(idx))), directed=False)
region = np.full(len(fp), -1); region[idx] = lab
for r in range(n):
    s = region == r; c = fc[s]; lo, hi = c.min(0), c.max(0)
    print(f'{r:3d} faces {s.sum():4d} mat {d["mats"][np.bincount(fm[s]).argmax()]:14s} ctr {np.round((lo + hi) / 2, 3)} size {np.round(hi - lo, 3)}')
np.savez(HERE / 'work/ivory_faces.npz', region=region)
