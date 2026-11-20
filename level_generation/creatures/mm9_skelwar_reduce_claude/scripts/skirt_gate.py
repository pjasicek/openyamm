#!/usr/bin/env python3
"""(Copied from ../mm9_skeletonwarrior_claude with a per-piece label vote and SKIRT_K nearest plate faces, default 24 as installed:
the reduced plates have larger faces, and 24 nearest centroids missed the plate face nearest a femur top, which then read 11.6 cm
'through' a back plate 15 cm away; run both files at SKIRT_K=96.) Thigh and knee through the skirt plates, per clip at 48 fps, on a runtime GLB (LOD0).
A sample point of the femur, knee cap or boot top counts as through a plate when it lies on the plate's OUTER side and its nearest
plate point is inside that triangle (perpendicular foot on the plate, not past its edge: a knee below the hem is free). Lining faces
(zero UV area) are not plates. Depth is the distance outside. Plates by group: front, front-side, side, back-side, back.
Args: <glb> <out json> [clips, comma separated]"""
import json, os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
GROUPS = {'front': [25, 57], 'front_R': [33], 'front_L': [41, 60], 'side_R': [30, 32, 16], 'side_L': [14, 49, 65],
          'back_R': [38, 50, 61], 'back_L': [42, 56, 58], 'back': [47]}
PLATE = {p: g for g, v in GROUPS.items() for p in v}
LEG = {3: 'R', 37: 'R', 12: 'R', 103: 'L', 137: 'L', 112: 'L'}
glb, out = sys.argv[1:3]
want = sys.argv[3].split(',') if len(sys.argv) > 3 else None
D = np.load(HERE / 'work' / 'skirt_dump.npz')
m = Model(Glb(glb)); P = m.primitives
G = m.glb.json
body = G['meshes'][0]['primitives'][0]
k = 0
pr = P[k]
assert G['materials'][body['material']]['name'].startswith('SkelWar')
names = [n.get('name') for n in m.glb.json['nodes']]
rest = m.skinned_positions(m.world({}))[k][0]
# rest vertices to master part ids (the armature's lift is the rest z offset)
co = D['co']; lift = 1.0588
tgt = np.c_[co[:, 0], co[:, 2] + lift, -co[:, 1]]
tree = cKDTree(tgt); d, i = tree.query(rest)
print('match dist p99', np.percentile(d, 99))
pid = D['pid'][i]
# (reduction copy) one label per connected piece by majority: a reduced piece's new vertices can lie nearer a neighbour's
# master vertex (the skeleton reduction's piece_vote); the installed file relabels none
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
_k = np.round(rest / 1e-6).astype(np.int64); _, _w = np.unique(_k, axis=0, return_inverse=True); _w = _w.ravel()
_t = _w[pr['triangles']]; _n = _w.max() + 1
_r = np.concatenate([_t[:, 0], _t[:, 1], _t[:, 2]]); _c = np.concatenate([_t[:, 1], _t[:, 2], _t[:, 0]])
_, _lab = connected_components(coo_matrix((np.ones(len(_r)), (_r, _c)), shape=(_n, _n)), directed=False)
_lv = _lab[_w]; _new = pid.copy()
for _q in np.unique(_lv):
    _s = _lv == _q; _v, _cn = np.unique(pid[_s], return_counts=True); _new[_s] = _v[_cn.argmax()]
print('piece vote relabelled', int((_new != pid).sum()), 'vertices'); pid = _new
tri = pr['triangles']; uv = np.asarray(m.glb.accessor(body['attributes']['TEXCOORD_0']))
a = np.abs((uv[tri[:, 1], 0] - uv[tri[:, 0], 0]) * (uv[tri[:, 2], 1] - uv[tri[:, 0], 1]) - (uv[tri[:, 2], 0] - uv[tri[:, 0], 0]) * (uv[tri[:, 1], 1] - uv[tri[:, 0], 1]))
outer = a > 1e-9
fg = np.array([PLATE.get(int(pid[t[0]]), '') for t in tri])
pl = np.where((fg != '') & outer)[0]
print('plate faces', len(pl), 'all skirt', int((fg != '').sum()))
# leg samples: vertices plus points along edges of the femur; boots only near the knee
legv = np.where(np.isin(pid, list(LEG)))[0]
jn = [names[j] for j in m.joints]
res = {}
clips = [a_['name'] for a_ in m.glb.json['animations']]
for clip in clips:
    if want and clip not in want: continue
    dur = m.clip_times(clip)[-1]; T = np.arange(0, dur + 1e-6, 1 / 48)
    worst = {}; frames = 0; fdepth = []
    for t_i, t in enumerate(T):
        w = m.world(m.sample(clip, float(t))); x = m.skinned_positions(w)[k][0]
        keep = []
        for s, ids in (('R', (3, 37, 12)), ('L', (103, 137, 112))):
            kn = w[names.index(f'Bip01 {s} Calf')][:3, 3]
            mask = np.isin(pid, ids[:2]) | ((pid == ids[2]) & (np.linalg.norm(x - kn, axis=1) < 0.16))
            keep.append(np.where(mask)[0])
        q = np.r_[keep[0], keep[1]]
        ft = x[tri[pl]]
        c_ = ft.mean(1); n_ = np.cross(ft[:, 1] - ft[:, 0], ft[:, 2] - ft[:, 0]); n_ /= np.maximum(np.linalg.norm(n_, axis=1, keepdims=True), 1e-12)
        _, near = cKDTree(c_).query(x[q], k=min(int(os.environ.get("SKIRT_K", "24")), len(c_)))
        pts = np.repeat(x[q], near.shape[1], 0)
        qq, _ = closest_on_triangles(pts, ft[near.ravel(), 0], ft[near.ravel(), 1], ft[near.ravel(), 2])
        dd = np.linalg.norm(pts - qq, axis=1).reshape(near.shape); b = dd.argmin(1); r = np.arange(len(q))
        fid = near[r, b]; cp = qq.reshape(*near.shape, 3)[r, b]; v = x[q] - cp
        s_ = np.einsum('ij,ij->i', v, n_[fid]); dist = dd[r, b]
        through = (s_ > 0.002) & (s_ > 0.98 * dist) & (dist < 0.2)
        top = 0.0
        if through.any():
            frames += 1
            for ii in np.where(through)[0]:
                g = fg[pl[fid[ii]]]; lg = LEG[int(pid[q[ii]])]
                key = f'{lg} into {g}'
                if s_[ii] * 100 > worst.get(key, (0, 0))[0]: worst[key] = (round(float(s_[ii]) * 100, 1), t_i)
                top = max(top, s_[ii])
        fdepth.append(top)
    res[clip] = dict(frames=frames, of=len(T), max_cm=round(max(fdepth) * 100, 1), by=worst)
    print(f"{clip:15s} frames through {frames:3d}/{len(T):3d} max {max(fdepth) * 100:5.1f} cm", dict(sorted(worst.items(), key=lambda kv: -kv[1][0])[:6]), flush=True)
json.dump(res, open(out, 'w'), indent=1)
