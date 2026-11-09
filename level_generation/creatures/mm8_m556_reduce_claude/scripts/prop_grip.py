#!/usr/bin/env python3
"""Grip faces of the held props: body vertices weighted to the fingers/hand (Hand_*, Claw*), taken into each
attachment joint's space with the skin's inverse bind matrix, and every prop face within REA_GRIP_R (default
12 mm) of one of them -> work/grip_<name>.npy (bool per face of the prop's welded LOD0 as prop_dump.py writes it).
Usage: prop_grip.py   (sword: joint Sword, left hand; shield: joint Shield, right hand)"""
import json, os, struct
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
P = Path(__file__).resolve().parents[1]; W = P / 'work'
R = float(os.environ.get('REA_GRIP_R', '0.012'))


def glb(path):
    raw = Path(path).read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), raw[28 + n:]


def acc(doc, binary, i):
    a = doc['accessors'][i]; bv = doc['bufferViews'][a['bufferView']]
    comp = {5126: np.float32, 5123: np.uint16, 5121: np.uint8, 5125: np.uint32}[a['componentType']]
    k = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0); stride = bv.get('byteStride', 0)
    item = np.dtype(comp).itemsize * k
    if stride and stride != item:
        buf = np.frombuffer(binary, np.uint8, a['count'] * stride, off).reshape(-1, stride)[:, :item]
        return np.ascontiguousarray(buf).view(comp).reshape(a['count'], k)
    return np.frombuffer(binary, comp, a['count'] * k, off).reshape(a['count'], k)


d, b = glb(W / 'mm8_m556_source_pre_reduce.glb')
node = next(n for n in d['nodes'] if n.get('name') == 'Wasp'); prim = d['meshes'][node['mesh']]['primitives'][0]
skin = d['skins'][node['skin']]; ibm = acc(d, b, skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
jn = [d['nodes'][j]['name'] for j in skin['joints']]
pos = acc(d, b, prim['attributes']['POSITION']); J = acc(d, b, prim['attributes']['JOINTS_0']); Wt = acc(d, b, prim['attributes']['WEIGHTS_0'])
if Wt.dtype != np.float32:
    Wt = Wt / 255.0
dom = np.array([jn[J[i, np.argmax(Wt[i])]] for i in range(len(pos))])
for name, joint, side in (('sword', 'Sword', '_L'), ('shield', 'Shield', '_R')):
    fing = np.array([(x.startswith('Hand') or x.startswith('Claw')) and x.endswith(side) for x in dom])
    m = ibm[jn.index(joint)]; hp = (np.c_[pos[fing], np.ones(fing.sum())] @ m.T)[:, :3]
    pd = np.load(W / f'{name}.npz'); v, f = pd['verts'], pd['faces']
    # prop_dump writes Blender space (z up); glTF joint space is y up: (x, y, z)_gl -> (x, -z, y)_blender
    hb = np.c_[hp[:, 0], -hp[:, 2], hp[:, 1]]
    dist = cKDTree(hb).query(v)[0]; near = dist < R
    grip = near[f].any(1)
    np.save(W / f'grip_{name}.npy', grip)
    print('GRIP', name, int(fing.sum()), 'finger verts; nearest prop vertex', round(float(dist.min() * 1000), 1), 'mm;',
          int(grip.sum()), 'of', len(f), 'faces kept')
