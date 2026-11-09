#!/usr/bin/env python3
"""Compare a rebuilt control clip with an accepted clip (dropped-clip pass, 2026-10-31): did the extra-clip route
reproduce the accepted clip route (same resample, post steps and floor fix)?

    compare_clips.py <a.glb> <clipA> <b.glb> <clipB> [--fps 30]

Samples both clips at FPS over the shorter length. Prints the worst rotation difference (degrees) and translation
difference (cm, model units x 100) over non-root joints, with the joint, and the root joints' translation difference
(min / max per axis), which is where floor fixes (hover, raise, grounding) live.
"""
import argparse
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / 'floor'))
import glb_pose  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('a', type=Path)
    parser.add_argument('clip_a')
    parser.add_argument('b', type=Path)
    parser.add_argument('clip_b')
    parser.add_argument('--fps', type=float, default=30.0)
    args = parser.parse_args()
    A, B = glb_pose.Model(glb_pose.Glb(args.a)), glb_pose.Model(glb_pose.Glb(args.b))
    names_b = {n.get('name'): i for i, n in enumerate(B.glb.json['nodes'])}
    ta, tb = A.clip_times(args.clip_a), B.clip_times(args.clip_b)
    length = min(ta[-1] - ta[0], tb[-1] - tb[0])
    print(f'lengths {ta[-1] - ta[0]:.4f} / {tb[-1] - tb[0]:.4f} s')
    roots = {A.glb.json['nodes'][j].get('name') for j in A.root_joints}
    worst_r, worst_t = (0.0, ''), (0.0, '')
    root_d = []
    for t in np.arange(0.0, length + 1e-6, 1.0 / args.fps):
        la, lb = A.sample(args.clip_a, ta[0] + t), B.sample(args.clip_b, tb[0] + t)
        for node in A.joints:
            name = A.glb.json['nodes'][node].get('name')
            if name not in names_b:
                continue
            ra = la.get(node, A.rest[node])
            rb = lb.get(names_b[name], B.rest[names_b[name]])
            dot = abs(float(np.dot(ra[1], rb[1])))
            angle = float(np.degrees(2 * np.arccos(min(1.0, dot))))
            if angle > worst_r[0]:
                worst_r = (angle, f'{name} @ {t:.3f}')
            d = (rb[0] - ra[0]) * 100
            if name in roots:
                root_d.append(d)
            elif np.abs(d).max() > worst_t[0]:
                worst_t = (float(np.abs(d).max()), f'{name} @ {t:.3f}')
    print(f'rotation worst {worst_r[0]:.4f} deg ({worst_r[1]})')
    print(f'translation worst (non-root) {worst_t[0]:.4f} cm ({worst_t[1]})')
    if root_d:
        r = np.array(root_d)
        print('root translation b-a cm: min', np.round(r.min(0), 3), 'max', np.round(r.max(0), 3))


if __name__ == '__main__':
    main()
