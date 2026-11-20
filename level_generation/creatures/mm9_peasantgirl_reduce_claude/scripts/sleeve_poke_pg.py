#!/usr/bin/env python3
"""Skin-through-sleeve gate (PeasantGirl copy of mm9_peasantm7_claude/scripts/sleeve_poke_gate.py: the grafted hands are in the body
material here, so the hand / sleeve split comes from the mesh npz parts: --npz work/uv_tex2.npz, --drop ears for the human GLB).
Original: user review 2026-11-01, PeasantM7: "hands sticking through the sleeves".

Per side: the sleeve = body-material triangles mostly weighted to that side's UpperArm/Forearm/Hand joints (the grafted
cuff has no open rim: Meshy's sleeve closes onto the old forearm). Candidates = head+hands-material vertices of that arm
(the grafted hand and its stub) up to 3 cm past the hand joint. Every clip at 48 fps, per candidate: a ray from the POSED
forearm->hand axis, perpendicular to it, through the vertex; where it meets the sleeve, the vertex must lie nearer the
axis than the hit (vertex radius - hit radius > TOL is skin through the cloth); no hit = the visible hand past the cuff.
Reports per clip and side: worst poke (mm), its frame, the number of frames with any poke > TOL, and the rest-pose count.
Usage: sleeve_poke_gate.py <glb> <out json> [--clips A,B] [--fps 48] [--tol 0.0005] [--margin 0.003]"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('glb'); ap.add_argument('out')
ap.add_argument('--clips', default='')
ap.add_argument('--fps', type=float, default=48.0)
ap.add_argument('--tol', type=float, default=0.0005)
ap.add_argument('--margin', type=float, default=0.003)
ap.add_argument('--npz', default='work/uv_tex2.npz'); ap.add_argument('--drop', default='')
o = ap.parse_args()
glb = Glb(Path(o.glb)); model = Model(glb)
doc = glb.json
names = [n.get('name') for n in doc['nodes']]
jn = [names[j] for j in model.joints]
P = model.primitives
node0 = P[0]['node']
mesh = doc['meshes'][doc['nodes'][node0]['mesh']]
USE = [k for k, pr in enumerate(P) if pr['node'] == node0 and pr['skinned']]
mats = [doc['materials'][mesh['primitives'][i].get('material', 0)]['name'] for i in range(len(USE))]
off, tri_all, dom_all, head_all = 0, [], [], []
for k, mname in zip(USE, mats):
    pr = P[k]
    tri_all.append(pr['triangles'] + off); off += len(pr['positions'])
    dom_all.append(np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]))
    head_all.append(np.full(len(pr['positions']), 'Head' in mname))
tris = np.concatenate(tri_all); dom = np.concatenate(dom_all)
# reduction copy (mm9_peasantgirl_reduce_claude): a reduced GLB keeps only the vertices it uses, so each GLB vertex takes the part of the
# installed elf vertex with the same position, UV and material (work/glb_parts.npz face labels -> vertex labels); --npz names the
# labels file, kept for the call signature
sys.path.insert(0, str(Path(__file__).resolve().parent)); import glbio as _gi  # noqa: E402
_HERE = Path(__file__).resolve().parents[1]
_g = np.load(_HERE / 'work' / 'glb_parts.npz'); pn_ = [str(x) for x in _g['names']]
_, _, _, _D = _gi.load(_HERE / 'before' / 'mm9_peasantgirl1e.glb', 'PeasantGirl')
_lab = {}
for _k, _nm in enumerate(['PeasantGirl_G1E', 'PeasantGirlHead']):
    _pp = _g['part'][_g['mat'] == _k]; _T = _D[_nm]['T']
    for _c in range(3):
        for _v, _q in zip(_T[:, _c], _pp):
            _lab[(_k, ) + tuple(np.round(_D[_nm]['P'][_v], 6)) + tuple(np.round(_D[_nm]['UV'][_v], 6))] = int(_q)
compv = []
_, _, _, _C = _gi.load(o.glb, 'PeasantGirl')
for _k, _nm in enumerate(mats):
    _Pc, _Uc = _C[_nm]['P'], _C[_nm]['UV']
    assert len(_Pc) == len(P[USE[_k]]['positions'])
    for _v in range(len(_Pc)):
        compv.append(_lab[(_k, ) + tuple(np.round(_Pc[_v], 6)) + tuple(np.round(_Uc[_v], 6))])
compv = np.array(compv)
assert len(compv) == len(dom), (len(compv), len(dom))
ishead = compv == pn_.index('hands')                      # candidates: the grafted hands and their stubs
tri_head = (compv[tris] != pn_.index('dress')).any(1)     # the sleeve: dress faces only


def posed(clip, t):
    w = model.world(model.sample(clip, float(t)) if clip else {})
    sp = model.skinned_positions(w)
    return w, np.concatenate([sp[k][0] for k in USE])


rw, rest = posed(None, 0)
idx = {n: i for i, n in enumerate(names)}
SIDES = {}
for tok in ('L', 'R'):
    arm = [j for j in jn if f' {tok} ' in j and any(k in j for k in ('UpperArm', 'Forearm', 'Hand', 'Finger', 'Thumb',
                                                                          'Index', 'Middle', 'Ring', 'Pinky'))]
    fa, hd = f'Bip01 {tok} Forearm', f'Bip01 {tok} Hand'
    a0, a1 = rw[idx[fa]][:3, 3], rw[idx[hd]][:3, 3]
    axis = (a1 - a0) / np.linalg.norm(a1 - a0)
    onarm = np.isin(dom, arm)
    sleeve_f = np.where(~tri_head & onarm[tris].sum(1).astype(bool) & (onarm[tris].sum(1) >= 2))[0]
    # open boundary of the sleeve triangles near the hand = the cuff rim
    E = np.sort(np.concatenate([tris[sleeve_f][:, [0, 1]], tris[sleeve_f][:, [1, 2]], tris[sleeve_f][:, [2, 0]]]), 1)
    # weld by position: glTF splits vertices at UV seams
    _, wid = np.unique(np.round(rest, 5), axis=0, return_inverse=True)
    wid = wid.ravel()
    Ew = np.sort(wid[E], 1)
    u, inv, cnt = np.unique(Ew, axis=0, return_inverse=True, return_counts=True)
    bnd = np.unique(E[cnt[inv.ravel()] == 1].ravel())
    near_hand = bnd[np.linalg.norm(rest[bnd] - a1, axis=1) < 0.08]
    t = (rest - a0) @ axis
    cand = np.where(ishead & np.isin(dom, arm) & (t < np.linalg.norm(a1 - a0) + 0.03) & (t > 0.05)
                    & (np.linalg.norm(np.cross(rest - a0, axis), axis=1) < 0.12))[0]
    t_rim, near_hand = 0.0, []
    SIDES[tok] = dict(sleeve_f=sleeve_f, cand=cand, t_rim=t_rim, rim_verts=len(near_hand), fa=idx[fa], hd=idx[hd])


def poke(W, X, d):
    """vertex radius minus the sleeve's radius along the same perpendicular ray (m; <= 0 inside, NaN when no sleeve)"""
    a0, a1 = W[d['fa']][:3, 3], W[d['hd']][:3, 3]
    ax = (a1 - a0) / np.linalg.norm(a1 - a0)
    v = X[d['cand']]
    tt = (v - a0) @ ax
    p0 = a0 + tt[:, None] * ax
    r = v - p0; rv = np.linalg.norm(r, axis=1); rd = r / np.maximum(rv, 1e-9)[:, None]
    T = X[tris[d['sleeve_f']]]
    A, B, C = T[:, 0], T[:, 1], T[:, 2]
    e1, e2 = B - A, C - A
    out = np.full(len(v), np.nan)
    for i in range(len(v)):
        pv = np.cross(rd[i], e2); det = np.einsum('ij,ij->i', e1, pv)
        ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
        tv = p0[i] - A
        uu = np.einsum('ij,ij->i', tv, pv) * inv
        qv = np.cross(tv, e1)
        vv = (qv @ rd[i]) * inv
        dist = np.einsum('ij,ij->i', e2, qv) * inv
        hit = ok & (uu >= 0) & (vv >= 0) & (uu + vv <= 1) & (dist > 0) & (dist < 0.10)
        if hit.any():
            out[i] = rv[i] - dist[hit].max()          # the outermost sleeve wall along the ray
    return out


