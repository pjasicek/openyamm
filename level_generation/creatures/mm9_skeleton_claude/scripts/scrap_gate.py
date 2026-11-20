#!/usr/bin/env python3
"""Thigh through the hip scraps and vest, per clip at 48 fps, on a runtime GLB (LOD0). True penetration: sample points on the cloth triangles (corners, edge middles, centroids) are taken into the
thigh's rest frame each frame, and a point counts when it lies inside the closed femur mesh (femoral head and shaft): signed distance to the nearest femur triangle, sign from its normal. Lining faces (zero UV
area) are not cloth. Depth is how far inside. The Skeleton Warrior's side test ("on the outer side of the plate") does not fit: the scraps are narrow strips, many edge-on to the leg.
Args: <glb> <lift> <out json> [clips, comma separated]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
SCR = [52, 142, 134, 109, 144, 127]
CLOTH = {p: 'scrap_R' for p in SCR} | {p + 1000: 'scrap_L' for p in SCR} | {124: 'vest', 2: 'vest', 1002: 'vest', 47: 'vest', 1047: 'vest', 300: 'vest'}
LEG = {3: 'R', 65: 'R', 26: 'R', 1003: 'L', 1065: 'L', 1026: 'L'}
glb, lift, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
want = sys.argv[4].split(',') if len(sys.argv) > 4 else None
D = np.load(HERE / 'work' / 'pid_dump.npz')
m = Model(Glb(glb)); pr = m.primitives[0]; G = m.glb.json
body = G['meshes'][0]['primitives'][0]
assert G['materials'][body['material']]['name'].startswith('Skel') and 'Head' not in G['materials'][body['material']]['name']
rest = m.skinned_positions(m.world({}))[0][0]
co = D['co']; lift = rest[:, 1].min() - co[:, 2].min(); tgt = np.c_[co[:, 0], co[:, 2] + lift, -co[:, 1]]
d, i = cKDTree(tgt).query(rest); print('match dist p99', np.percentile(d, 99), 'max', d.max())
pid = D['pid'][i]
tri = pr['triangles']; uv = np.asarray(m.glb.accessor(body['attributes']['TEXCOORD_0']))
a = np.abs((uv[tri[:, 1], 0] - uv[tri[:, 0], 0]) * (uv[tri[:, 2], 1] - uv[tri[:, 0], 1]) - (uv[tri[:, 2], 0] - uv[tri[:, 0], 0]) * (uv[tri[:, 1], 1] - uv[tri[:, 0], 1]))
outer = a > 1e-9
fg = np.array([CLOTH.get(int(pid[t[0]]), '') for t in tri])
pl = np.where((fg != '') & outer)[0]
print('cloth faces', len(pl), 'all', int((fg != '').sum()))
names = [n.get('name') for n in G['nodes']]
ci = pl
FEM = {}
for sd, off in (('R', 0), ('L', 1000)):
    f = np.where(np.isin(pid[tri[:, 0]], (3 + off, 65 + off)))[0]
    t_ = rest[tri[f]]; n_ = np.cross(t_[:, 1] - t_[:, 0], t_[:, 2] - t_[:, 0]); n_ /= np.maximum(np.linalg.norm(n_, axis=1, keepdims=True), 1e-12)
    FEM[sd] = (t_, n_, cKDTree(t_.mean(1)), names.index(f'Bip01 {sd} Thigh'))
ctri = tri[ci]; A_, B_, C_ = ctri[:, 0], ctri[:, 1], ctri[:, 2]
res = {}
joints = list(m.joints); ibm = m.inverse_binds
for clip in [a_['name'] for a_ in G['animations']]:
    if want and clip not in want: continue
    dur = m.clip_times(clip)[-1]; T = np.arange(0, dur + 1e-6, 1 / 48)
    worst = {}; frames = 0; fdepth = []
    for t_i, t in enumerate(T):
        w = m.world(m.sample(clip, float(t))); x = m.skinned_positions(w)[0][0]
        P = np.vstack([x[A_], x[B_], x[C_], (x[A_] + x[B_]) / 2, (x[B_] + x[C_]) / 2, (x[A_] + x[C_]) / 2, (x[A_] + x[B_] + x[C_]) / 3])
        lab = np.tile(np.array([f'{g}#{int(pid[tri[i, 0]])}' for i, g in zip(ci, fg[ci])]), 7); top = 0.0
        for sd, (ft, fn, kd, node) in FEM.items():
            M = w[node] @ ibm[joints.index(node)]
            q = (np.linalg.inv(M) @ np.c_[P, np.ones(len(P))].T).T[:, :3]
            _, near = kd.query(q, k=min(12, len(ft)))
            pts = np.repeat(q, near.shape[1], 0); cand = near.ravel()
            cp, _ = closest_on_triangles(pts, ft[cand, 0], ft[cand, 1], ft[cand, 2])
            dd = np.linalg.norm(pts - cp, axis=1).reshape(near.shape); b = dd.argmin(1); r = np.arange(len(q))
            c = cp.reshape(*near.shape, 3)[r, b]; sg = ((q - c) * fn[near[r, b]]).sum(1)
            inside = (sg < -0.002) & (-sg > 0.9 * dd[r, b])
            if inside.any():
                i_ = np.where(inside)[0]; j_ = i_[np.argmax(dd[r, b][i_])]; dep = float(dd[r, b][j_])
                key = f'{sd} femur / {lab[j_]}'
                if dep * 100 > worst.get(key, (0, 0))[0]: worst[key] = (round(dep * 100, 1), t_i)
                top = max(top, dep)
        if top > 0: frames += 1
        fdepth.append(top)
    res[clip] = dict(frames=frames, of=len(T), max_cm=round(max(fdepth) * 100, 1), by=worst)
    print(f"{clip:15s} frames through {frames:3d}/{len(T):3d} max {max(fdepth) * 100:5.1f} cm", dict(sorted(worst.items(), key=lambda kv: -kv[1][0])[:4]), flush=True)
json.dump(res, open(out, 'w'), indent=1)
