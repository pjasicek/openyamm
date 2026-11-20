#!/usr/bin/env python3
"""Jerk, bob and wrist checks of locomotion clips (sole_probe/jerk_probe/wrist rules of the humanoid playbook).

    motion_probe.py <glb> <clip>[,<clip>...]

Per clip at 48 Hz over one loop, including the seam (last sample to first): the largest world-rotation step and its
largest change (second difference) for head, hands and feet (degrees per 1/48 s); pelvis height range and largest
step (cm, the "jump" the m412 walk once had); wrist flexion (hand vs forearm, max) and forearm-twist roll range;
lowest skin point over the loop (cm, below the floor when negative).
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose, open_glb  # noqa: E402

JOINTS = ('B_Head', 'B_L_Hand', 'B_R_Hand', 'B_L_Foot', 'B_R_Foot')


def angle(a, b):
    r = a.T @ b
    return float(np.degrees(np.arccos(np.clip((np.trace(r) - 1) / 2, -1, 1))))


def main():
    glb = open_glb(sys.argv[1])
    model = glb_pose.Model(glb)
    names = [n['name'] for n in glb.json['nodes']]
    I = {n: i for i, n in enumerate(names)}
    for clip in sys.argv[2].split(','):
        T = model.clip_times(clip)[-1]
        n = int(round(T * 48))
        Ws = [model.world(model.sample(clip, k * T / n)) for k in range(n)]
        Ws.append(Ws[0])
        cells = []
        for j in JOINTS:
            steps = np.array([angle(Ws[k][I[j], :3, :3], Ws[k + 1][I[j], :3, :3]) for k in range(n)])
            second = np.abs(np.diff(np.append(steps, steps[0])))
            cells.append(f'{j[2:]} {steps.max():.1f}/{second.max():.1f}')
        pel = np.array([W[I['B_Pelvis'], 1, 3] for W in Ws])
        wrist = max(angle(W[I[f'B_{s}_Forearm'], :3, :3], W[I[f'B_{s}_Hand'], :3, :3]) for W in Ws for s in 'LR')
        low = min(model.lowest(clip, k * T / n) for k in range(0, n, 2))
        print(f'{clip:9} T {T:.3f}  ' + '  '.join(cells)
              + f'  pelvis {100 * np.ptp(pel):.1f} cm step {100 * np.abs(np.diff(pel)).max():.2f}'
              + f'  wrist max {wrist:.0f} deg  lowest {100 * low:.1f} cm')


if __name__ == '__main__':
    main()
