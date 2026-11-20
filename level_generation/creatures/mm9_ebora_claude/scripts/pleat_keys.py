#!/usr/bin/env python3
"""Keys of the wing pleat helpers XPleat{A,B}{1,2,3} (one per membrane panel; build_wings.py blends a tent of membrane
weight into them). MM9's clips close the wing fan at the wrist (Standing: arm to third finger 46.8 -> 6.5 deg), which
flattens the membrane between the spars. Per key, each panel's mid-line (the bisector of its two spars seen from the wrist)
is turned out of the spars' plane by phi, cos(phi) = cos(theta0 / 2) / cos(theta / 2) (theta0 rest opening, theta posed),
so each half of the panel keeps its rest opening: a pleat instead of a squashed sheet. The side is the one away from the
spine. A panel opened wider than at rest gets phi = 0. Args: <in glb> <out glb>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, matrix_quaternion
from pygltflib import GLTF2, Accessor, BufferView, AnimationSampler, AnimationChannel, AnimationChannelTarget
IN, OUT = sys.argv[1:3]
import os
PANEL_SCALE = [float(x) for x in os.environ.get('PLEAT_SCALE', '0.6,0.6,0.2').split(',')]   # per panel (lead|f2, f2|f3, f3|arm); 1.0 keeps each half's rest opening: the full and half pleat made the inner panel stand out like a sail when folded
m = Model(Glb(IN)); doc = m.glb.json; names = [n.get('name') for n in doc['nodes']]; ix = {n: i for i, n in enumerate(names)}
SIDES = {'A': dict(wrist='Bone50', panels=[('Bone55', 'Bone63'), ('Bone63', 'Bone59'), ('Bone59', 'Bone49')]),
         'B': dict(wrist='Bone15', panels=[('Bone20', 'Bone11'), ('Bone11', 'Bone27'), ('Bone27', 'Bone14')])}
def unit(v): return v / max(np.linalg.norm(v), 1e-12)
W0 = m.world({})
def frame(x, n):
    x = unit(x); n = unit(n - (n @ x) * x); return np.c_[x, n, np.cross(x, n)]
rest = {}
for a, sd in SIDES.items():
    w0 = W0[ix[sd['wrist']]]
    for k, (p1, p2) in enumerate(sd['panels'], 1):
        d1 = W0[ix[p1]][:3, 3] - w0[:3, 3]; d2 = W0[ix[p2]][:3, 3] - w0[:3, 3]
        n0 = unit(np.cross(d1, d2)); th0 = np.arccos(np.clip(unit(d1) @ unit(d2), -1, 1))
        rest[(a, k)] = dict(d1=d1, d2=d2, n_local=w0[:3, :3].T @ n0, th0=th0, F0=frame(unit(d1) + unit(d2), n0))
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
def add(arr, typ):
    global blob
    while len(blob) % 4: blob.append(0)
    o = len(blob); d = arr.astype('f4').tobytes(); blob += d
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o, byteLength=len(d)))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type=typ))
    return len(g.accessors) - 1
maxphi = {}
for an in g.animations:
    ch = next(c for c in an.channels if names[c.target.node] == 'Bip01 Pelvis')
    tin = an.samplers[ch.sampler].input
    a_ = g.accessors[tin]; bv = g.bufferViews[a_.bufferView]; off = (bv.byteOffset or 0) + (a_.byteOffset or 0)
    ts = np.frombuffer(bytes(blob[off:off + 4 * a_.count]), 'f4').copy()
    Ws = [m.world(m.sample(an.name, float(t))) for t in ts]
    pn = {f'XPleat{a}{k}' for a in 'AB' for k in (1, 2, 3)}
    an.channels = [c for c in an.channels if names[c.target.node] not in pn]
    for a, sd in SIDES.items():
        for k, (p1, p2) in enumerate(sd['panels'], 1):
            R0 = rest[(a, k)]; node = f'XPleat{a}{k}'
            T = np.zeros((len(ts), 3)); Q = np.zeros((len(ts), 4)); ph = []
            for i, Wt in enumerate(Ws):
                wm = Wt[ix[sd['wrist']]]; wp = wm[:3, 3]
                d1 = Wt[ix[p1]][:3, 3] - wp; d2 = Wt[ix[p2]][:3, 3] - wp
                th = np.arccos(np.clip(unit(d1) @ unit(d2), -1, 1))
                nref = wm[:3, :3] @ R0['n_local']; n = unit(np.cross(d1, d2))
                if n @ nref < 0 or np.linalg.norm(np.cross(d1, d2)) < 1e-6: n = unit(nref)
                b = unit(unit(d1) + unit(d2))
                n = unit(n - (n @ b) * b)
                c = np.clip(np.cos(R0['th0'] / 2) / max(np.cos(th / 2), 1e-6), -1, 1)
                phi = np.arccos(c) if np.cos(R0['th0'] / 2) < np.cos(th / 2) else 0.0
                spine = Wt[ix['Bip01 Spine2']][:3, 3]
                # lying or near the ground: fade the pleat out (the corpse's wings lie flat), never push into the floor
                lift = np.clip((wp[1] - 0.05) / 0.25, 0, 1); phi = PANEL_SCALE[k - 1] * phi * (0.6 + 0.4 * lift * lift * (3 - 2 * lift))
                cand = [np.cos(phi) * b + s_ * np.sin(phi) * n for s_ in (1, -1)]
                arms = [Wt[ix[j]][:3, 3] for j in ('Bip01 L Forearm', 'Bip01 L Hand', 'Bip01 R Forearm', 'Bip01 R Hand')]
                def armgap(v):      # the bulge stays clear of a forearm or hand lying over the wing (corpse, fall)
                    pts = [wp + r * v for r in (0.3, 0.6, 0.9)]
                    return min(np.linalg.norm(q - a_) for q in pts for a_ in arms)
                M = max(cand, key=lambda v: np.linalg.norm(wp + 0.5 * v - spine) - 10 * max(0.0, 0.02 - (wp + 0.9 * v)[1])
                        + 4 * min(armgap(v), 0.35))
                sgn = 1 if np.allclose(M, cand[0]) else -1
                F = frame(M, n * np.cos(phi) - sgn * np.sin(phi) * b)
                F0 = R0['F0']
                Rw = F @ F0.T @ W0[ix[node]][:3, :3]
                Wn = np.eye(4); Wn[:3, :3] = Rw; Wn[:3, 3] = wp
                L = np.linalg.inv(wm) @ Wn
                T[i] = L[:3, 3]; Q[i] = matrix_quaternion(L[:3, :3]); ph.append(np.degrees(phi))
            for i in range(1, len(Q)):
                if Q[i] @ Q[i - 1] < 0: Q[i] *= -1
            maxphi[(an.name, node)] = round(max(ph), 1)
            s1 = len(an.samplers); an.samplers.append(AnimationSampler(input=tin, output=add(T, 'VEC3'), interpolation='LINEAR'))
            s2 = len(an.samplers); an.samplers.append(AnimationSampler(input=tin, output=add(Q, 'VEC4'), interpolation='LINEAR'))
            an.channels.append(AnimationChannel(sampler=s1, target=AnimationChannelTarget(node=ix[node], path='translation')))
            an.channels.append(AnimationChannel(sampler=s2, target=AnimationChannelTarget(node=ix[node], path='rotation')))
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
print('PLEAT', {c: max(v for (cc, _), v in maxphi.items() if cc == c) for c in sorted({c for c, _ in maxphi})})
