#!/usr/bin/env python3
"""Orientation gate, every clip at 48 fps, ours (delivered GLB) against MM9's source clip at the same time:
head direction (mid-eye -> bill/snout tip; MM9's eye from the skin's eye texels) and the sole normal per foot (the
foot's lowest vertices in the bind). Both heads are rigid and mirror-symmetric on the same bones, so roll follows.
Usage: orient_gate.py <mm9 glb> <our glb> <config.json> [report.json]
config: {"roles": {role: mm9 clip}, "tip": bone, "head": [bones], "feet": {name: [bones]}}"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model


def ang(a, b):
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    return float(np.degrees(np.arccos(np.clip(a @ b, -1, 1))))


class M:
    def __init__(self, path, cfg, mm9=False):
        self.m = Model(Glb(path))
        N = self.m.glb.json['nodes']
        jn = [N[j]['name'] for j in self.m.joints]
        self.pi = int(np.argmax([len(q['weights']) for q in self.m.primitives]))
        p = self.m.primitives[self.pi]
        self.d = {}
        W = p['weights']; J = p['joints']
        n = len(W)
        wsum = lambda names: sum((W * np.isin(np.array(jn)[J], names)).sum(1) for _ in [0])
        P0 = self.pose(None)
        self.head = np.nonzero(wsum(cfg['head']) > 0.6)[0]
        fw = P0[self.head] @ np.array([0, 0, 1.0])
        self.tip = self.head[np.argsort(-fw)[:3]]
        tris = np.asarray(self.m.skinned_positions(self.m.world({}))[self.pi][1]).reshape(-1, 3)
        self.eye = None
        uv = p.get('uv') if isinstance(p, dict) else None
        if mm9:
            prim = self.m.glb.json['meshes'][self.mi(cfg)]['primitives'][0]
            uv = self.m.glb.accessor(prim['attributes']['TEXCOORD_0'])
            e = np.array(cfg['eye_uv']) / cfg['skin_size']
            hits = []
            for t in tris:
                a_, b_, c_ = uv[t]
                M_ = np.array([b_ - a_, c_ - a_]).T
                if abs(np.linalg.det(M_)) < 1e-10:
                    continue
                l = np.linalg.solve(M_, e - a_)
                if l.min() >= -1e-3 and l.sum() <= 1 + 1e-3:
                    hits.append((t, (1 - l.sum(), l[0], l[1])))
            self.eye = hits
        else:
            # our eyes: the two smallest welded components near the head
            parent = np.arange(len(P0))

            def find(x):
                while parent[x] != x:
                    parent[x] = parent[parent[x]]; x = parent[x]
                return x
            key = {}
            for i, q in enumerate(np.round(P0, 6)):
                k = tuple(q)
                if k in key:
                    parent[find(i)] = find(key[k])
                else:
                    key[k] = i
            for t in tris:
                a_, b_, c_ = find(t[0]), find(t[1]), find(t[2])
                parent[b_] = a_; parent[find(c_)] = a_
            roots = np.array([find(i) for i in range(len(P0))])
            ids, cnt = np.unique(roots, return_counts=True)
            self.eyev = np.nonzero(np.isin(roots, ids[cnt < 400]))[0]
        floor = cfg.get('sole_height', 0.03)
        self.feet = {}
        for k, v in cfg['feet'].items():
            ids_ = np.nonzero(wsum(v) > 0.3)[0]
            self.feet[k] = ids_[P0[ids_, 1] < P0[ids_, 1].min() + floor]

    def mi(self, cfg):
        for i, me in enumerate(self.m.glb.json['meshes']):
            if len(me['primitives'][0]['attributes']) and self.m.glb.accessor(me['primitives'][0]['attributes']['POSITION']).shape[0] == len(self.m.primitives[self.pi]['weights']):
                return i
        return 0

    def pose(self, clip_t):
        wd = self.m.world({}) if clip_t is None else self.m.world(self.m.sample(*clip_t))
        pos, _ = self.m.skinned_positions(wd)[self.pi]
        return pos

    def frame(self, P):
        if self.eye is not None:
            c = np.mean([sum(w * P[i] for i, w in zip(t, l)) for t, l in self.eye], 0)
        else:
            c = P[self.eyev].mean(0)
        return P[self.tip].mean(0) - c, None

    def sole(self, P, k):
        X = P[self.feet[k]]
        n = np.linalg.svd(X - X.mean(0))[2][2]
        return n


mm9path, ours, cfgp = sys.argv[1:4]
cfg = json.load(open(cfgp))
A, B = M(mm9path, cfg, True), M(ours, cfg)
out = {}
for role, clip in cfg['roles'].items():
    ta, tb = A.m.clip_times(clip), B.m.clip_times(role)
    T = min(ta[-1], tb[-1])
    rep = {'dir': 0.0, 'feet': {k: 0.0 for k in cfg['feet']}, 'head_turn_mm9': 0.0}
    d0a, _ = A.frame(A.pose((clip, ta[0])))
    for t in np.arange(0, T + 1e-6, 1 / 48):
        Pa, Pb = A.pose((clip, ta[0] + t)), B.pose((role, tb[0] + t))
        da, _ = A.frame(Pa); db, _ = B.frame(Pb)
        rep['dir'] = max(rep['dir'], ang(da, db))
        rep['head_turn_mm9'] = max(rep['head_turn_mm9'], ang(da, d0a))
        for k in cfg['feet']:
            na, nb = A.sole(Pa, k), B.sole(Pb, k)
            rep['feet'][k] = max(rep['feet'][k], min(ang(na, nb), ang(na, -nb)))
    rep = {k: (round(v, 1) if not isinstance(v, dict) else {a: round(b, 1) for a, b in v.items()}) for k, v in rep.items()}
    out[role] = rep
    print(role, rep)
if len(sys.argv) > 4:
    json.dump(out, open(sys.argv[4], 'w'), indent=1)
