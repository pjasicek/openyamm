#!/usr/bin/env python3
"""(MM6 PeasantF1 rebuild: env CLIPS limits it to the listed clips.) A constant small abduction of an upper arm in every clip (MM9's stand hangs one hand where our wider hips are): same local offset on every key, in the clavicle's MM9 frame, so nothing new moves. Args: <in> <out> <side:deg> ... (raw ABC sides: R at +x)"""
import sys
from pathlib import Path
import numpy as np
from pygltflib import GLTF2
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
IN, OUT = sys.argv[1:3]
src = Model(Glb(HERE / 'source/mm9/pf1b.glb')); sn = [n.get('name') for n in src.glb.json['nodes']]; w0 = src.world({})
g = GLTF2().load(IN); blob = bytearray(g.binary_blob()); names = [n.name for n in g.nodes]
def qmul(p, q):
    x1, y1, z1, w1 = p.T; x2, y2, z2, w2 = q.T
    return np.c_[w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2]
par = {}
for i, nd in enumerate(src.glb.json['nodes']):
    for c in nd.get('children', []): par[sn[c]] = sn[i]
for spec in sys.argv[3:]:
    # <side>:<deg> turns the upper arm (positive = out); <side>F:<deg> turns the forearm at the elbow (follow-up 2, 2026-11-12: elbow in,
    # hand kept); the upper arm about the frontal axis in the parent's MM9 rest frame, the forearm as below
    s, deg = spec.split(':'); bone = 'Forearm' if s.endswith('F') else 'UpperArm'; s = s[0]
    sign = 1 if s == 'R' else -1; a = np.radians(float(deg)) * sign
    idx = names.index(f'FHP {s} {bone}'); Rc = w0[sn.index(par[f'FHP {s} {bone}'])][:3, :3]
    ax = Rc.T @ np.array([0, 0, 1.0]); q = np.r_[ax * np.sin(a / 2), np.cos(a / 2)]
    n = 0
    only = [x for x in __import__('os').environ.get('CLIPS', '').split(',') if x]
    # forearm: by default the frontal-axis turn in the parent (upper arm) frame, a fixed carrying angle, so a bent elbow keeps the gesture's
    # shape with the hands a little wider. FOREARM_FRAME=own: the same turn at Standing's first key but post-multiplied in the forearm's own
    # frame (world angular velocity unchanged); tried 2026-11-12 and rejected: with the elbow bent it pulls the hands to the midline
    # (Attack's raised hands dropped to the belt)
    def keys(an, c):
        x = g.accessors[an.samplers[c.sampler].output]; v = g.bufferViews[x.bufferView]; o = (v.byteOffset or 0) + (x.byteOffset or 0)
        return o, np.frombuffer(blob, 'f4', x.count * 4, o).reshape(x.count, 4).copy()
    own = bone == 'Forearm' and __import__('os').environ.get('FOREARM_FRAME', 'parent') == 'own'
    if own:
        an = next(an for an in g.animations if an.name == 'Standing')
        c = next(c for c in an.channels if c.target.node == idx and c.target.path == 'rotation'); r = keys(an, c)[1][0]; r = r / np.linalg.norm(r)
        rc = np.r_[-r[:3], r[3]]                                    # local axis = R(ref)^T ax
        axl = qmul(qmul(rc[None], np.r_[ax, 0][None]), r[None])[0, :3]; q = np.r_[axl * np.sin(a / 2), np.cos(a / 2)]
    for an in g.animations:
        if only and an.name not in only: continue
        for c in an.channels:
            if c.target.node == idx and c.target.path == 'rotation':
                o, Q = keys(an, c)
                Qn = qmul(Q, np.tile(q, (len(Q), 1))) if own else qmul(np.tile(q, (len(Q), 1)), Q)
                blob[o:o + Qn.size * 4] = Qn.astype('f4').tobytes(); n += 1
    print('ARMOUT', s, bone, deg, n)
g.set_binary_blob(bytes(blob)); g.save(OUT)
