#!/usr/bin/env python3
"""Coarse-LOD floor repair (in place): a LOD1-3 colour or shadow vertex that sinks more than TOL under the floor in
Death, Death2 or Dead (8 influences, every key time) takes the rest position and skin weights of the nearest LOD0 vertex.
s82: the LOD3 collapse gave one wing-root vertex a Ywamid01/spine blend that sank 8.1 cm in Death2's end pose; protected
floor contacts and other wing LOD3 ratios did not move it. Usage: fix_lod_floor.py <glb> [TOL m, default 0.004]"""
import struct, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parents[2] / 'tools')); sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from build_actor_lods import read_glb, write_glb, accessor_bytes  # noqa: E402
from glb_pose import Glb, Model  # noqa: E402
path = Path(sys.argv[1]); TOL = float(sys.argv[2]) if len(sys.argv) > 2 else 0.004
doc, binary = read_glb(path); binary = bytearray(binary)
m = Model(Glb(str(path)))
node = next(n for n in doc['nodes'] if n.get('name') == 'Wmut'); ex = doc['meshes'][node['mesh']]['extras']
lods = ex['openyamm_lods'] + ex.get('openyamm_shadow_lods', [])[1:]
ref_p = np.vstack([p['positions'] for p in m.primitives]); ref_j = np.vstack([p['joints'] for p in m.primitives])
ref_w = np.vstack([p['weights'] for p in m.primitives]); tree = cKDTree(ref_p)
pals = []
for clip in ('Death', 'Death2', 'Dead'):
    for t in m.clip_times(clip):
        w = m.world(m.sample(clip, t)); pals.append(w[m.joints] @ m.inverse_binds)


def acc(idx, dt, n):
    a = doc['accessors'][idx]; v = doc['bufferViews'][a['bufferView']]; o = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    return o, np.frombuffer(bytes(binary[o:o + a['count'] * n * np.dtype(dt).itemsize]), dt).reshape(-1, n).copy()


fixed = 0
for mi in lods:
    for prim in doc['meshes'][mi]['primitives']:
        at = prim['attributes']
        op, P = acc(at['POSITION'], np.float32, 3)
        oj0, J0 = acc(at['JOINTS_0'], np.uint8, 4); ow0, W0 = acc(at['WEIGHTS_0'], np.float32, 4)
        oj1, J1 = acc(at['JOINTS_1'], np.uint8, 4) if 'JOINTS_1' in at else (None, np.zeros_like(J0))
        ow1, W1 = acc(at['WEIGHTS_1'], np.float32, 4) if 'WEIGHTS_1' in at else (None, np.zeros_like(W0))

        def low():
            J = np.c_[J0, J1].astype(int); Wt = np.c_[W0, W1]; Wt = Wt / np.maximum(Wt.sum(1, keepdims=True), 1e-12)
            h = np.c_[P, np.ones(len(P))]; out = np.full(len(P), 9.0)
            for pal in pals:
                M = np.einsum('vk,vkij->vij', Wt, pal[J]); y = np.einsum('vij,vj->vi', M, h)[:, 1]; out = np.minimum(out, y)
            return out
        y = low(); bad = np.flatnonzero(y < -TOL)
        if not len(bad):
            continue
        _, nn = tree.query(P[bad])
        J0[bad] = ref_j[nn]; W0[bad] = ref_w[nn]; J1[bad] = 0; W1[bad] = 0
        P[bad] = ref_p[nn]   # and its rest position: the weights alone left it 4.3 cm under (it sat off the LOD0 surface)
        binary[op:op + P.nbytes] = P.astype(np.float32).tobytes()
        y2 = low()
        print(f'{doc["meshes"][mi]["name"]}: {len(bad)} vertices under -{TOL} m (worst {y.min():.4f}) -> worst now {y2.min():.4f}')
        binary[oj0:oj0 + J0.nbytes] = J0.tobytes(); binary[ow0:ow0 + W0.nbytes] = W0.tobytes()
        if oj1 is not None:
            binary[oj1:oj1 + J1.nbytes] = J1.tobytes(); binary[ow1:ow1 + W1.nbytes] = W1.tobytes()
        fixed += len(bad)
write_glb(path, doc, bytes(binary)); print('FIXED', fixed)
