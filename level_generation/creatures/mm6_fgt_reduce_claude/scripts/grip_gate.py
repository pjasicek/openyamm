"""Grip gate in the bind pose: the mace attachment placed at the Mace joint's bind transform, then the right glove's
vertices (weights mostly on B_R_Hand/Finger*) of the source and a reduced body GLB measured against the handle axis:
penetration = glove vertices closer to the axis than the handle radius, gap = nearest glove distance to the handle
surface along the grip span. Usage: grip_gate.py <body glb> <mace glb> [...]"""
import json, struct, sys
import numpy as np
CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def load(p):
    b = open(p, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + n]); bin0 = 20 + n + 8
    def acc(i):
        a = j['accessors'][i]; bv = j['bufferViews'][a['bufferView']]
        o = bin0 + bv.get('byteOffset', 0) + a.get('byteOffset', 0); k = NC[a['type']]; dt = np.dtype(CT[a['componentType']])
        st = bv.get('byteStride', dt.itemsize * k)
        return np.array([np.frombuffer(b, dt, k, o + st * r) for r in range(a['count'])])
    return j, acc


def lod0(j, acc, node_name):
    nd = next(n for n in j['nodes'] if n.get('name') == node_name and 'mesh' in n)
    pr = j['meshes'][nd['mesh']]['primitives'][0]; at = pr['attributes']
    return nd, {k: acc(v) for k, v in at.items()}, acc(pr['indices']).reshape(-1, 3)


def gate(body, mace, ref_axis=None):
    j, acc = load(body); nd, at, _ = lod0(j, acc, 'Thug'); sk = j['skins'][nd['skin']]
    names = [j['nodes'][i]['name'] for i in sk['joints']]; ibm = acc(sk['inverseBindMatrices']).reshape(-1, 4, 4)
    mace_bind = np.linalg.inv(ibm[names.index('Mace')].T)  # column-major -> world from joint
    hand = [i for i, n in enumerate(names) if n.startswith('B_R_Hand') or n.startswith('B_R_Finger')]
    jw = at['JOINTS_0'].astype(int); w = at['WEIGHTS_0'].astype(float)
    hw = sum(w[:, k] * np.isin(jw[:, k], hand) for k in range(4))
    pv = at['POSITION'][hw > .5]
    mj, macc = load(mace); _, mat, _ = lod0(mj, macc, 'Mace')
    mv = (mace_bind @ np.c_[mat['POSITION'], np.ones(len(mat['POSITION']))].T).T[:, :3]
    # handle axis: mace local z through the origin
    o = mace_bind[:3, 3]; ax = mace_bind[:3, 2] / np.linalg.norm(mace_bind[:3, 2])
    t = (pv - o) @ ax; rad = np.linalg.norm((pv - o) - np.outer(t, ax), axis=1)
    span = (t > -.08) & (t < .06)
    return pv, t, rad, span


for body in sys.argv[1:-1]:
    pv, t, rad, span = gate(body, sys.argv[-1])
    R = .0125
    print(body.split('/')[-1], 'glove verts', len(pv), 'in grip span', int(span.sum()),
          'inside r<%.4f: %d' % (R - .001, int(((rad < R - .001) & span).sum())),
          'nearest to axis mm %.1f' % (rad[span].min() * 1000), 'median mm %.1f' % (np.median(rad[span]) * 1000),
          'within 5 mm of handle: %d' % int(((rad < R + .005) & span).sum()))
