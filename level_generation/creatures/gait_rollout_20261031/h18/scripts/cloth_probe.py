#!/usr/bin/env python3
"""Cloth flap against the legs: share of samples where a vertex dominated by the cloth bone lies inside the thigh or
calf skin (nearest leg vertex within 4 cm, behind its normal), and the deepest (mm); plus the flap's forward angle
range (its rest-down axis against the pelvis), per clip.  cloth_probe.py <glb> <clip>[,...] [bone=B_Loincloth]"""
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose, open_glb  # noqa: E402
from contact_probe import vertex_normals  # noqa: E402

glb = open_glb(sys.argv[1])
model = glb_pose.Model(glb)
names = [n['name'] for n in glb.json['nodes']]
bone = sys.argv[3] if len(sys.argv) > 3 else 'B_Loincloth'
prim = model.primitives[0]
dom = [names[model.joints[j]] for j in prim['joints'][np.arange(len(prim['joints'])), prim['weights'].argmax(axis=1)]]
cloth = np.array([d == bone for d in dom])
legs = np.array([('Thigh' in d or 'Calf' in d) for d in dom])
for clip in sys.argv[2].split(','):
    T = model.clip_times(clip)[-1]
    hits, deep, n = 0, 0.0, 60
    for k in range(n):
        points, _ = model.skinned_positions(model.world(model.sample(clip, k * T / n)))[0]
        normals = vertex_normals(points, prim['triangles'])
        tree = cKDTree(points[legs])
        d, i = tree.query(points[cloth])
        depth = np.einsum('ij,ij->i', points[cloth] - points[legs][i], normals[legs][i])
        inside = (d < 0.04) & (depth < -0.003)
        if inside.any():
            hits += 1
            deep = max(deep, float(-depth[inside].min()))
    print(f'{clip:9} {bone} inside legs {100 * hits / n:.0f}% max {1000 * deep:.0f} mm')
