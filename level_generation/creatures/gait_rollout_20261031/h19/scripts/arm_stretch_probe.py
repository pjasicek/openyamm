#!/usr/bin/env python3
"""Arm and hand skin stretch per clip (G4/G5 of the humanoid playbook on the GLB): edges of LOD0 triangles whose two
vertices carry more than 0.3 weight on arm bones (clavicle, upper arm, forearm, twist, hand, fingers); posed over rest
(Standing at 0 s) length ratio, per side: p99 and max over the loop (60 Hz), and the count of edges above 1.5x.
New clips must not stretch the arms more than the model's accepted clips (their arms are those clips' own, with the
swing scaled about its mean by `side_gain`).

    arm_stretch_probe.py <glb> <clip>[,<clip>...]
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose, open_glb  # noqa: E402

ARM = ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger')


def main():
    glb = open_glb(sys.argv[1])
    model = glb_pose.Model(glb)
    names = [n['name'] for n in glb.json['nodes']]
    prim = model.primitives[0]
    weights = np.zeros((len(prim['positions']), 2))
    for k in range(prim['joints'].shape[1]):
        bone = [names[model.joints[j]] for j in prim['joints'][:, k]]
        for c, s in enumerate('LR'):
            weights[:, c] += prim['weights'][:, k] * np.array([b.startswith(f'B_{s}_') and any(a in b for a in ARM)
                                                               for b in bone])
    tri = prim['triangles']
    edges = np.unique(np.sort(np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]]), axis=1), axis=0)
    rest = model.skinned_positions(model.world(model.sample('Standing', 0.0)))[0][0]
    rl = np.linalg.norm(rest[edges[:, 0]] - rest[edges[:, 1]], axis=1)
    sides = {s: (weights[edges[:, 0], c] > 0.3) & (weights[edges[:, 1], c] > 0.3) & (rl > 1e-5)
             for c, s in enumerate('LR')}
    for clip in sys.argv[2].split(','):
        T = model.clip_times(clip)[-1]
        n = max(int(round(T * 60)), 1)
        ratios = []
        for k in range(n):
            p = model.skinned_positions(model.world(model.sample(clip, k * T / n)))[0][0]
            ratios.append(np.linalg.norm(p[edges[:, 0]] - p[edges[:, 1]], axis=1) / np.maximum(rl, 1e-9))
        ratios = np.array(ratios)
        cells = []
        for s, m in sides.items():
            r = ratios[:, m]
            cells.append(f'{s} p99 {np.percentile(r, 99):.2f} max {r.max():.2f} >1.5x {(r.max(axis=0) > 1.5).sum()}')
        print(f'{clip:9} ' + '  '.join(cells))


if __name__ == '__main__':
    main()
