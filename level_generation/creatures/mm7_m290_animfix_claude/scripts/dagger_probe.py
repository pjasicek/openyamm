#!/usr/bin/env python3
"""Thief (m410): how far the sheathed dagger's node drifts from its sheath per clip. Sheath vertices: skin weighted
to B_Pelvis and B_L_Thigh only, with a thigh share of 0.15-0.35 (the 0.75 / 0.25 sheath weighting of the source
project). Each sample: the sheath vertices in the Dagger node's frame, compared with Standing's (max offset, cm).

    dagger_probe.py <glb> <clip>[,<clip>...]
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose  # noqa: E402


def sheath_ids(model, names):
    prim = model.primitives[0]
    joints = np.asarray(model.joints)[prim['joints']]
    w = prim['weights']
    pel, thigh = names.index('B_Pelvis'), names.index('B_L_Thigh')
    share_t = (w * (joints == thigh)).sum(axis=1)
    share_p = (w * (joints == pel)).sum(axis=1)
    return np.where((share_t + share_p > 0.99) & (share_t > 0.15) & (share_t < 0.35))[0]


def main():
    glb = glb_pose.Glb(sys.argv[1])
    model = glb_pose.Model(glb)
    names = [n['name'] for n in glb.json['nodes']]
    ids = sheath_ids(model, names)
    d = names.index('Dagger')

    def local(W):
        p = model.skinned_positions(W)[0][0][ids]
        return (p - W[d, :3, 3]) @ (W[d, :3, :3] / np.linalg.norm(W[d, :3, :3], axis=0))

    ref = local(model.world(model.sample('Standing', 0.0)))
    print('sheath vertices', len(ids))
    for clip in sys.argv[2].split(','):
        T = model.clip_times(clip)[-1]
        errs = [np.linalg.norm(local(model.world(model.sample(clip, k * T / 48))) - ref, axis=1).max()
                for k in range(48)]
        print(f'{clip:9} dagger vs sheath: max {100 * max(errs):.2f} cm, median {100 * np.median(errs):.2f} cm')


if __name__ == '__main__':
    main()
