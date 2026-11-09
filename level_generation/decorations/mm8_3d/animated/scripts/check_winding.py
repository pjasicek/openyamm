#!/usr/bin/env python3
"""Face-orientation check of an exported or finished GLB (the engine culls back faces of single-sided materials;
Blender's review renders do not, so an inverted surface only shows in game). For every primitive of every mesh, the
triangles are split into connected parts (shared positions); a closed part's signed volume must be positive
(normals outward). Open parts are listed with their area-weighted mean normal for inspection.
Usage: check_winding.py <glb> [...]"""
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / 'tools'))
from link_static_model_lods import read_glb  # noqa: E402

TYPES = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
WIDTH = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def array(document, binary, index):
    accessor = document['accessors'][index]
    view = document['bufferViews'][accessor['bufferView']]
    dtype = np.dtype(TYPES[accessor['componentType']])
    width = WIDTH[accessor['type']]
    start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    stride = view.get('byteStride', dtype.itemsize * width)
    raw = np.frombuffer(binary, np.uint8, accessor['count'] * stride, start).reshape(accessor['count'], stride)
    return raw[:, :dtype.itemsize * width].copy().view(dtype).reshape(accessor['count'], width)


def components(tris, keys):
    parent = list(range(len(tris)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    owner = {}
    for t, tri in enumerate(tris):
        for v in tri:
            k = keys[v]
            if k in owner:
                ra, rb = find(owner[k]), find(t)
                if ra != rb:
                    parent[ra] = rb
            else:
                owner[k] = t
    groups = defaultdict(list)
    for t in range(len(tris)):
        groups[find(t)].append(t)
    return list(groups.values())


def check(path):
    document, binary = read_glb(Path(path))
    bad = 0
    for mesh in document['meshes']:
        # All single-sided primitives of a mesh together: a closed part may span materials (a log's bark and ends).
        positions, triangles, names = [], [], []
        offset = 0
        for prim in mesh['primitives']:
            material = document['materials'][prim['material']]
            if material.get('doubleSided') or material.get('alphaMode') == 'BLEND':
                continue
            pos = array(document, binary, prim['attributes']['POSITION']).astype(np.float64)
            tris = array(document, binary, prim['indices']).reshape(-1, 3).astype(np.int64) + offset
            positions.append(pos)
            triangles.append(tris)
            names += [material['name']] * len(tris)
            offset += len(pos)
        if not positions:
            continue
        pos = np.concatenate(positions)
        tris = np.concatenate(triangles)
        keys = [tuple(np.round(p, 5)) for p in pos]
        for part in components(tris, keys):
            t = tris[part]
            a, b, c = pos[t[:, 0]], pos[t[:, 1]], pos[t[:, 2]]
            edges = defaultdict(int)
            for tri in t:
                for i in range(3):
                    edges[tuple(sorted((keys[tri[i]], keys[tri[(i + 1) % 3]])))] += 1
            closed = all(n == 2 for n in edges.values())
            volume = float(np.einsum('ij,ij->i', a, np.cross(b, c)).sum()) / 6
            centre = (a + b + c).mean(0) / 3
            if closed and volume < 0:
                bad += 1
                materials = sorted({names[i] for i in part})
                print(f'INVERTED {mesh["name"]} {"+".join(materials)} closed part of {len(t)} triangles at '
                      f'{np.round(centre * 81.7, 1)} units, volume {volume:.6f}')
    print('WINDING', Path(path).name, 'inverted closed parts:', bad)
    return bad


if __name__ == '__main__':
    total = sum(check(p) for p in sys.argv[1:])
    sys.exit(1 if total else 0)
