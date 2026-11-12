#!/usr/bin/env python3
"""Footfall phases of locomotion clips: where each foot is forward-most (ankle relative to the pelvis) and where its
sole lands and lifts (LOD0 sole vertices below 6 cm in Standing within 1.5 cm of the floor), as a share of the loop.
The engine shares one gait phase across walk, run and sprint and switches clips at the same phase, so new clips must
put the same foot forward at the same phase as the accepted Walking and Running.

    phase_probe.py <glb> <clip>[,<clip>...]
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose, open_glb  # noqa: E402


def main():
    glb = open_glb(sys.argv[1])
    model = glb_pose.Model(glb)
    names = [n['name'] for n in glb.json['nodes']]
    I = {n: i for i, n in enumerate(names)}
    W0 = model.world(model.sample('Standing', 0.0))
    p0 = model.skinned_positions(W0)[0][0]
    mid = W0[I['B_Pelvis'], 0, 3]
    sets = {'L': np.where((p0[:, 1] < 0.06) & (p0[:, 0] > mid))[0], 'R': np.where((p0[:, 1] < 0.06) & (p0[:, 0] <= mid))[0]}
    for clip in sys.argv[2].split(','):
        T = model.clip_times(clip)[-1]
        n = 96
        Ws = [model.world(model.sample(clip, k * T / n)) for k in range(n)]
        cells = []
        for s in 'LR':
            rel = np.array([W[I[f'B_{s}_Foot'], 2, 3] - W[I['B_Pelvis'], 2, 3] for W in Ws])
            low = np.array([model.skinned_positions(W)[0][0][sets[s], 1].min() for W in Ws])
            on = low < 0.015
            land = [k / n for k in range(n) if on[k] and not on[k - 1]]
            lift = [k / n for k in range(n) if not on[k] and on[k - 1]]
            cells.append(f'{s} front {np.argmax(rel) / n:.2f} land {",".join(f"{v:.2f}" for v in land)} '
                         f'lift {",".join(f"{v:.2f}" for v in lift)} stance {on.mean():.2f}')
        print(f'{clip:9} T {T:.3f}  ' + '  |  '.join(cells))


if __name__ == '__main__':
    main()
