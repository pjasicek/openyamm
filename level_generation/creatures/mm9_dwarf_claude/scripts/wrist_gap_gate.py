#!/usr/bin/env python3
"""Glove and bracer at the wrist (run 2, coordinator 2026-10-31: a dark jagged wedge between the glove top and the bracer cuff when the wrist bends).
The bracer is the voxel skin (torso set, rigid on the forearm) closed at the wrist by a cap on the dark texel (finish_dwarf.py); the glove (limbs set) is
a closed shell whose top sits inside the bracer. Exposed cap: cap faces (dark texel, within 9 cm of the hand joint) whose centroid lies outside the glove
surface by more than 2 mm (signed distance to the nearest glove face, by its normal) - the dark annulus you see between glove and cuff. Per clip at 48 fps
and side: the largest exposed area (cm2), its frame, and the wrist bend (hand against forearm, deg) there; also the largest gap (cm) from an exposed cap
point to the glove. Args: <glb> [clips]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
g = Glb(Path(sys.argv[1])); m = Model(g); d = g.json
want = sys.argv[2].split(',') if len(sys.argv) > 2 else None
names = [n.get('name') for n in d['nodes']]
P = [p for p in m.primitives if p['skinned'] and p['node'] == m.primitives[0]['node']]
prims = d['meshes'][d['nodes'][m.primitives[0]['node']]['mesh']]['primitives'][:len(P)]
mats = [d['materials'][pr['material']]['name'] for pr in prims]
DT = json.load(open(HERE / 'work' / 'dark_texel.json'))['torso']
w0 = m.world({})
offs = np.cumsum([0] + [len(p['positions']) for p in P])
tri = np.vstack([p['triangles'] + o for p, o in zip(P, offs)])
fmat = np.concatenate([[mn] * len(p['triangles']) for p, mn in zip(P, mats)])
uv = np.vstack([np.asarray(g.accessor(pr['attributes']['TEXCOORD_0']), float) for pr in prims])
X0 = np.vstack([x for x, _ in m.skinned_positions(w0)[:len(P)]])
dark = np.linalg.norm(uv[tri].mean(1) - [DT['u'], DT['v']], axis=1) < 0.002
torso = np.char.startswith(fmat.astype(str), 'DwarfTorso'); limbs = np.char.startswith(fmat.astype(str), 'DwarfLimbs')
SIDE = {}
for s in 'LR':
    H = w0[names.index(f'Bip01 {s} Hand')][:3, 3]; c0 = X0[tri].mean(1)
    cap = np.where(torso & dark & (np.linalg.norm(c0 - H, axis=1) < 0.09))[0]
    glove = np.where(limbs & (np.linalg.norm(c0 - H, axis=1) < 0.16))[0]
    near_t = np.where(torso & ~dark & (np.linalg.norm(c0 - H, axis=1) < 0.12))[0]
    wall = {tuple(np.round(X0[v], 5)) for v in np.unique(tri[near_t])}          # the cap's own vertices are split from the wall's by the UV seam
    pos = {}
    for v in np.unique(tri[cap]):
        k_ = tuple(np.round(X0[v], 5))
        if k_ in wall: pos.setdefault(k_, v)                                       # where the cap meets the bracer's wall
    SIDE[s] = dict(cap=cap, glove=glove, rim=np.array(sorted(pos.values()), int))


def area(x, f): return 0.5 * np.linalg.norm(np.cross(x[tri[f, 1]] - x[tri[f, 0]], x[tri[f, 2]] - x[tri[f, 0]]), axis=1)


def exposed(x, s):
    cap, glove = SIDE[s]['cap'], SIDE[s]['glove']
    T = x[tri[glove]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
    n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    pts = x[tri[cap]].mean(1)
    _, near = cKDTree((a + b + c) / 3).query(pts, k=16)
    rp = np.repeat(pts, 16, 0); q, _ = closest_on_triangles(rp, a[near.ravel()], b[near.ravel()], c[near.ravel()])
    dd = np.linalg.norm(rp - q, axis=1).reshape(near.shape); bi = dd.argmin(1); r = np.arange(len(pts))
    sd = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[r, bi], n[near[r, bi]])
    out = sd > 0.002
    return float(area(x, cap[out]).sum()), float(sd.max())


def rim_gap(x, s):
    """per rim vertex: distance to the glove surface (cm). The opening you look into between cuff and glove."""
    glove, rim = SIDE[s]['glove'], SIDE[s]['rim']
    T = x[tri[glove]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
    pts = x[rim]; _, near = cKDTree((a + b + c) / 3).query(pts, k=16)
    rp = np.repeat(pts, 16, 0); q, _ = closest_on_triangles(rp, a[near.ravel()], b[near.ravel()], c[near.ravel()])
    return np.linalg.norm(rp - q, axis=1).reshape(near.shape).min(1) * 100


def bend(w, s):
    A = w[names.index(f'Bip01 {s} Forearm')][:3, :3]; B = w[names.index(f'Bip01 {s} Hand')][:3, :3]
    A0 = w0[names.index(f'Bip01 {s} Forearm')][:3, :3]; B0 = w0[names.index(f'Bip01 {s} Hand')][:3, :3]
    R = (np.linalg.inv(A) @ B) @ np.linalg.inv(np.linalg.inv(A0) @ B0)
    U, _, Vt = np.linalg.svd(R); R = U @ Vt
    return float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))))


RG0 = {s: rim_gap(X0, s) for s in 'LR'}
print('rim verts', {s: len(v['rim']) for s, v in SIDE.items()}, 'rest rim gap cm max/mean', {s: (round(float(v.max()), 2), round(float(v.mean()), 2)) for s, v in RG0.items()})
res = {}
for clip in m.clips:
    if want and clip not in want: continue
    dur = max(m.clip_times(clip)); e = {s: dict(gap_cm=0.0, open_cm=0.0, frame=0, bend=0.0, frames_over=0) for s in 'LR'}
    for k, t in enumerate(np.arange(0, dur + 1e-6, 1 / 48)):
        w = m.world(m.sample(clip, float(t))); x = np.vstack([xx for xx, _ in m.skinned_positions(w)[:len(P)]])
        for s in 'LR':
            g_ = rim_gap(x, s); op = float((g_ - RG0[s]).max())            # widening of the opening against rest, worst rim point
            e[s]['frames_over'] += int(op > 0.5)
            if op > e[s]['open_cm']: e[s].update(open_cm=op, gap_cm=float(g_.max()), frame=k, bend=bend(w, s))
    res[clip] = {s: {k_: round(v, 2) for k_, v in e[s].items()} for s in 'LR'}
    print(f"{clip:13s} " + ' | '.join(f"{s}: opens +{e[s]['open_cm']:4.2f} cm (gap {e[s]['gap_cm']:4.2f}) @{e[s]['frame']:3d} bend {e[s]['bend']:5.1f}, {e[s]['frames_over']} f > 0.5" for s in 'LR'), flush=True)
json.dump(res, open(HERE / 'review' / 'gates' / 'wrist_gap.json', 'w'), indent=1)
