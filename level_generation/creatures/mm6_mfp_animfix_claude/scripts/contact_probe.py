#!/usr/bin/env python3
"""Arm and prop contacts against the legs and trunk of a pirate GLB, per clip (G6-style, approximate).

    contact_probe.py <body.glb> <clip>[,<clip>...] [node=attachment.glb ...] [--rate 60]

Posed LOD0 skin per sample; a probe point is inside when its nearest skin vertex of the target group lies within
4 cm and the point is behind that vertex's normal. Probes: every attachment's vertices (placed at its node), and the
arm vertices (dominated by clavicle/arm/forearm/hand/finger/twist bones). Targets: vertices dominated by the legs,
pelvis and spine (env PROBE_TARGET, comma list of bone-name parts: an open coat calls for Calf,Foot,Toe) (the arms' own skin and the holding hand are not targets). Prints, per clip and probe, the share of
samples with a point inside and the deepest point (mm). Compare new clips with the model's accepted Walking and
Running: the arms and props of the new clips are those clips' own, so only the legs and trunk differ.
"""
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose  # noqa: E402

ARM = ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger')
import os
TARGET = tuple(os.environ.get('PROBE_TARGET', 'Thigh,Calf,Foot,Toe,Pelvis,Spine').split(','))


def vertex_normals(points, triangles):
    n = np.zeros_like(points)
    face = np.cross(points[triangles[:, 1]] - points[triangles[:, 0]], points[triangles[:, 2]] - points[triangles[:, 0]])
    for c in range(3):
        np.add.at(n, triangles[:, c], face)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    rate = 60
    body = glb_pose.Glb(args[0])
    model = glb_pose.Model(body)
    names = [n['name'] for n in body.json['nodes']]
    clips = args[1].split(',')
    attachments = {}
    for item in args[2:]:
        node, path = item.split('=', 1)
        g = glb_pose.Glb(path)
        m = glb_pose.Model(g)
        pts = np.concatenate([p['positions'] for p in m.primitives])
        attachments[node] = pts
    prim = model.primitives[0]
    dominant = [names[model.joints[j]] for j in prim['joints'][np.arange(len(prim['joints'])),
                                                              prim['weights'].argmax(axis=1)]]
    arm = np.array([any(t in d for t in ('Forearm', 'Hand', 'Finger')) for d in dominant])
    target = np.array([any(t in d for t in TARGET) and not any(t in d for t in ARM) for d in dominant])
    tri = prim['triangles']
    for clip in clips:
        times = model.clip_times(clip)
        samples = np.arange(0, times[-1], 1.0 / rate)
        stats = {}
        for t in samples:
            W = model.world(model.sample(clip, float(t)))
            points, _ = model.skinned_positions(W)[0]
            normals = vertex_normals(points, tri)
            tree = cKDTree(points[target])
            tpts, tnrm = points[target], normals[target]
            probes = {'arms': points[arm]}
            for node, pts in attachments.items():
                M = W[names.index(node)]
                if np.linalg.norm(M[:3, :3]) < 1e-6:
                    continue
                probes[node] = pts @ M[:3, :3].T + M[:3, 3]
            for name, p in probes.items():
                d, i = tree.query(p)
                depth = np.einsum('ij,ij->i', p - tpts[i], tnrm[i])
                inside = (d < 0.04) & (depth < -0.002)
                s = stats.setdefault(name, [0, 0.0, 0])
                s[2] += 1
                if inside.any():
                    s[0] += 1
                    s[1] = max(s[1], float(-depth[inside].min()))
        cells = '  '.join(f'{n}: {100 * s[0] / s[2]:.0f}% max {1000 * s[1]:.0f} mm' for n, s in stats.items())
        print(f'{clip:10} {cells}')


if __name__ == '__main__':
    main()
