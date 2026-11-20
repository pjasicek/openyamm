#!/usr/bin/env python3
"""Foot heading from the foot mesh (for rigs whose foot->toe joint line is not the foot's long axis, such as the MM6
Lizard Archer): LOD0 vertices dominated by each foot and toe bone, their horizontal principal axis while the foot is
planted (foot joint in its lowest 25 %), as toe-out from +Z in degrees (positive = toe out, either side).

    foot_mesh_heading_probe.py <glb> <clip>[,<clip>...]
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose, open_glb  # noqa: E402


def heading(points, sign):
    xz = points[:, [0, 2]] - points[:, [0, 2]].mean(axis=0)
    w, v = np.linalg.eigh(xz.T @ xz)
    a = v[:, -1]
    if a[1] < 0:
        a = -a                       # toward +Z (forward)
    return sign * np.degrees(np.arctan2(a[0], a[1]))


def main():
    glb = open_glb(sys.argv[1])
    model = glb_pose.Model(glb)
    I = {n['name']: i for i, n in enumerate(glb.json['nodes'])}
    W0 = model.world(model.sample('Standing', 0.0))
    joints = np.array(model.joints)
    pi = next(i for i, p in enumerate(model.primitives) if p['skinned'])
    J, Wt = model.primitives[pi]['joints'], model.primitives[pi]['weights']
    dom = joints[J[np.arange(len(J)), np.argmax(Wt, axis=1)]]
    sets = {}
    for s in 'LR':
        sets[s] = np.where(np.isin(dom, [I[n] for n in (f'B_{s}_Foot', f'B_{s}_Toe0') if n in I]))[0]
    for clip in ['Standing'] + sys.argv[2].split(','):
        T = model.clip_times(clip)[-1]
        times = [k * T / 64 for k in range(64)] if T > 0 else [0.0]
        res = {s: [] for s in 'LR'}
        hs = {s: [] for s in 'LR'}
        for t in times:
            W = model.world(model.sample(clip, t))
            p = model.skinned_positions(W)[pi][0]
            for s, sign in (('L', 1.0), ('R', -1.0)):
                res[s].append(heading(p[sets[s]], sign))
                hs[s].append(W[I[f'B_{s}_Foot'], 1, 3])
        cells = []
        for s in 'LR':
            y, h = np.array(res[s]), np.array(hs[s])
            low = h <= h.min() + 0.25 * max(np.ptp(h), 1e-9)
            cells.append(f'{s} planted {y[low].mean():+.1f} ({y[low].min():+.1f}..{y[low].max():+.1f})')
        print(f'{clip:9} mesh toe-out  ' + '  |  '.join(cells))


if __name__ == '__main__':
    main()
