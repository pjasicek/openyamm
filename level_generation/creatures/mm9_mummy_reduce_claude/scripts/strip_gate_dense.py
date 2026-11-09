#!/usr/bin/env python3
"""Mummy reduction copy of ../mm9_mummy_claude/scripts/strip_gate.py with surface samples at a fixed spacing (SPACING m, default
0.006) instead of four per face: the creature's gate samples each skin face at its centroid and three inner points, so on a
reduced leg (larger faces) the nearest sample can be up to the 10 cm search bound away and the 45 deg cone test reads a band point
outside the leg as "through" at that distance. Run on the installed file and the candidate alike; SPACING=0 keeps the creature's four samples per face.
Original: Thighs through the strips, per clip at 48 fps, on a clip GLB with the strips. Strip vertices (found by their helper bones) against the leg skin (faces whose dominant bone is a Thigh or Calf, and the pelvis):
a strip point is through when it lies behind the nearest skin sample within 45 deg (as arm_hand_gate). Reports per clip and strip: frames with any point through, deepest cm.
Args: <glb> <out json> [clips]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb, out = sys.argv[1:3]
want = sys.argv[3].split(',') if len(sys.argv) > 3 and sys.argv[3] else None
m = Model(Glb(glb)); doc = m.glb.json
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
prs = m.primitives
# all primitives with one vertex set; LOD0 = first mesh
P0 = prs[0]; J = P0['joints']; W = P0['weights']
dom = J[np.arange(len(J)), W.argmax(1)]
Tall = [p['triangles'] for p in prs if p['node'] == P0['node']]
print('prims', len(prs), [len(t) for t in Tall])
# the creature's gate stacked every primitive's triangles (the head's index the head's own vertices) onto the body's vertex set: ~80
# garbage 'leg' faces spanning random body vertices (83 in the installed file, 78 in the reduced one). Only the body primitive here.
T = Tall[0]
SK = sys.argv[4] if len(sys.argv) > 4 else 'leg'
leg_b = {names.index(n) for n in names if any(k in n for k in (('Thigh', 'Calf') if SK == 'leg' else ('Pelvis', 'Bip01 Spine')))} 
strip_sets = {'band': ['XstripRoot', 'XstripTip'] + [n for n in names if n.startswith('Xband')]}
sid = np.full(len(J), -1)
for i, (k, bs) in enumerate(strip_sets.items()):
    idx = [names.index(b) for b in bs]; sid[np.isin(J, idx).any(1)] = i
# the band's root is pinned on the waist on purpose: first 15 % of its length out of the test
bandv = np.where(sid == 0)[0]; wr = names.index('XstripRoot'); root_w = (W[bandv] * (J[bandv] == wr)).sum(1); sid[bandv[root_w > 0.01]] = -2
print('strip verts', {k: int((sid == i).sum()) for i, k in enumerate(strip_sets)})
vf = np.isin(dom, list(leg_b)) & (sid < 0)
F = T[vf[T].all(1)]
res = {}
import os
SP = float(os.environ.get('SPACING', '0.006'))
BARY = np.array([[1, 1, 1], [2, 1, 1], [1, 2, 1], [1, 1, 2]], float); BARY /= BARY.sum(1, keepdims=True)
# extra barycentric samples on faces larger than the spacing (rest-pose size; the legs do not stretch much)
P0r = m.skinned_positions(m.world(m.sample('Standing', 0.0)))[0][0]
fi, fw = [], []
for f_, t_ in enumerate(F):
    a_, b_, c_ = P0r[t_]; L = max(np.linalg.norm(b_ - a_), np.linalg.norm(c_ - b_), np.linalg.norm(a_ - c_))
    k = int(np.ceil(L / SP)) if SP > 0 else 0
    if SP > 0 and k > 2:
        i_, j_ = np.meshgrid(np.arange(k + 1), np.arange(k + 1)); mm = i_ + j_ <= k
        w_ = np.stack([i_[mm], j_[mm], k - i_[mm] - j_[mm]], 1) / k
        fi.append(np.full(len(w_), f_)); fw.append(w_)
FINE = (np.concatenate(fi), np.concatenate(fw)) if fi else None
print('leg faces', len(F), 'extra samples', 0 if FINE is None else len(FINE[0]))
clips = [a['name'] for a in doc['animations'] if not want or a['name'] in want]
for clip in clips:
    dur = m.clip_times(clip)[-1]; times = np.arange(0, dur + 1e-6, 1 / 48)
    cnt = {k: 0 for k in strip_sets}; deep = {k: 0.0 for k in strip_sets}; when = {}
    for t in times:
        Pz = m.skinned_positions(m.world(m.sample(clip, float(t))))[0][0]
        A, B, C = Pz[F[:, 0]], Pz[F[:, 1]], Pz[F[:, 2]]
        n = np.cross(B - A, C - A); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        samp = np.einsum('sk,fkc->fsc', BARY, np.stack([A, B, C], 1)).reshape(-1, 3); ns = np.repeat(n, len(BARY), 0)
        if FINE is not None:
            samp = np.vstack([samp, np.einsum('fk,fkc->fc', FINE[1], np.stack([A, B, C], 1)[FINE[0]])]); ns = np.vstack([ns, n[FINE[0]]])
        tree = cKDTree(samp)
        for i, k in enumerate(strip_sets):
            pts = Pz[sid == i]
            d, f = tree.query(pts, distance_upper_bound=0.10)
            ok = np.isfinite(d)
            if not ok.any(): continue
            v = samp[f[ok]] - pts[ok]; dot = (v * ns[f[ok]]).sum(1); dist = d[ok]
            inside = dot > 0.7 * dist           # behind the surface, within a 45 deg cone
            if inside.any():
                cnt[k] += 1; dd = dist[inside].max() * 100
                if dd > deep[k]: deep[k] = dd; when[k] = float(t)
    res[clip] = {k: {'frames': cnt[k], 'of': len(times), 'deep_cm': round(deep[k], 2), 't': when.get(k)} for k in strip_sets}
    print(f'{clip:14}', ' '.join(f'{k} {cnt[k]}/{len(times)} {deep[k]:.1f}cm' for k in strip_sets))
json.dump(res, open(out, 'w'), indent=1)
