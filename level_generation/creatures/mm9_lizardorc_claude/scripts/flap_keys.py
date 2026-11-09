#!/usr/bin/env python3
"""Keys of XFlap: the front flap hinges at the belt and keeps in front of the leading thigh: per key the forward angle of each thigh in the spine's frame relative to the bind; the hinge takes the larger (never behind the bind), low-passed. Args: <in glb> <out glb>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
from pygltflib import GLTF2, Accessor, BufferView, AnimationSampler, AnimationChannel, AnimationChannelTarget
from scipy.ndimage import gaussian_filter1d
IN, OUT = sys.argv[1:3]
m = Model(Glb(IN)); doc = m.glb.json; names = [n.get('name') for n in doc['nodes']]; ix = {n: i for i, n in enumerate(names)}
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
def add(arr, typ):
    global blob
    while len(blob) % 4: blob.append(0)
    o = len(blob); d = arr.astype('f4').tobytes(); blob += d
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o, byteLength=len(d)))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type=typ))
    return len(g.accessors) - 1
jn = [names[j] for j in m.joints]; ibm = {n: m.inverse_binds[i] for i, n in enumerate(jn)}
Bs = np.linalg.inv(ibm['Bip01 Spine'])
def ang(v): return np.arctan2(v[2], -v[1])
bind = {s: np.linalg.inv(ibm[f'Bip01 {s} Calf'])[:3, 3] - np.linalg.inv(ibm[f'Bip01 {s} Thigh'])[:3, 3] for s in 'LR'}
r0 = {s: ang(bind[s]) for s in 'LR'}
axis_local = Bs[:3, :3].T @ np.array([1., 0, 0]); axis_local /= np.linalg.norm(axis_local)
import os
KF, KR, CL = float(os.environ.get('KF', 1.0)), float(os.environ.get('KR', -1.0)), float(os.environ.get('CL', 100))
fwd_local = Bs[:3, :3].T @ np.array([0, 0, 1.]); fwd_local /= np.linalg.norm(fwd_local)
T0 = list(np.array(doc['nodes'][ix['XFlap']]['translation'], float))
tops = {}
for an in g.animations:
    an.channels = [c for c in an.channels if names[c.target.node] != 'XFlap']
    ch0 = next(c for c in an.channels if names[c.target.node] == 'Bip01 Spine')
    tin = an.samplers[ch0.sampler].input
    a = g.accessors[tin]; bv = g.bufferViews[a.bufferView]; ts = np.frombuffer(bytes(blob[(bv.byteOffset or 0) + (a.byteOffset or 0):(bv.byteOffset or 0) + (a.byteOffset or 0) + 4 * a.count]), 'f4').copy()
    A = np.zeros(len(ts)); Bb = np.zeros(len(ts))
    for k, t in enumerate(ts):
        W = m.world(m.sample(an.name, float(t)))
        Rs = (W[ix['Bip01 Spine']] @ ibm['Bip01 Spine'])[:3, :3]      # spine's skin rotation
        vals = []
        for s in 'LR':
            v = Rs.T @ (W[ix[f'Bip01 {s} Calf']][:3, 3] - W[ix[f'Bip01 {s} Thigh']][:3, 3]); vals.append(ang(v) - r0[s])
        A[k] = max(max(vals), 0); Bb[k] = vals[0] - vals[1]
    if an.name == 'Dead': pass
    A = gaussian_filter1d(A, 1.2, mode='nearest') * KF
    A = np.clip(A, 0, np.radians(CL)); Bb = gaussian_filter1d(Bb, 1.2, mode='nearest') * KR; Bb = np.clip(Bb, -np.radians(30), np.radians(30))
    def qa(ax, a): return np.c_[ax[None] * np.sin(a / 2)[:, None], np.cos(a / 2)]
    def qm(p, q):
        x1, y1, z1, w1 = p.T; x2, y2, z2, w2 = q.T
        return np.c_[w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2]
    Q = qm(qa(fwd_local, Bb), qa(axis_local, -A))       # forward about -x, then swung off the leading thigh about the body's forward axis
    s2 = len(an.samplers); an.samplers.append(AnimationSampler(input=tin, output=add(Q, 'VEC4'), interpolation='LINEAR'))
    s1 = len(an.samplers); an.samplers.append(AnimationSampler(input=tin, output=add(np.tile(T0, (len(ts), 1)), 'VEC3'), interpolation='LINEAR'))
    an.channels.append(AnimationChannel(sampler=s2, target=AnimationChannelTarget(node=ix['XFlap'], path='rotation')))
    an.channels.append(AnimationChannel(sampler=s1, target=AnimationChannelTarget(node=ix['XFlap'], path='translation')))
    tops[an.name] = round(float(np.degrees(A.max())), 1)
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
print('FLAP deg', tops)
