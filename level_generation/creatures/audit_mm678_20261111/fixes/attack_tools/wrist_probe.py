#!/usr/bin/env python3
"""Wrist swing and forearm twist per clip (humanoid playbook arm gate item 5: swing <= 60 deg, twist continuous and
<= ~90 deg), measured as the hand's rotation relative to its forearm, against Standing frame 0, split into the twist
about the forearm axis and the remaining swing; also the largest twist step between 48 fps frames.

    wrist_probe.py <glb> <clip>[,<clip>...]
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import donor_attack as da  # noqa: E402


def main():
    glb, clips = sys.argv[1], sys.argv[2].split(',')
    T = da.Skeleton(glb)
    _, W0 = T.world('Standing', 0.0)
    for clip in clips:
        L = T.model.clip_times(clip)[-1]
        out = []
        for s in 'LR':
            f, h = T.idx[f'B_{s}_Forearm'], T.idx[f'B_{s}_Hand']
            rel0 = da.rot_of(W0[f]).T @ da.rot_of(W0[h])
            axis = da.unit(da.rot_of(W0[f]).T @ (W0[h, :3, 3] - W0[f, :3, 3]))
            sw, tw = [], []
            for t in np.arange(0, L + 1e-6, 1 / 48):
                _, W = T.world(clip, t)
                rel = da.rot_of(W[f]).T @ da.rot_of(W[h])
                d = rel @ rel0.T
                q = da.glb_pose.matrix_quaternion(d)
                twist = da.twist_about(q, axis)
                total = math.degrees(math.acos(np.clip((np.trace(d) - 1) / 2, -1, 1)))
                swing_r = d @ da.axis_angle(axis, -twist)
                swing = math.degrees(math.acos(np.clip((np.trace(swing_r) - 1) / 2, -1, 1)))
                sw.append(swing)
                tw.append(math.degrees(twist))
            tw = np.unwrap(np.radians(tw))
            out.append(f"{s}: swing max {max(sw):.0f} twist max {np.degrees(np.abs(tw)).max():.0f} "
                       f"step {np.degrees(np.abs(np.diff(tw))).max() if len(tw) > 1 else 0:.1f}")
        print(f'{clip:10s}', ' | '.join(out))


if __name__ == '__main__':
    main()
