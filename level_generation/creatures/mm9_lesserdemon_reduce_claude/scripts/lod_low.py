#!/usr/bin/env python3
"""Lowest posed vertex of every colour LOD at one clip time, with its rest position and dominant joint (what sets an LOD's
floor contact). Usage: lod_low.py <glb> <clip> <seconds>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model
import bglbio
f, clip, t = sys.argv[1], sys.argv[2], float(sys.argv[3])
m = Model(Glb(f)); doc, b = bglbio.read(f); w = m.world(m.sample(clip, t)); pal = w[m.joints] @ m.inverse_binds
jn = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
node = next(n for n in doc['nodes'] if n.get('name') == 'LesserDemon' and 'mesh' in n)
for lv, mi in enumerate([node['mesh']] + doc['meshes'][node['mesh']]['extras']['openyamm_lods']):
    best = None
    for p in bglbio.prims(doc, b, mi):
        P = np.c_[p['POSITION'], np.ones(len(p['POSITION']))]; W = p['WEIGHTS_0'].astype(float); J = p['JOINTS_0'].astype(int)
        X = np.einsum('vij,vj->vi', np.einsum('vk,vkij->vij', W, pal[J]), P)[:, :3]
        i = np.argmin(X[:, 1])
        if best is None or X[i, 1] < best[0]: best = (X[i, 1], X[i].round(3), p['POSITION'][i].round(3), jn[J[i, W[i].argmax()]], p['material'])
    print('LOD', lv, 'lowest', round(float(best[0]) * 100, 1), 'cm at', best[1], 'rest', best[2], best[3], best[4])
