#!/usr/bin/env python3
"""Arm-through-sleeve gate for PF1 (after mm9_peasantm7_claude/scripts/sleeve_poke_gate.py; TOWNSFOLK_BRIEF "Sleeves and hands"): the
MPFB upper-arm stub inside each short puffed sleeve. On work/half.glb (the rigged mesh before the runtime steps; vertex positions match
work/uv_tex2.npz, so parts are known): candidates = arm vertices ('hands' part) between the shoulder and the sleeve hem + 1 cm along the
posed UpperArm->Forearm axis; sleeve = dress triangles beyond x 0.15. Every clip at FPS: a ray from the posed axis, perpendicular to it,
through the vertex; where it meets the sleeve, the vertex must lie nearer the axis than the hit (vertex radius - hit radius > TOL = skin
through the cloth) unless more sleeve lies further out on that ray (the gathered hem rolls inward over the arm); no hit = bare arm below the hem. Args: <half glb> <out json> [fps] [tol m]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
G, OUT = sys.argv[1:3]; FPS = float(sys.argv[3]) if len(sys.argv) > 3 else 30.0; TOL = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0005
glb = Glb(Path(G)); model = Model(glb); doc = glb.json; names = [n.get('name') for n in doc['nodes']]; idx = {n: i for i, n in enumerate(names)}
P = model.primitives; USE = [k for k, pr in enumerate(P) if pr['skinned']]
tris = []; off = 0
for k in USE: tris.append(P[k]['triangles'] + off); off += len(P[k]['positions'])
tris = np.concatenate(tris)
def posed(clip, t):
    w = model.world(model.sample(clip, float(t)) if clip else {})
    sp = model.skinned_positions(w); return w, np.concatenate([sp[k][0] for k in USE])
rw, rest = posed(None, 0)
U = np.load(HERE / 'work' / 'uv_tex2.npz'); pn = [str(x) for x in U['names']]
Ub = np.c_[U['co'][:, 0], U['co'][:, 2], -U['co'][:, 1]]          # Blender -> glTF
off_ = np.array([0, rest[:, 1].min() - Ub[:, 1].min(), 0]); Ub = Ub + off_      # the scene root's lift to the floor
d, nn = cKDTree(Ub).query(rest); part = np.where(d < 1e-4, U['comp'][nn], -1)
print('matched', round(float((d < 1e-4).mean()), 4))
HEM = float(np.load(HERE / 'work' / 'asm_frozen.npz')['hem'])
SIDES = {}
for s in ('L', 'R'):
    a0, a1 = rw[idx[f'FHP {s} UpperArm']][:3, 3], rw[idx[f'FHP {s} Forearm']][:3, 3]; ax = (a1 - a0) / np.linalg.norm(a1 - a0)
    sg = np.sign(a1[0])
    t = (rest - a0) @ ax
    cand = np.where((part == pn.index('hands')) & (np.sign(rest[:, 0]) == sg) & (t > 0.02) & (t < HEM + 0.01))[0]
    dv = (part == pn.index('dress')) & (rest[:, 0] * sg > 0.15)
    sf = np.where(dv[tris].all(1))[0]
    SIDES[s] = dict(cand=cand, sf=sf, ua=idx[f'FHP {s} UpperArm'], fa=idx[f'FHP {s} Forearm'])
    print(s, 'candidates', len(cand), 'sleeve faces', len(sf))
def poke(W, X, dd):
    a0, a1 = W[dd['ua']][:3, 3], W[dd['fa']][:3, 3]; ax = (a1 - a0) / np.linalg.norm(a1 - a0)
    v = X[dd['cand']]; tt = (v - a0) @ ax; p0 = a0 + tt[:, None] * ax
    r = v - p0; rv = np.linalg.norm(r, axis=1); rd = r / np.maximum(rv, 1e-9)[:, None]
    T = X[tris[dd['sf']]]; A, B, C = T[:, 0], T[:, 1], T[:, 2]; e1, e2 = B - A, C - A
    out = np.full(len(v), np.nan)
    for i in range(len(v)):
        pv = np.cross(rd[i], e2); det = np.einsum('ij,ij->i', e1, pv); ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1 / np.where(ok, det, 1), 0); tv = p0[i] - A
        uu = np.einsum('ij,ij->i', tv, pv) * inv; qv = np.cross(tv, e1); vv = np.einsum('j,ij->i', rd[i], qv) * inv
        tr = np.einsum('ij,ij->i', e2, qv) * inv
        hit = ok & (uu >= 0) & (vv >= 0) & (uu + vv <= 1) & (tr > 0)
        if hit.any():
            th = tr[hit]
            # covered = sleeve cloth further out along the same ray (an inward-rolled, gathered hem lies inside the arm's radius there)
            out[i] = -1.0 if (th > rv[i] - TOL).any() else rv[i] - th.max()
    return out
rep = {'tol_m': TOL, 'clips': {}}
DEBUG = '--debug' in sys.argv
for a in ([] if DEBUG else doc.get('animations', [])):
    clip = a['name']; dur = model.duration(clip) if hasattr(model, 'duration') else max(float(glb.accessor(sm['input']).max()) for sm in a['samplers'])
    n = max(2, int(dur * FPS) + 1); row = {}
    for s, dd in SIDES.items():
        worst, wf, nf = 0.0, 0, 0
        for f in range(n):
            W, X = posed(clip, min(f / FPS, dur))
            p = poke(W, X, dd); m = float(np.nanmax(p)) if np.isfinite(p).any() else -1
            if m > TOL: nf += 1
            if m > worst: worst, wf = m, f
        row[s] = dict(worst_mm=round(worst * 1000, 1), frame=wf, frames_over=nf, frames=n)
    rep['clips'][clip] = row
    print(f"{clip:12s} " + ' | '.join(f"{s}: {r['worst_mm']} mm @{r['frame']} ({r['frames_over']}/{r['frames']} f)" for s, r in row.items()))
json.dump(rep, open(OUT, 'w'), indent=1); print('SLEEVE_POKE done')
if '--debug' in sys.argv:
    for s, dd in SIDES.items():
        p = poke(rw, rest, dd); a0, a1 = rw[dd['ua']][:3, 3], rw[dd['fa']][:3, 3]; ax = (a1 - a0) / np.linalg.norm(a1 - a0)
        bad = np.where(p > TOL)[0]; v = rest[dd['cand'][bad]]; t = (v - a0) @ ax
        print(s, 'rest pokes', len(bad), 't range', np.round([t.min(), t.max()], 3) if len(bad) else None, 'mm', np.round(np.sort(p[bad])[-5:] * 1000, 1))
        for i in bad[np.argsort(-p[bad])][:5]: print('  ', np.round(rest[dd['cand'][i]], 3), 't', round(float((rest[dd['cand'][i]] - a0) @ ax), 3), 'poke mm', round(p[i] * 1000, 1))
