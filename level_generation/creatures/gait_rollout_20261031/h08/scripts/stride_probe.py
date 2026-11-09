#!/usr/bin/env python3
"""Planted-sole stride per side (left shoe, right shoe or peg) of locomotion clips.

    stride_probe.py <glb> <clip>[,<clip>...]

Sole vertices: below 6 cm in Standing, split at the pelvis. Per pair of consecutive samples (240 Hz), the vertices
under 1 cm in both move back at the ground speed when planted; median backward speed x clip length = stride. Unlike
stride_audit.py (foot-joint vertices only) this also reads the Pirate Mage's peg (calf-skinned), so the binding stride
can be chosen to keep both supports still.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose  # noqa: E402


def main():
    glb = glb_pose.Glb(sys.argv[1])
    model = glb_pose.Model(glb)
    names = [n['name'] for n in glb.json['nodes']]
    W0 = model.world(model.sample('Standing', 0.0))
    p0 = model.skinned_positions(W0)[0][0]
    mid = W0[names.index('B_Pelvis'), 0, 3]
    sets = {'L': np.where((p0[:, 1] < 0.06) & (p0[:, 0] > mid))[0], 'R': np.where((p0[:, 1] < 0.06) & (p0[:, 0] <= mid))[0]}
    for clip in sys.argv[2].split(','):
        T = model.clip_times(clip)[-1]
        n = int(round(T * 240))
        pts = [model.skinned_positions(model.world(model.sample(clip, k * T / n)))[0][0] for k in range(n)]
        pts.append(pts[0])
        cells = []
        for s, ids in sets.items():
            v = []
            for k in range(n):
                a, b = pts[k][ids], pts[k + 1][ids]
                on = (a[:, 1] < 0.01) & (b[:, 1] < 0.01)
                v.extend(-(b[on, 2] - a[on, 2]) / (T / n))
            cells.append(f'{s} {np.median(v) * T:.3f} ({len(v)})' if v else f'{s} -')
        print(f'{clip:9} T {T:.3f}  ' + '  '.join(cells))


if __name__ == '__main__':
    main()
