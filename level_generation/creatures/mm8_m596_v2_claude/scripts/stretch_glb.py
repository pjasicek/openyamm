#!/usr/bin/env python3
"""Stretched faces of a GLB's clips on every mesh (LODs included), without Blender: a face stretches when its
longest edge grows over LIMIT x its rest length. Prints per mesh and clip the worst ratio and the face count over
the limit, plus the rest centre of the worst face and its vertices' dominant joints.
Usage: stretch_glb.py <glb> [clip ...] (default: every clip)"""
from pathlib import Path
import re
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402

LIMIT = 3.0


def main():
    glb = Glb(sys.argv[1]); model = Model(glb)
    doc = glb.json; names = [n.get('name', '') for n in doc['nodes']]
    meshes = []
    # LOD and shadow meshes are stored unreferenced beside the skinned LOD0 node and share its skin
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            a = primitive['attributes']
            if 'JOINTS_0' not in a:
                continue
            w = glb.accessor(a['WEIGHTS_0']).astype(np.float64)
            meshes.append((mesh.get('name'), glb.accessor(a['POSITION']).astype(np.float64),
                           glb.accessor(primitive['indices']).astype(np.int64).reshape(-1, 3),
                           glb.accessor(a['JOINTS_0']).astype(np.int64), w / w.sum(axis=1, keepdims=True)))
    clips = sys.argv[2:] or [a['name'] for a in doc['animations']]
    for name, pos, tri, joints, weights in meshes:
        rest = edges(pos, tri)
        for clip in clips:
            worst, count, face = 1.0, set(), -1
            for t in np.linspace(0, model.clip_times(clip)[-1], 49):
                world = model.world(model.sample(clip, t))
                palette = world[model.joints] @ model.inverse_binds
                blended = np.einsum('vk,vkij->vij', weights, palette[joints])
                p = np.einsum('vij,vj->vi', blended, np.c_[pos, np.ones(len(pos))])[:, :3]
                ratio = edges(p, tri) / np.maximum(rest, 1e-5)
                over = np.nonzero(ratio > LIMIT)[0]; count.update(over.tolist())
                if ratio.max() > worst:
                    worst, face = float(ratio.max()), int(ratio.argmax())
            info = ''
            if face >= 0 and worst > LIMIT:
                dom = {names[model.joints[joints[v][np.argmax(weights[v])]]] for v in tri[face]}
                info = f' worst face at {np.round(pos[tri[face]].mean(0), 3).tolist()} joints {sorted(dom)}'
            print(f'{name[:28]:28} {clip:10} max x{worst:5.2f}  faces over x{LIMIT:g}: {len(count)}{info}')


def edges(p, tri):
    a, b, c = (p[tri[:, k]] for k in range(3))
    return np.maximum.reduce([np.linalg.norm(b - a, axis=1), np.linalg.norm(c - b, axis=1),
                              np.linalg.norm(a - c, axis=1)])


if __name__ == '__main__':
    main()
