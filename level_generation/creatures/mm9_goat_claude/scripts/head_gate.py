#!/usr/bin/env python3
"""Orientation gate, every role clip at 48 fps, ours against the MM9 source clip: landmark frames fixed in the bind pose
(independent of the weights). Head: skull joint -> muzzle tip (direction) and skull joint -> crown (up), for feet: ankle
joint -> toe vertices and ankle -> heel side. Each frame's rotation from bind is compared with MM9's (deg, full
orientation including roll). Also the head's fold (angle tip/crown against bind; a rigid head keeps 0) and the snout
direction angle alone. Usage: head_gate.py <mm9 glb> <our glb> [json]"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb_pose import Glb, Model
import rigcfg

BONES = {'head': rigcfg.SKULL, 'foot_fl': 'Xffoot01', 'foot_fr': 'Xffoot', 'foot_hl': 'Xbfoot01', 'foot_hr': 'Xbfoot'}


class M:
    def __init__(self, path):
        self.m = Model(Glb(path))
        N = self.m.glb.json['nodes']
        self.idx = {N[j]['name']: j for j in self.m.joints}
        ps = self.m.primitives
        self.W0 = self.m.world({})
        P = np.concatenate([q for q, _ in self.m.skinned_positions(self.W0)])
        J = np.concatenate([p['joints'] for p in ps]); W = np.concatenate([p['weights'] for p in ps])
        jn = np.array([N[j]['name'] for j in self.m.joints])
        self.dom = jn[J[np.arange(len(J)), W.argmax(1)]]
        self.lm = {}
        for k, b in BONES.items():
            o = self.W0[self.idx[b]][:3, 3]
            if k == 'head':   # glTF: +Z forward, +Y up
                reg = np.nonzero(np.isin(self.dom, list(rigcfg.HEAD_BONES)) & ~np.isin(self.dom, rigcfg.EAR_BONES))[0]
                tip = reg[np.argsort(-P[reg, 2])[:max(3, len(reg) // 40)]]
                crown = reg[np.argsort(-P[reg, 1])[:max(3, len(reg) // 40)]]
                skull = reg
            else:
                reg = np.nonzero(self.dom == b)[0]
                tip = reg[np.argsort(-P[reg, 2])[:max(3, len(reg) // 5)]]
                crown = reg[np.argsort(P[reg, 2])[:max(3, len(reg) // 5)]]
                skull = reg
            self.lm[k] = (skull, tip, crown)
        self.F0 = {k: self.frame(k, P) for k in BONES}

    def frame(self, k, P):
        s, t, c = self.lm[k]
        o = P[s].mean(0)
        a = P[t].mean(0) - o; a /= np.linalg.norm(a)
        u = P[c].mean(0) - o; u = u - (u @ a) * a; u /= np.linalg.norm(u)
        return np.stack([a, u, np.cross(a, u)], 1)

    def rot(self, k, clip, t):
        P = np.concatenate([q for q, _ in self.m.skinned_positions(self.m.world(self.m.sample(clip, t)))])
        F = self.frame(k, P)
        return F @ self.F0[k].T, P


def ang(R):
    return float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))))


mm, ours = M(sys.argv[1]), M(sys.argv[2])
_s, _a, _c = ours.lm['head']
_P = np.concatenate([q for q, _ in ours.m.skinned_positions(ours.W0)])
_o = _P[_s].mean(0)
_d1, _d2 = _P[_a].mean(0) - _o, _P[_c].mean(0) - _o
fold0 = np.degrees(np.arccos(np.clip(_d1 @ _d2 / np.linalg.norm(_d1) / np.linalg.norm(_d2), -1, 1)))
rep = {}
for role, (src, loop) in rigcfg.ROLES.items():
    T = ours.m.clip_times(role)[-1]
    Tm = mm.m.clip_times(src[0])[-1]
    row = {k: 0.0 for k in BONES}
    fold = 0.0
    for t in np.arange(0, T + 1e-6, 1 / 48):
        tm = min(t * Tm / T, Tm)
        for k in BONES:
            R0, _ = mm.rot(k, src[0], tm)
            R1, P1 = ours.rot(k, role, t)
            row[k] = max(row[k], ang(R1 @ R0.T))
            if k == 'head':
                s, a, c = ours.lm[k]
                o = P1[s].mean(0)
                d1, d2 = P1[a].mean(0) - o, P1[c].mean(0) - o
                now = np.degrees(np.arccos(np.clip(d1 @ d2 / np.linalg.norm(d1) / np.linalg.norm(d2), -1, 1)))
                fold = max(fold, abs(now - fold0))
    row['head_fold'] = fold
    rep[role] = {k: round(v, 1) for k, v in row.items()}
    print(role, rep[role])
if len(sys.argv) > 3:
    json.dump(rep, open(sys.argv[3], 'w'), indent=1)
