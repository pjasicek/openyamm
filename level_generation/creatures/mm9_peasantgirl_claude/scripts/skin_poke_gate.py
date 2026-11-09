#!/usr/bin/env python3
"""Skin-through-cover gate for PeasantF5 (after PeasantM7's sleeve_poke_gate.py, user review 2026-11-01 "hands sticking through
the sleeves"). Two covers on this body:
  stub:   the grafted MPFB hand's forearm stub (hand vertices behind the wrist) must stay inside the bare forearm + bracelet;
  sleeve: the bare arm's top (arm vertices that start inside the puffed sleeve) must stay inside the sleeve.
Parts come from matching the GLB's rest vertices to work/uv_tex2.npz (the frozen mesh). Every clip at 48 fps, per candidate: a ray
from the posed bone axis (Forearm->Hand, or UpperArm->Forearm), perpendicular to it, through the vertex; the vertex must lie nearer the
axis than the outermost cover wall along that ray (vertex radius - wall radius > TOL is skin through the cover); no hit is skipped.
Usage: skin_poke_gate.py <glb> <out json> [--fps 48] [--tol 0.0005] [--mirrored]"""
import argparse, json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
ap = argparse.ArgumentParser(); ap.add_argument('glb'); ap.add_argument('out')
ap.add_argument('--fps', type=float, default=48.0); ap.add_argument('--tol', type=float, default=0.0005); ap.add_argument('--mirrored', action='store_true')
o = ap.parse_args()
glb = Glb(Path(o.glb)); model = Model(glb); doc = glb.json
names = [n.get('name') for n in doc['nodes']]; idx = {n: i for i, n in enumerate(names)}
P = model.primitives; node0 = P[0]['node']
USE = [k for k, pr in enumerate(P) if pr['node'] == node0 and pr['skinned']]
off, T = 0, []
for k in USE: T.append(P[k]['triangles'] + off); off += len(P[k]['positions'])
tris = np.concatenate(T)
def posed(clip, t):
    w = model.world(model.sample(clip, float(t)) if clip else {})
    sp = model.skinned_positions(w); return w, np.concatenate([sp[k][0] for k in USE])
rw, rest = posed(None, 0)
D = np.load(HERE / 'work/uv_tex2.npz'); co = D['co']; comp = D['comp']; pn = [str(x) for x in D['names']]
g = np.c_[co[:, 0] * (-1 if o.mirrored else 1), co[:, 2], -co[:, 1]]
g = g + (0.5 * (rest.min(0) + rest.max(0)) - 0.5 * (g.min(0) + g.max(0)))     # translation from the bounding boxes
d, nn = cKDTree(g).query(rest); part = comp[nn]
print('match max mm', round(float(d.max()) * 1000, 2), 'p99', round(float(np.percentile(d, 99)) * 1000, 2))
lab = {n: part == pn.index(n) for n in pn}
ftri = lambda m: np.where(m[tris].sum(1) >= 2)[0]
SIDES = {}
for tok in ('L', 'R'):
    sg = None
    for test, (j0, j1), cand_part, cover_parts in (('stub', ('Forearm', 'Hand'), 'hands', ('arms', 'bracelets')),
                                                    ('sleeve', ('UpperArm', 'Forearm'), 'arms', ('dress',))):
        a0, a1 = rw[idx[f'FHP {tok} {j0}']][:3, 3], rw[idx[f'FHP {tok} {j1}']][:3, 3]; L_ = np.linalg.norm(a1 - a0); ax = (a1 - a0) / L_
        tt = (rest - a0) @ ax; side = np.sign(rest[:, 0]) == np.sign(a1[0])
        cov_m = np.zeros(len(rest), bool)
        for c in cover_parts: cov_m |= lab[c]
        cov_m &= side; cf = ftri(cov_m)
        if test == 'stub': cand = np.where(lab[cand_part] & side & (tt < L_ - 0.002) & (tt > L_ - 0.06))[0]
        else: cand = np.where(lab[cand_part] & side & (tt < 0.22))[0]
        SIDES[(tok, test)] = dict(cand=cand, cf=cf, j0=idx[f'FHP {tok} {j0}'], j1=idx[f'FHP {tok} {j1}'])
def poke(W, X, s):
    a0, a1 = W[s['j0']][:3, 3], W[s['j1']][:3, 3]; ax = (a1 - a0) / np.linalg.norm(a1 - a0)
    v = X[s['cand']]; tt = (v - a0) @ ax; p0 = a0 + tt[:, None] * ax
    r = v - p0; rv = np.linalg.norm(r, axis=1); rd = r / np.maximum(rv, 1e-9)[:, None]
    Tq = X[tris[s['cf']]]; A, B, C = Tq[:, 0], Tq[:, 1], Tq[:, 2]; e1, e2 = B - A, C - A
    out = np.full(len(v), np.nan)
    for i in range(len(v)):
        pv = np.cross(rd[i], e2); det = np.einsum('ij,ij->i', e1, pv); ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1 / np.where(ok, det, 1), 0); tv = p0[i] - A
        uu = np.einsum('ij,ij->i', tv, pv) * inv; qv = np.cross(tv, e1); vv = (qv @ rd[i]) * inv; dist = np.einsum('ij,ij->i', e2, qv) * inv
        hit = ok & (uu >= 0) & (vv >= 0) & (uu + vv <= 1) & (dist > 0) & (dist < 0.12)
        if hit.any(): out[i] = rv[i] - dist[hit].max()
    return out
# keep only candidates that are covered at rest (inside, with a hit), so the gate tests what the cover hides
for k, s in SIDES.items():
    sd = poke(rw, rest, s); keep = ~np.isnan(sd) & (sd < 0)
    s['rest_uncovered'] = int((~keep).sum()); s['cand'] = s['cand'][keep]
rep = {'sides': {f'{a}_{b}': {'candidates': int(len(s['cand'])), 'dropped_uncovered_at_rest': s['rest_uncovered']} for (a, b), s in SIDES.items()}, 'clips': {}}
print('SIDES', json.dumps(rep['sides']))
worst = 0.0
for clip in model.clips:
    dur = max(model.clip_times(clip)); times = np.arange(0, dur + 1e-6, 1 / o.fps) if dur > 0 else [0.0]
    e = {f'{a}_{b}': {'worst_mm': 0.0, 'frame': 0, 'frames': 0} for (a, b) in SIDES}
    for k, tm in enumerate(times):
        W, X = posed(clip, tm)
        for (a, b), s in SIDES.items():
            if not len(s['cand']): continue
            m = float(np.nan_to_num(poke(W, X, s), nan=-1.0).max()); q = e[f'{a}_{b}']
            if m > o.tol: q['frames'] += 1
            if m * 1000 > q['worst_mm']: q.update(worst_mm=round(m * 1000, 1), frame=k)
    rep['clips'][clip] = e; worst = max(worst, max(v['worst_mm'] for v in e.values()))
    print(f"{clip:10s} " + ' | '.join(f"{k}: {v['worst_mm']:.1f}mm@{v['frame']} ({v['frames']}f)" for k, v in e.items()), flush=True)
print('SKIN_POKE worst mm', worst)
json.dump(rep, open(o.out, 'w'), indent=1)
