#!/usr/bin/env python3
"""Axe attachment against the posed body per frame (30 fps): axe vertices behind the nearest body surface.
    axe_clear.py <body glb> <axe glb> <clip> [<clip> ...]
Prints per clip: frames with any axe vertex over 1 cm inside, deepest (cm) and its time."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
import motion_audit  # noqa
import glb_pose  # noqa
a = motion_audit.Audit(sys.argv[1])
ax = glb_pose.Glb(sys.argv[2])
am = glb_pose.Model(ax)
axv = np.concatenate([p['positions'] for p in am.primitives])
names = [n.get('name') for n in a.glb.json['nodes']]
sword = names.index('Sword')
for clip in sys.argv[3:]:
    ts = a.model.clip_times(clip)
    deep, when, frames = 0.0, 0.0, 0
    for t in np.linspace(ts[0], ts[-1], max(2, int((ts[-1] - ts[0]) * 30) + 1)):
        posed, scale, pal, world = a.pose(clip, t)
        tri = posed[a.tris]
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        vn = np.zeros_like(posed)
        for k in range(3):
            np.add.at(vn, a.tris[:, k], n)
        vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
        core = np.isin(a.vertex_region, [motion_audit.REGIONS.index(r) for r in ('spine', 'head', 'leg')])
        idx = np.nonzero(core)[0]
        tree = cKDTree(posed[idx])
        pts = (np.c_[axv, np.ones(len(axv))] @ world[sword].T)[:, :3]
        d, j = tree.query(pts)
        v = idx[j]
        depth = -np.einsum('ij,ij->i', pts - posed[v], vn[v])
        inside = (depth > 0.01) & (d < 0.06)
        if inside.any():
            frames += 1
            if depth[inside].max() > deep:
                deep, when = depth[inside].max(), t
    print(f'{clip:9s} frames with axe >1 cm inside: {frames}, deepest {deep * 100:.1f} cm at {when:.2f}s')
