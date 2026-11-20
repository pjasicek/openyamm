"""Minimal GLB readers shared by the scripts (positions of every mesh primitive, in glTF space, with node transforms
ignored: the raw converter writes rigid pieces at their bind pose under identity or translated nodes)."""
import json
import struct
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'tools'))
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


def positions(path, meshes=None):
    document, binary = read_glb(Path(path))
    out = []
    for mi, mesh in enumerate(document['meshes']):
        if meshes is not None and mi not in meshes:
            continue
        for p in mesh['primitives']:
            out.append(array(document, binary, p['attributes']['POSITION']))
    return np.concatenate(out) if out else np.zeros((0, 3))


def quat_matrix(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def node_matrix(node):
    if 'matrix' in node:
        return np.array(node['matrix'], float).reshape(4, 4).T
    m = np.eye(4)
    m[:3, :3] = quat_matrix(node.get('rotation', [0, 0, 0, 1])) @ np.diag(node.get('scale', [1, 1, 1]))
    m[:3, 3] = node.get('translation', [0, 0, 0])
    return m


def world_positions(path):
    """Every mesh node's positions in glTF scene space (node transforms applied, skins ignored)."""
    document, binary = read_glb(Path(path))
    nodes = document['nodes']
    parent = {c: i for i, n in enumerate(nodes) for c in n.get('children', [])}

    def world(i):
        m = node_matrix(nodes[i])
        while i in parent:
            i = parent[i]
            m = node_matrix(nodes[i]) @ m
        return m
    out = []
    for i, n in enumerate(nodes):
        if 'mesh' not in n:
            continue
        m = world(i)
        for p in document['meshes'][n['mesh']]['primitives']:
            pos = array(document, binary, p['attributes']['POSITION'])
            out.append(pos @ m[:3, :3].T + m[:3, 3])
    return np.concatenate(out)
