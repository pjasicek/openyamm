"""Shared GLB helpers for the cage bird: reading accessors, evaluating node transforms at a clip time, and skinning a
mesh (LOD0..3) into a pose."""
import json
import struct
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[2]
sys.path.insert(0, str(REPO / 'tools'))
from link_static_model_lods import read_glb, write_glb  # noqa: E402,F401

CROW = REPO / 'assets_source/worlds/mm9/models/mm9_crow.glb'
TYPES = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
WIDTH = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def array(doc, binary, index):
    accessor = doc['accessors'][index]
    view = doc['bufferViews'][accessor['bufferView']]
    dtype = np.dtype(TYPES[accessor['componentType']])
    width = WIDTH[accessor['type']]
    start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    stride = view.get('byteStride', dtype.itemsize * width)
    raw = np.frombuffer(bytes(binary), np.uint8, accessor['count'] * stride - (stride - dtype.itemsize * width),
                        start)
    raw = np.lib.stride_tricks.as_strided(raw, (accessor['count'], dtype.itemsize * width), (stride, 1))
    out = raw.copy().view(dtype).reshape(accessor['count'], width)
    if accessor.get('normalized'):
        out = out.astype(np.float64) / np.iinfo(dtype).max
    return out


def quat_matrix(q):
    x, y, z, w = np.asarray(q, float) / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def trs(t, r, s=(1, 1, 1)):
    m = np.identity(4)
    m[:3, :3] = quat_matrix(r) @ np.diag(s)
    m[:3, 3] = t
    return m


def slerp(a, b, t):
    a, b = np.array(a, float), np.array(b, float)
    if np.dot(a, b) < 0:
        b = -b
    d = np.clip(np.dot(a, b), -1, 1)
    if d > 0.9995:
        q = a + t * (b - a)
    else:
        th = np.arccos(d)
        q = (np.sin((1 - t) * th) * a + np.sin(t * th) * b) / np.sin(th)
    return q / np.linalg.norm(q)


class Model:
    def __init__(self, path=CROW):
        self.doc, self.bin = read_glb(Path(path))
        self.parent = {c: i for i, n in enumerate(self.doc['nodes']) for c in n.get('children', [])}
        self.tracks = {}
        for animation in self.doc.get('animations', []):
            tracks = {}
            for channel in animation['channels']:
                sampler = animation['samplers'][channel['sampler']]
                tracks[(channel['target']['node'], channel['target']['path'])] = (
                    array(self.doc, self.bin, sampler['input']).ravel(),
                    array(self.doc, self.bin, sampler['output']).astype(float))
            self.tracks[animation['name']] = tracks

    def duration(self, clip):
        return max(float(times[-1]) for times, _ in self.tracks[clip].values())

    def local_trs(self, index, clip=None, time=0.0):
        node = self.doc['nodes'][index]
        values = {'translation': np.array(node.get('translation', [0, 0, 0]), float),
                  'rotation': np.array(node.get('rotation', [0, 0, 0, 1]), float),
                  'scale': np.array(node.get('scale', [1, 1, 1]), float)}
        for path in values:
            track = self.tracks.get(clip, {}).get((index, path)) if clip else None
            if track is None:
                continue
            times, out = track
            if time <= times[0]:
                values[path] = out[0]
            elif time >= times[-1]:
                values[path] = out[-1]
            else:
                k = int(np.searchsorted(times, time)) - 1
                f = (time - times[k]) / (times[k + 1] - times[k])
                values[path] = slerp(out[k], out[k + 1], f) if path == 'rotation' \
                    else out[k] + f * (out[k + 1] - out[k])
        return values

    def local(self, index, clip=None, time=0.0):
        v = self.local_trs(index, clip, time)
        return trs(v['translation'], v['rotation'], v['scale'])

    def world(self, index, clip=None, time=0.0):
        m = self.local(index, clip, time)
        while index in self.parent:
            index = self.parent[index]
            m = self.local(index, clip, time) @ m
        return m

    def joint_matrices(self, skin_index, clip=None, time=0.0):
        skin = self.doc['skins'][skin_index]
        ibm = array(self.doc, self.bin, skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
        return np.array([self.world(j, clip, time) @ ibm[k] for k, j in enumerate(skin['joints'])])

    def skin_primitive(self, prim, joints):
        """(positions, normals) of a skinned primitive under joint matrices (n_joints, 4, 4)."""
        a = prim['attributes']
        p = array(self.doc, self.bin, a['POSITION']).astype(float)
        n = array(self.doc, self.bin, a['NORMAL']).astype(float)
        m = np.zeros((len(p), 4, 4))
        for s in range(4):
            if f'JOINTS_{s}' not in a:
                break
            j = array(self.doc, self.bin, a[f'JOINTS_{s}']).astype(int)
            w = array(self.doc, self.bin, a[f'WEIGHTS_{s}']).astype(float)
            m += np.einsum('nk,nkij->nij', w, joints[j])
        ph = np.c_[p, np.ones(len(p))]
        pos = np.einsum('nij,nj->ni', m, ph)[:, :3]
        nrm = np.einsum('nij,nj->ni', m[:, :3, :3], n)
        nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
        return pos, nrm


def lod_meshes(doc):
    """The draw chain [LOD0, LOD1, LOD2, LOD3] mesh indices of the first skinned node."""
    node = next(n for n in doc['nodes'] if 'mesh' in n and 'skin' in n)
    base = node['mesh']
    return [base] + list(doc['meshes'][base].get('extras', {}).get('openyamm_lods', []))
