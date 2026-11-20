#!/usr/bin/env python3
"""Foot heading per clip, planted and swinging: each foot's lateral axis (Standing's horizontal axis across the foot,
up x (foot->toe), carried in the foot bone's frame; the axis a foot pitches about), projected on the ground and turned
into a heading, in degrees of toe-out from +Z (positive = toe out, either side; Standing's own feet read about 27). Unlike foot->toe yaw it stays defined while the foot points steeply down in the
swing. Planted = foot joint in its lowest 25 %. Reports mean and range planted, and the range while swinging.

    foot_heading_probe.py <glb> <clip>[,<clip>...]
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose  # noqa: E402


def main():
    glb = glb_pose.Glb(sys.argv[1])
    model = glb_pose.Model(glb)
    I = {n['name']: i for i, n in enumerate(glb.json['nodes'])}
    W0 = model.world(model.sample('Standing', 0.0))
    local = {}
    for s in 'LR':
        d = W0[I[f'B_{s}_Toe0'], :3, 3] - W0[I[f'B_{s}_Foot'], :3, 3]
        lat = np.cross([0, 1.0, 0], [d[0], 0, d[2]])
        local[s] = W0[I[f'B_{s}_Foot'], :3, :3].T @ (lat / np.linalg.norm(lat))
    for clip in ['Standing'] + sys.argv[2].split(','):
        T = model.clip_times(clip)[-1]
        Ws = [model.world(model.sample(clip, k * T / 96)) for k in range(96)] if T > 0 else [W0]
        cells = []
        for s, sign in (('L', 1.0), ('R', -1.0)):
            yaw, h = [], []
            for W in Ws:
                x = W[I[f'B_{s}_Foot'], :3, :3] @ local[s]
                # heading = lateral x up on the ground; toe-out turns the left toe to +X (left is +X)
                yaw.append(sign * np.degrees(np.arctan2(-x[2], x[0])))
                h.append(W[I[f'B_{s}_Foot'], 1, 3])
            yaw, h = np.array(yaw), np.array(h)
            low = h <= h.min() + 0.25 * max(np.ptp(h), 1e-9)
            swing = f'swing {yaw[~low].min():+.1f}..{yaw[~low].max():+.1f}' if (~low).any() else ''
            cells.append(f'{s} planted {yaw[low].mean():+.1f} ({yaw[low].min():+.1f}..{yaw[low].max():+.1f}) {swing}')
        print(f'{clip:9} toe-out  ' + '  |  '.join(cells))


if __name__ == '__main__':
    main()
