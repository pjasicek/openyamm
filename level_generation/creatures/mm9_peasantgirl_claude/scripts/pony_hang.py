#!/usr/bin/env python3
"""Long hair hangs (PeasantGirl): MM9's Ponytail chain turns rigidly with the bowed head (Hit: 72 deg from down; MM9's hair ends at the
shoulders, ours at mid-back, so it stuck out behind like a horn). Per key, the Ponytail1 -> Ponytail11 world direction's angle from
straight down is soft-clamped (a above A0 becomes A0 + (a - A0) * K), turning Ponytail1 in world space about its own joint by the least
rotation; Ponytail11 follows as its child. Nothing below A0 changes (Standing 15 deg). Args: <in glb> <out glb> [A0 deg] [K]"""
import sys
from pathlib import Path
import numpy as np
from pygltflib import GLTF2
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, quaternion_matrix, matrix_quaternion
IN, OUT = sys.argv[1:3]; A0 = float(sys.argv[3]) if len(sys.argv) > 3 else 35.0; K = float(sys.argv[4]) if len(sys.argv) > 4 else 0.3
g = GLTF2().load(IN); blob = bytearray(g.binary_blob()); names = [n.name for n in g.nodes]
m = Model(Glb(IN)); i1 = names.index('Bip01 Ponytail1'); i2 = names.index('Bip01 Ponytail11'); ip = names.index('Bip01 Head')
def rot(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b); v = np.cross(a, b); c = a @ b; s = np.linalg.norm(v)
    if s < 1e-9: return np.eye(3)
    Kx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); return np.eye(3) + Kx + Kx @ Kx * ((1 - c) / s ** 2)
down = np.array([0, -1.0, 0])      # glTF y up
rep = {}
SKIP = ('Death', 'Dead')      # a lying body: the hair lies on the floor (MM9's own pose), never hung through it
for an in g.animations:
    if an.name in SKIP: continue
    ch = next(c for c in an.channels if c.target.node == i1 and c.target.path == 'rotation')
    s = an.samplers[ch.sampler]; ta = g.accessors[s.input]; tv = g.bufferViews[ta.bufferView]
    ts = np.frombuffer(bytes(blob[(tv.byteOffset or 0) + (ta.byteOffset or 0):(tv.byteOffset or 0) + (ta.byteOffset or 0) + 4 * ta.count]), 'f4')
    x = g.accessors[s.output]; v = g.bufferViews[x.bufferView]; o = (v.byteOffset or 0) + (x.byteOffset or 0)
    Q = np.frombuffer(blob, 'f4', x.count * 4, o).reshape(x.count, 4).copy().astype(float)
    worst = 0
    for k, t in enumerate(ts):
        W = m.world(m.sample(an.name, float(t)))
        d = W[i2][:3, 3] - W[i1][:3, 3]; d /= np.linalg.norm(d)
        a = np.degrees(np.arccos(np.clip(d @ down, -1, 1))); worst = max(worst, a)
        if a <= A0: continue
        a2 = A0 + (a - A0) * K
        # rotate d toward down by (a - a2) about d x down
        ax = np.cross(d, down); ax /= np.linalg.norm(ax); th = np.radians(a - a2)
        Kx = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]]); R = np.eye(3) + np.sin(th) * Kx + (1 - np.cos(th)) * Kx @ Kx
        Pr = W[ip][:3, :3]; Rp = Pr / np.linalg.norm(Pr, axis=0)
        L = quaternion_matrix(Q[k])[:3, :3] if quaternion_matrix(Q[k]).shape[0] == 4 else quaternion_matrix(Q[k])
        Ln = Rp.T @ R @ Rp @ L
        Q[k] = matrix_quaternion(Ln)
    for k in range(1, len(Q)):
        if Q[k] @ Q[k - 1] < 0: Q[k] = -Q[k]
    blob[o:o + Q.size * 4] = Q.astype('f4').tobytes(); rep[an.name] = round(float(worst), 1)
g.set_binary_blob(bytes(blob)); g.save(OUT); print('PONY hang, worst angle before', rep)
