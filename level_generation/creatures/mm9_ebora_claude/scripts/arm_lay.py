#!/usr/bin/env python3
"""(wing_settle) Death and Dead: MM9's die2 lays the left forearm over the raised left wing fan (60-100 arm edges through the
membrane). The wing root (Bone48 / Bone13) is turned about the world vertical at its head, so the fan sweeps in the
floor plane away from the arm (no floor change): eased in with a smoothstep from T0 to T1 seconds of Death, held through
the end of Death and the whole of Dead. Runs on the raw clip GLB (before half joints, mirror). Args: <in glb> <out glb>
<root bone> <deg> [t0 t1]"""
import os, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, matrix_quaternion, quaternion_matrix
from pygltflib import GLTF2, Accessor, BufferView
IN, OUT, ROOT = sys.argv[1:4]; DEG = float(sys.argv[4]); T0 = float(sys.argv[5]) if len(sys.argv) > 5 else 0.55
T1 = float(sys.argv[6]) if len(sys.argv) > 6 else 0.95
m = Model(Glb(IN)); doc = m.glb.json; names = [n.get('name') for n in doc['nodes']]; ix = {n: i for i, n in enumerate(names)}
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
def read(acc):
    a = g.accessors[acc]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a.type]
    o = (bv.byteOffset or 0) + (a.byteOffset or 0)
    return np.frombuffer(bytes(blob[o:o + 4 * n * a.count]), 'f4').reshape(a.count, n).astype(float)
def add(arr, typ):
    global blob
    while len(blob) % 4: blob.append(0)
    o = len(blob); d = arr.astype('f4').tobytes(); blob += d
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o, byteLength=len(d)))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type=typ))
    return len(g.accessors) - 1
up = np.array([0.0, 1.0, 0.0])
def axis_rot(ax, ang):
    ax = ax / np.linalg.norm(ax); K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * K @ K
AX_LOCAL = None
if ROOT.endswith('UpperArm'):
    Wd = m.world(m.sample('Dead', 0.0)); Pd = Wd[m.parent[ix[ROOT]]][:3, :3]
    sh = Wd[ix[ROOT]][:3, 3]; hd = Wd[ix[ROOT.replace('UpperArm', 'Hand')]][:3, 3]
    AX_LOCAL = Pd.T @ (np.cross(hd - sh, up) / np.linalg.norm(np.cross(hd - sh, up)))
for an in g.animations:
    if an.name not in ('Death', 'Dead'): continue
    ch = next(c for c in an.channels if names[c.target.node] == ROOT and c.target.path == 'rotation')
    s = an.samplers[ch.sampler]; ts = read(s.input)[:, 0]; Q = read(s.output)
    out = Q.copy()
    for k, t in enumerate(ts):
        u = 1.0 if an.name == 'Dead' else np.clip((t - T0) / max(T1 - T0, 1e-6), 0, 1)
        w = u * u * (3 - 2 * u)
        if w <= 0: continue
        W = m.world(m.sample(an.name, float(t)))
        Pw = W[m.parent[ix[ROOT]]][:3, :3]
        L = quaternion_matrix(Q[k])[:3, :3]
        if ROOT.endswith('UpperArm') and os.environ.get('AXIS', 'key') == 'fixed':
            # one axis in the parent's frame, taken from the corpse pose (a per-key axis spun with the falling arm and
            # failed the jitter gate): across the arm, so +angle lifts the hand off the wing
            out[k] = matrix_quaternion(axis_rot(AX_LOCAL, np.radians(DEG) * w) @ L)
        elif ROOT.endswith('UpperArm'):      # axis across the arm at this key (lower jitter on the falling arm)
            sh = W[ix[ROOT]][:3, 3]; hd = W[ix[ROOT.replace('UpperArm', 'Hand')]][:3, 3]
            R = axis_rot(np.cross(hd - sh, up), np.radians(DEG) * w)
            out[k] = matrix_quaternion(Pw.T @ R @ Pw @ L)
        else:
            R = axis_rot(up, np.radians(DEG) * w)
            out[k] = matrix_quaternion(Pw.T @ R @ Pw @ L)
    for k in range(1, len(out)):
        if out[k] @ out[k - 1] < 0: out[k] *= -1
    s.output = add(out, 'VEC4')
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
print('ARM LAY', ROOT, DEG)