rep = {'sides': {s: {'candidates': int(len(d['cand'])), 'rim_vertices': d['rim_verts'], 't_rim': round(d['t_rim'], 4)}
                 for s, d in SIDES.items()}, 'clips': {}}
for s, d in SIDES.items():
    sd = np.nan_to_num(poke(rw, rest, d), nan=-1.0)
    rep['sides'][s]['rest_poke_mm'] = round(float(max(sd.max(), 0) * 1000), 1)
    rep['sides'][s]['rest_poke_verts'] = int((sd > o.tol).sum())
clips = [c for c in model.clips if not o.clips or c in o.clips.split(',')]
for clip in clips:
    dur = max(model.clip_times(clip))
    times = np.arange(0, dur + 1e-6, 1 / o.fps) if dur > 0 else [0.0]
    e = {}
    for s in SIDES:
        e[s] = {'worst_mm': 0.0, 'frame': 0, 'frames_poking': 0, 'verts_worst_frame': 0}
    for k, tm in enumerate(times):
        W, X = posed(clip, tm)
        for s, d in SIDES.items():
            if not len(d['cand']):
                continue
            sd = np.nan_to_num(poke(W, X, d), nan=-1.0)
            m = float(sd.max())
            if m > o.tol:
                e[s]['frames_poking'] += 1
            if m * 1000 > e[s]['worst_mm']:
                e[s].update(worst_mm=round(m * 1000, 1), frame=k, verts_worst_frame=int((sd > o.tol).sum()))
    rep['clips'][clip] = e
    print(f"{clip:12s} " + ' | '.join(f"{s}: poke {v['worst_mm']:.1f}mm@{v['frame']} ({v['frames_poking']}f, {v['verts_worst_frame']}v)"
                                      for s, v in e.items()), flush=True)
print('SLEEVE_POKE', json.dumps(rep['sides']))
json.dump(rep, open(o.out, 'w'), indent=1)
