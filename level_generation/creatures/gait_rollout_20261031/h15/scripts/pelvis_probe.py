#!/usr/bin/env python3
"""Mean and range of the pelvis joint height per clip, and the mean knee bend (thigh-calf angle) in stance.

    pelvis_probe.py <glb> <clip>[,<clip>...]
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose, open_glb  # noqa: E402


def main():
    glb = open_glb(sys.argv[1])
    model = glb_pose.Model(glb)
    I = {n['name']: i for i, n in enumerate(glb.json['nodes'])}
    for clip in sys.argv[2].split(','):
        T = model.clip_times(clip)[-1]
        W = np.array([model.world(model.sample(clip, t)) for t in np.arange(120) / 120 * T])
        y = W[:, I['B_Pelvis'], 1, 3]
        bends = []
        for s in 'LR':
            h, k, a = (W[:, I[f'B_{s}_{b}'], :3, 3] for b in ('Thigh', 'Calf', 'Foot'))
            u, v = k - h, a - k
            ang = np.degrees(np.arccos(np.sum(u * v, 1) / np.linalg.norm(u, axis=1) / np.linalg.norm(v, axis=1)))
            low = a[:, 1] <= a[:, 1].min() + 0.25 * np.ptp(a[:, 1])
            bends.append(ang[low].mean())
        print(f'{clip:9} pelvis mean {y.mean():.3f} range {y.min():.3f}..{y.max():.3f}  stance knee bend '
              f'L {bends[0]:.0f} R {bends[1]:.0f} deg')


if __name__ == '__main__':
    main()
