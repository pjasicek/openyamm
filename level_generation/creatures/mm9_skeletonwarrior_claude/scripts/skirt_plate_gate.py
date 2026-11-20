#!/usr/bin/env python3
"""Plates, new build against the approved one, per clip at 48 fps: hem-tip acceleration (mm/f2, p95 and max over groups, flap and
tick), direction reversals of the tip's speed along its main axis (a flap reverses more often than the leg), plate separation (rest
neighbours within 3 cm between groups: worst single-point opening, cm), lowest plate point. Args: <new glb> <approved glb> <out json>"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
GR = json.load(open(HERE / 'work' / 'skirt_groups.json'))
D = np.load(HERE / 'work' / 'skirt_dump.npz'); LIFT = 1.0588
tgt = np.c_[D['co'][:, 0], D['co'][:, 2] + LIFT, -D['co'][:, 1]]; tree = cKDTree(tgt)
res = {}


def load(p):
    m = Model(Glb(p)); r = m.skinned_positions(m.world({}))[0][0]; pid = D['pid'][tree.query(r)[1]]
    idx = {g: np.where(np.isin(pid, b['pids']))[0] for g, b in GR.items()}
    pairs = []
    gs = list(idx)
    for i, a in enumerate(gs):
        for b in gs[i + 1:]:
            dist, j = cKDTree(r[idx[b]]).query(r[idx[a]])
            ok = dist < 0.03
            if ok.sum() >= 3: pairs.append((a, b, idx[a][ok], idx[b][j[ok]], dist[ok]))
    return m, idx, pairs


def run(p, clips):
    m, idx, pairs = load(p); out = {}
    for c in clips:
        T = np.arange(0, m.clip_times(c)[-1] + 1e-6, 1 / 48)
        X = [m.skinned_positions(m.world(m.sample(c, float(t))))[0][0] for t in T]
        tips = {g: np.array([x[v[np.argmin(m.skinned_positions(m.world({}))[0][0][v, 1])]] for x in X]) for g, v in idx.items()} if False else None
        r0 = m.skinned_positions(m.world({}))[0][0]
        acc, rev = [], []
        for g, v in idx.items():
            tip = v[np.argmin(r0[v, 1])]; P = np.array([x[tip] for x in X])
            if len(P) > 3:
                a = np.linalg.norm(np.diff(P, 2, axis=0), axis=1) * 1000; acc.append(a)
                u = np.linalg.svd(P - P.mean(0), full_matrices=False)[2][0]; sp = np.diff(P @ u)
                sp = sp[np.abs(sp) > 0.0015]; rev.append(int((np.sign(sp[1:]) != np.sign(sp[:-1])).sum()))
        gap = 0.0; worst = ''
        for a, b, i, j, d0 in pairs:
            for x in X[:: 2]:
                o = float((np.linalg.norm(x[i] - x[j], axis=1) - d0).max())
                if o > gap: gap, worst = o, f'{a}-{b}'
        A = np.concatenate(acc) if acc else np.zeros(1)
        low = min(float(x[np.concatenate(list(idx.values())), 1].min()) for x in X)
        out[c] = dict(acc_p95=round(float(np.percentile(A, 95)), 1), acc_max=round(float(A.max()), 1), reversals=max(rev) if rev else 0,
                      opening_cm=round(gap * 100, 1), pair=worst, lowest_cm=round(low * 100, 1))
    return out


clips = sys.argv[4].split(',') if len(sys.argv) > 4 else ['Walking', 'Running', 'Fidget', 'AttackMelee', 'AttackMelee2', 'AttackRanged', 'Hit', 'Taunt', 'Death']
new, old = run(sys.argv[1], clips), run(sys.argv[2], clips)
for c in clips:
    print(f'{c:13s} new {new[c]}   approved {old[c]}')
json.dump(dict(new=new, approved=old), open(sys.argv[3], 'w'), indent=1)
