#!/usr/bin/env python3
"""Crotch skin stretch per clip (h22, the Plane Guardian's inner thighs): LOD0 edges with both vertices within 12 cm of
the midline and between 15 cm below and 10 cm above Standing's hip joints, carrying thigh weight; posed over rest
(Standing at 0 s) length ratio over the loop (60 Hz): p99, max and the count of edges above 1.5x. New clips should
stretch the crotch no more than the accepted Walking and Running.

    crotch_stretch_probe.py <glb> <clip>[,<clip>...]
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
    prim = model.primitives[0]
    thigh = np.zeros(len(prim['positions']))
    for k in range(prim['joints'].shape[1]):
        bone = np.array([names[model.joints[j]] for j in prim['joints'][:, k]])
        thigh += prim['weights'][:, k] * np.char.endswith(bone.astype(str), '_Thigh')
    W0 = model.world(model.sample('Standing', 0.0))
    hip_y = W0[I['B_L_Thigh'], 1, 3]
    rest = model.skinned_positions(W0)[0][0]
    sel = (np.abs(rest[:, 0]) < 0.12) & (rest[:, 1] > hip_y - 0.15) & (rest[:, 1] < hip_y + 0.10) & (thigh > 0.2)
    tri = prim['triangles']
    edges = np.unique(np.sort(np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]]), axis=1), axis=0)
    edges = edges[sel[edges[:, 0]] & sel[edges[:, 1]]]
    rl = np.linalg.norm(rest[edges[:, 0]] - rest[edges[:, 1]], axis=1)
    edges, rl = edges[rl > 1e-5], rl[rl > 1e-5]
    print(f'{len(edges)} crotch edges')
    for clip in sys.argv[2].split(','):
        T = model.clip_times(clip)[-1]
        n = max(int(round(T * 60)), 1)
        r = []
        for k in range(n):
            p = model.skinned_positions(model.world(model.sample(clip, k * T / n)))[0][0]
            r.append(np.linalg.norm(p[edges[:, 0]] - p[edges[:, 1]], axis=1) / rl)
        r = np.array(r)
        print(f'{clip:9} crotch p99 {np.percentile(r, 99):.2f} max {r.max():.2f} >1.5x {(r.max(axis=0) > 1.5).sum()}')


if __name__ == '__main__':
    main()
