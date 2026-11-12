#!/usr/bin/env python3
"""Model-space track of nodes over a clip, to place the contact key (attacks-2, 2026-11-11).

    track.py <glb> <clip> <node>[,<node>...] [--fps 30] [--axis z]

Prints per sample the node positions and speeds; marks the sample where the first node's coordinate along --axis
(x, y, z, or -x ...) is largest (the reach) and where its speed peaks.
"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared' / 'floor'))
import glb_pose  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument('glb')
    p.add_argument('clip')
    p.add_argument('nodes')
    p.add_argument('--fps', type=float, default=30)
    p.add_argument('--axis', default='z')
    a = p.parse_args()
    g = glb_pose.Glb(a.glb)
    m = glb_pose.Model(g)
    names = [n.get('name') for n in g.json['nodes']]
    idx = [names.index(n) for n in a.nodes.split(',')]
    ts = m.clip_times(a.clip)
    times = np.arange(ts[0], ts[-1] + 1e-6, 1 / a.fps)
    pos = np.array([[m.world(m.sample(a.clip, t))[i][:3, 3] for i in idx] for t in times])
    sign = -1 if a.axis.startswith('-') else 1
    k = 'xyz'.index(a.axis[-1])
    along = sign * pos[:, 0, k]
    speed = np.r_[0, np.linalg.norm(np.diff(pos[:, 0], axis=0), axis=1) * a.fps]
    for i, t in enumerate(times):
        mark = (' <reach' if i == np.argmax(along) else '') + (' <speed' if i == np.argmax(speed) else '')
        print(f'{t:6.3f} ' + '  '.join(np.array2string(q, precision=3) for q in pos[i]) + f'  v {speed[i]:5.2f}{mark}')


if __name__ == '__main__':
    main()
