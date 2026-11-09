#!/usr/bin/env python3
"""Mean trunk lean (pelvis joint to neck joint, degrees forward of vertical), mean head pitch (the head bone's forward
axis below the horizontal, relative to Standing) and mean pelvis height per clip.

    posture_probe.py <glb> <clip>[,<clip>...]
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
    for clip in ['Standing'] + sys.argv[2].split(','):
        T = model.clip_times(clip)[-1]
        Ws = [model.world(model.sample(clip, k * T / 48)) for k in range(48)] if T > 0 else [W0]
        lean, head, hip = [], [], []
        for W in Ws:
            d = W[I['B_Neck'], :3, 3] - W[I['B_Pelvis'], :3, 3]
            lean.append(np.degrees(np.arctan2(d[2], d[1])))
            r = W[I['B_Head'], :3, :3] @ W0[I['B_Head'], :3, :3].T     # head rotation relative to Standing
            f = r @ np.array([0, 0, 1.0])
            head.append(np.degrees(np.arctan2(-f[1], f[2])))
            hip.append(W[I['B_Pelvis'], 1, 3])
        print(f'{clip:9} trunk lean {np.mean(lean):5.1f} deg  head pitch {np.mean(head):+5.1f} deg (down +)  '
              f'pelvis {np.mean(hip):.3f} m')


if __name__ == '__main__':
    main()
