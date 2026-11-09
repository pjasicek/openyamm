#!/usr/bin/env python3
"""World position/scale of a node against a reference node over a clip (is a pelvis-child prop held in a hand?).
    node_track.py <glb> <clip> <node> <ref node> [samples]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose  # noqa: E402
import gaitlib  # noqa: E402
g = glb_pose.Glb(sys.argv[1]); gaitlib.alias_nodes(g); m = glb_pose.Model(g)
idx = {n['name']: i for i, n in enumerate(g.json['nodes'])}
a, b = idx[sys.argv[3]], idx[sys.argv[4]]
T = m.clip_times(sys.argv[2])[-1]
n = int(sys.argv[5]) if len(sys.argv) > 5 else 6
for t in np.arange(n) / n * T:
    W = m.world(m.sample(sys.argv[2], float(t)))
    rel = np.linalg.inv(W[b]) @ W[a]
    print(f'{t:.3f} node {np.round(W[a][:3, 3], 3)} scale {np.round(np.linalg.norm(W[a][:3, :3], axis=0), 3)} '
          f'in ref: pos {np.round(rel[:3, 3], 3)} rot row0 {np.round(rel[0, :3], 3)}')
