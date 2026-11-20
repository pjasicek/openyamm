#!/usr/bin/env python3
"""Lowest skin point per clip (the floor audit's measure) and where it is: time, dominant bone, height in cm.

    low_probe.py <glb> <clip>[,<clip>...] [scale]
With a scale (actors.yml), also prints the world units the floor audit compares with its tolerance.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose  # noqa: E402


def main():
    glb = glb_pose.Glb(sys.argv[1])
    model = glb_pose.Model(glb)
    scale = float(sys.argv[3]) if len(sys.argv) > 3 else None
    names = [n['name'] for n in glb.json['nodes']]
    prim = model.primitives[0]
    dom = prim['joints'][np.arange(len(prim['joints'])), prim['weights'].argmax(axis=1)]
    for clip in sys.argv[2].split(','):
        rows = []
        for t in model.clip_times(clip):
            points = model.skinned_positions(model.world(model.sample(clip, float(t))))[0][0]
            i = int(np.argmin(points[:, 1]))
            rows.append((points[i, 1], float(t), names[model.joints[dom[i]]]))
        low, t, bone = min(rows)
        world = f'  world {low * scale:+.1f}' if scale else ''
        sinking = sorted({b for h, _, b in rows if h < -0.01})
        print(f'{clip:9} lowest {100 * low:+.2f} cm at {t:.3f} s ({bone}){world}  keys below -1 cm: '
              f'{sum(h < -0.01 for h, _, _ in rows)}/{len(rows)} {sinking}')


if __name__ == '__main__':
    main()
