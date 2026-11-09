#!/usr/bin/env python3
"""Hands and forearms inside solid bones, per clip at 48 fps, on a runtime GLB (LOD0). arm_hand_gate.py counts any sheet near a hand: on this body its depth is capped noise from the open vest panels and hip strips (viewer shots
show air there). Here the solids are the closed bones: pelvis, ribcage, sternum, spine, femurs, the other arm's bones. Samples: hand and finger and forearm vertices, taken into each solid's rest frame; a sample counts when it lies inside the
closed mesh (signed distance to the nearest triangle, sign from its normal). Args: <glb> <lift> <out json> [clips]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
glb, lift, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
want = sys.argv[4].split(',') if len(sys.argv) > 4 else None
D = np.load(HERE / 'work' / 'pid_dump.npz')
m = Model(Glb(glb)); pr = m.primitives[0]; G = m.glb.json
rest = m.skinned_positions(m.world({}))[0][0]
co = D['co']; lift = rest[:, 1].min() - co[:, 2].min(); tgt = np.c_[co[:, 0], co[:, 2] + lift, -co[:, 1]]
d, i = cKDTree(tgt).query(rest); pid = D['pid'][i]
names = [n.get('name') for n in G['nodes']]; joints = list(m.joints); ibm = m.inverse_binds
tri = pr['triangles']
HAND = [74, 149, 150, 33, 90, 29, 77, 130, 7, 104, 107, 45, 135, 15, 59, 136, 67, 111]
FORE = [76, 6, 41, 54]
SOLID = {'pelvis': ([36], 'Bip01 Spine'), 'ribs': ([18], 'Bip01 Spine2'), 'femur_L': ([1003, 1065], 'Bip01 L Thigh'), 'femur_R': ([3, 65], 'Bip01 R Thigh')}
S = {}
for k, (ids, bone) in SOLID.items():
    f = np.where(np.isin(pid[tri[:, 0]], ids))[0]; t_ = rest[tri[f]]
    n_ = np.cross(t_[:, 1] - t_[:, 0], t_[:, 2] - t_[:, 0]); n_ /= np.maximum(np.linalg.norm(n_, axis=1, keepdims=True), 1e-12)
    S[k] = (t_, n_, cKDTree(t_.mean(1)), names.index(bone))
ARM = {'L hand': np.where(np.isin(pid, [1000 + p for p in HAND]))[0], 'R hand': np.where(np.isin(pid, HAND))[0], 'L fore': np.where(np.isin(pid, [1000 + p for p in FORE]))[0], 'R fore': np.where(np.isin(pid, FORE))[0]}
res = {}
for clip in [a['name'] for a in G['animations']]:
    if want and clip not in want: continue
    dur = m.clip_times(clip)[-1]; T = np.arange(0, dur + 1e-6, 1 / 48); stats = {}
    for t_i, t in enumerate(T):
        w = m.world(m.sample(clip, float(t))); x = m.skinned_positions(w)[0][0]
        for arm, idx in ARM.items():
            top = 0.0; who = ''
            for k, (ft, fn, kd, node) in S.items():
                if k.endswith(arm[0]) and k.startswith('femur') and False: continue
                M = w[node] @ ibm[joints.index(node)]
                q = (np.linalg.inv(M) @ np.c_[x[idx], np.ones(len(idx))].T).T[:, :3]
                dist0, _ = kd.query(q); near_mask = dist0 < 0.09
                if not near_mask.any(): continue
                qq = q[near_mask]; _, near = kd.query(qq, k=min(10, len(ft)))
                pts = np.repeat(qq, near.shape[1], 0); cand = near.ravel()
                cp, _ = closest_on_triangles(pts, ft[cand, 0], ft[cand, 1], ft[cand, 2])
                dd = np.linalg.norm(pts - cp, axis=1).reshape(near.shape); b = dd.argmin(1); r = np.arange(len(qq))
                c = cp.reshape(*near.shape, 3)[r, b]; sg = ((qq - c) * fn[near[r, b]]).sum(1)
                ins = (sg < -0.003) & (-sg > 0.85 * dd[r, b]) & (dd[r, b] < 0.035)   # these bones are under 7 cm thick: deeper means a stray back-facing triangle
                if ins.any():
                    dep = float(dd[r, b][ins].max())
                    if dep > top: top, who = dep, k
            s = stats.setdefault(arm, dict(frames=0, max_cm=0.0, by=''))
            if top > 0.01: s['frames'] += 1
            if top * 100 > s['max_cm']: s['max_cm'] = round(top * 100, 1); s['by'] = f'{who}@{t_i}'
    res[clip] = stats
    print(f'{clip:14s}', ' | '.join(f"{a}: {v['max_cm']}cm {v['frames']}f>1cm {v['by']}" for a, v in stats.items()), flush=True)
json.dump(res, open(out, 'w'), indent=1)
