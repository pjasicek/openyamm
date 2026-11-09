#!/usr/bin/env python3
"""Orientation gate (crow lesson): head and hooves of our GLB against MM9's own mesh, every clip at 48 fps.

For each region (skull = vertices dominated by Xheadpiv/Xhead, jaw = Xjawpiv, each hoof = its foot joint) the rigid
rotation from the bind pose to the posed vertices is solved (Kabsch) on ours and on MM9's mesh at the same clip time.
Reported per clip (max over frames, degrees): full rotation difference, the up vector (+Z) difference and the snout
direction (-Y) difference for the skull; full difference and sole normal (-Z) difference for the hooves. Also the
skull's own fold (rotation spread between its front and back halves; a rigid head keeps 0).

Usage: orient_gate.py <our glb> <mm9 glb> [report.json]
"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model

ROLE_SRC = {'Standing': 'stand', 'Walking': 'walk', 'Running': 'run', 'Fidget': 'fidget1', 'AttackMelee': 'Hattack1',
            'Hit': 'wince1', 'Death': 'die1'}
REGIONS = {'skull': ['Xheadpiv', 'Xhead'], 'jaw': ['Xjawpiv'], 'hoof_fl': ['Xffoot01'], 'hoof_fr': ['Xffoot'],
           'hoof_hl': ['Xbfoot01'], 'hoof_hr': ['Xbfoot']}


def dominant(model):
    names = [model.glb.json['nodes'][j].get('name') for j in model.joints]
    out = []
    for prim in model.primitives:
        if not prim['skinned']:
            out.append(np.array([None] * len(prim['positions'])))
            continue
        k = prim['joints'][np.arange(len(prim['joints'])), prim['weights'].argmax(1)]
        w = prim['weights'].max(1)
        lab = np.array([names[i] for i in k], dtype=object)
        lab[w < 0.6] = None          # blended border vertices are not part of a rigid region
        out.append(lab)
    return out


def region_points(posed, labels, bones):
    return np.concatenate([p[np.isin(l, bones)] for (p, _), l in zip(posed, labels)])


def kabsch(a, b):
    a0, b0 = a - a.mean(0), b - b.mean(0)
    u, _, vt = np.linalg.svd(a0.T @ b0)
    d = np.sign(np.linalg.det(vt.T @ u.T))
    return vt.T @ np.diag([1, 1, d]) @ u.T


def ang(r):
    return float(np.degrees(np.arccos(np.clip((np.trace(r) - 1) / 2, -1, 1))))


def vang(a, b):
    return float(np.degrees(np.arccos(np.clip(a @ b / np.linalg.norm(a) / np.linalg.norm(b), -1, 1))))


ours, mm9 = Model(Glb(sys.argv[1])), Model(Glb(sys.argv[2]))
lo, lm = dominant(ours), dominant(mm9)
bind_o = ours.skinned_positions(ours.world({}))
bind_m = mm9.skinned_positions(mm9.world({}))
B_o = {r: region_points(bind_o, lo, b) for r, b in REGIONS.items()}
B_m = {r: region_points(bind_m, lm, b) for r, b in REGIONS.items()}
counts = {r: [len(B_o[r]), len(B_m[r])] for r in REGIONS}
# skull halves (front / back along -Y) for the fold measure
sk = B_o['skull']
front = sk[:, 1] < np.median(sk[:, 1])
report = {'_vertices_ours_mm9': counts}
for role, src in ROLE_SRC.items():
    if role not in ours.clips or src not in mm9.clips:
        continue
    t1 = ours.clip_times(role)[-1]
    res = {}
    grid = mm9.clip_times(src) if '--keys' in sys.argv else np.arange(0, t1 + 1e-6, 1 / 48)
    for t in [x for x in grid if x <= t1 + 1e-6]:
        po = ours.skinned_positions(ours.world(ours.sample(role, t)))
        pm = mm9.skinned_positions(mm9.world(mm9.sample(src, t)))
        for r, bones in REGIONS.items():
            if len(B_o[r]) < 4 or len(B_m[r]) < 4:
                continue
            ro = kabsch(B_o[r], region_points(po, lo, bones))
            rm = kabsch(B_m[r], region_points(pm, lm, bones))
            d = res.setdefault(r, {'full': 0, 'up': 0, 'dir': 0, 'at': 0})
            full = ang(ro @ rm.T)
            if r == 'skull':
                up, dr = vang(ro @ [0, 0, 1], rm @ [0, 0, 1]), vang(ro @ [0, -1, 0], rm @ [0, -1, 0])
                pts = region_points(po, lo, bones)
                fold = ang(kabsch(sk[front], pts[front]) @ kabsch(sk[~front], pts[~front]).T)
                d['fold'] = max(d.get('fold', 0), fold)
            elif r.startswith('hoof'):
                up, dr = vang(ro @ [0, 0, -1], rm @ [0, 0, -1]), 0.0
            else:
                up, dr = vang(ro @ [0, 0, 1], rm @ [0, 0, 1]), 0.0
            if full > d['full']:
                d['at'] = round(float(t), 3)
            d['full'], d['up'], d['dir'] = max(d['full'], full), max(d['up'], up), max(d['dir'], dr)
    report[role] = {r: {k: round(v, 1) for k, v in d.items()} for r, d in res.items()}
    print(role, report[role])
if len(sys.argv) > 3 and not sys.argv[3].startswith('--'):
    json.dump(report, open(sys.argv[3], 'w'), indent=1)
