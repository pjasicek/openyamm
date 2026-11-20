#!/usr/bin/env python3
"""Where an attachment (the sword) enters the legs/trunk skin: per sample inside, the phase, depth, the target bone and
the share of the blade's length (0 = grip end, 1 = tip) of the deepest point. Same inside test as contact_probe.py.

    sword_probe.py <body.glb> <clip> <node>=<attachment.glb>
"""
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose  # noqa: E402
from contact_probe import ARM, TARGET, vertex_normals  # noqa: E402


def main():
    body = glb_pose.Glb(sys.argv[1])
    model = glb_pose.Model(body)
    names = [n['name'] for n in body.json['nodes']]
    clip = sys.argv[2]
    node, path = sys.argv[3].split('=', 1)
    att = np.concatenate([p['positions'] for p in glb_pose.Model(glb_pose.Glb(path)).primitives])
    axis = att - att.mean(axis=0)
    main_axis = np.linalg.svd(axis, full_matrices=False)[2][0]
    along = axis @ main_axis
    share = (along - along.min()) / np.ptp(along)
    prim = model.primitives[0]
    dominant = [names[model.joints[j]] for j in prim['joints'][np.arange(len(prim['joints'])),
                                                              prim['weights'].argmax(axis=1)]]
    target = np.array([any(t in d for t in TARGET) and not any(t in d for t in ARM) for d in dominant])
    tnames = np.array(dominant)[target]
    T = model.clip_times(clip)[-1]
    n = int(round(T * 60))
    for k in range(n):
        W = model.world(model.sample(clip, k * T / n))
        points, _ = model.skinned_positions(W)[0]
        normals = vertex_normals(points, prim['triangles'])
        tree = cKDTree(points[target])
        M = W[names.index(node)]
        p = att @ M[:3, :3].T + M[:3, 3]
        d, i = tree.query(p)
        depth = np.einsum('ij,ij->i', p - points[target][i], normals[target][i])
        inside = (d < 0.04) & (depth < -0.002)
        if inside.any():
            j = np.argmin(np.where(inside, depth, 0))
            print(f'{k / n:.2f} {1000 * -depth[j]:5.1f} mm into {tnames[i[j]]}, blade share {share[j]:.2f}, '
                  f'{inside.sum()} points')


if __name__ == '__main__':
    main()
