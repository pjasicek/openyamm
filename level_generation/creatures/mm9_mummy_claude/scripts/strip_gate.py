#!/usr/bin/env python3
"""Thighs through the strips, per clip at 48 fps, on a clip GLB with the strips. Strip vertices (found by their helper bones) against the leg skin (faces whose dominant bone is a Thigh or Calf, and the pelvis):
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
T = np.vstack(Tall)
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
clips = [a['name'] for a in doc['animations'] if not want or a['name'] in want]
for clip in clips:
    dur = m.clip_times(clip)[-1]; times = np.arange(0, dur + 1e-6, 1 / 48)
    cnt = {k: 0 for k in strip_sets}; deep = {k: 0.0 for k in strip_sets}; when = {}
    for t in times:
        Pz = m.skinned_positions(m.world(m.sample(clip, float(t))))[0][0]
        A, B, C = Pz[F[:, 0]], Pz[F[:, 1]], Pz[F[:, 2]]
        n = np.cross(B - A, C - A); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        samp = np.vstack([(A + B + C) / 3, (A * 2 + B + C) / 4, (A + B * 2 + C) / 4, (A + B + C * 2) / 4]); ns = np.tile(n, (4, 1))
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
