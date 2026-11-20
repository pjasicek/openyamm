#!/usr/bin/env python3
"""(mm9_highwayman_claude/scripts/blade_gate.py, Yanmir: the staff on Ystaff) Staff against the body (from mm9_imp_claude/scripts/blade_gate.py): every clip at 48 fps, points along the shaft and blades (densified) against the skin, excluding
the holding hand and fingers. Signed distance to the nearest triangle by its face normal; a point behind a face within 6 cm
is inside. Usage: staff_gate.py <full glb> <out json> Ystaff 'Bip01 R '. Also the grip: finger skin inside the shaft (r 2.1 cm) within 9 cm of the wrist's projection on the axis, and how far each finger wraps"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, '../claude_shared/floor'); sys.path.insert(0, '../claude_shared')
sys.path.insert(0, '../claude_shared/floor'); sys.path.insert(0, '../claude_shared')
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
g = Glb(Path(sys.argv[1])); m = Model(g)
names = [n.get('name') for n in g.json['nodes']]
jn = [names[j] for j in m.joints]
P = [p for p in m.primitives if p['node'] == m.primitives[0]['node'] and p['skinned']]
tri, off, dom = [], 0, []
for p in P:
    tri.append(p['triangles'] + off); off += len(p['positions'])
    dom.append(np.array([jn[p['joints'][v][np.argmax(p['weights'][v])]] for v in range(len(p['positions']))]))
tri = np.concatenate(tri); dom = np.concatenate(dom)
ITEM, TOK = sys.argv[3], sys.argv[4]
item = np.char.startswith(dom.astype(str), ITEM)
hand = np.array([any(k in d for k in (TOK + 'Hand', TOK + 'Finger', TOK + 'Thumb', TOK + 'Index', TOK + 'Middle', TOK + 'Ring', TOK + 'Pinky')) for d in dom])
uvs = np.concatenate([np.asarray(g.accessor(pr['attributes']['TEXCOORD_0'])) for pr in g.json['meshes'][0]['primitives'][:len(P)]])
ua = uvs[tri]; uvarea = np.abs((ua[:, 1, 0] - ua[:, 0, 0]) * (ua[:, 2, 1] - ua[:, 0, 1]) - (ua[:, 2, 0] - ua[:, 0, 0]) * (ua[:, 1, 1] - ua[:, 0, 1]))
other = np.char.startswith(dom.astype(str), 'Ystaff')
body_f = np.where(~(item[tri].any(1) | hand[tri].any(1) | other[tri].any(1)) & (uvarea > 1e-9))[0]    # the dark linings (one texel) are not skin
itf = np.where(item[tri].all(1))[0]
USE = [k for k, pr in enumerate(m.primitives) if pr['node'] == m.primitives[0]['node'] and pr['skinned']]
BARY = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1 / 3, 1 / 3, 1 / 3]])
iv = np.where(item)[0]
ax = np.linalg.svd(np.concatenate([p['positions'] for p in P])[iv] - np.concatenate([p['positions'] for p in P])[iv].mean(0))[2][0]
tt = np.concatenate([p['positions'] for p in P])[iv] @ ax
E0, E1 = iv[tt.argmin()], iv[tt.argmax()]
RSH = 0.021
FING = {f: np.where(np.char.startswith(dom.astype(str), TOK + f))[0] for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')}
HAND0 = np.where(dom == TOK + 'Hand')[0]
out = {}
for clip in m.clips:
    dur = max(m.clip_times(clip))
    worst = (0.0, 0, None); bad = 0; gin = [0.0, 0]; wrap = {}
    for k, t in enumerate(np.arange(0, dur + 1e-6, 1 / 48)):
        sp = m.skinned_positions(m.world(m.sample(clip, float(t))))
        X = np.concatenate([sp[i][0] for i in USE])
        pts = np.einsum('kb,fbc->fkc', BARY, X[tri[itf]]).reshape(-1, 3)
        ends = X[[E0, E1]]                     # the long shaft faces have no interior points: a line of 240 samples
        pts = np.vstack([pts, ends[0] + np.outer(np.linspace(0, 1, 240), ends[1] - ends[0])])
        T = X[tri[body_f]]
        a, b, c = T[:, 0], T[:, 1], T[:, 2]
        n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        tree = cKDTree((a + b + c) / 3)
        d0, near = tree.query(pts, k=16)
        q, _ = closest_on_triangles(np.repeat(pts, 16, 0), a[near.ravel()], b[near.ravel()], c[near.ravel()])
        d = np.linalg.norm(np.repeat(pts, 16, 0) - q, axis=1).reshape(near.shape)
        best = d.argmin(1); rows = np.arange(len(pts))
        side = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[rows, best], n[near[rows, best]])
        dep = np.where((side < 0) & (d[rows, best] <= 0.06) & (np.abs(side) > 0.9 * d[rows, best]), d[rows, best], 0.0)    # foot of the perpendicular on the face: the sole beside a pole is not 'inside'
        if dep.max() > worst[0]:
            worst = (float(dep.max()), k, dom[tri[body_f][near[rows, best][dep.argmax()], 0]])
        bad += int(dep.max() > 0.01)
        if k % 6 == 0 and len(HAND0):          # grip at 8 fps (none for the beard)
            Q = X[iv]; cq = Q.mean(0); uu = np.linalg.svd(Q - cq)[2][0]
            h0 = X[HAND0].mean(0); g0 = cq + uu * ((h0 - cq) @ uu)
            for f, ids in FING.items():
                v = X[ids] - g0; al = v @ uu; pr_ = v - np.outer(al, uu); r = np.linalg.norm(pr_, axis=1)
                on = np.abs(al) < 0.09
                if on.any(): gin[0] = max(gin[0], float((RSH - r[on]).max())); gin[1] += int((r[on] < RSH - 0.001).sum())
                kk = on & (r < 0.045)
                if kk.sum() > 3:
                    e1 = np.cross(uu, [0.3, 0.9, 0.2]); e1 /= np.linalg.norm(e1); e2 = np.cross(uu, e1)
                    wrap.setdefault(f, []).append(len(np.unique((np.degrees(np.arctan2(pr_[kk] @ e2, pr_[kk] @ e1)) // 15).astype(int))) * 15)
                else: wrap.setdefault(f, []).append(0)
    out[clip] = {'worst_cm': round(worst[0] * 100, 1), 'frame48': worst[1], 'bone': worst[2], 'frames_over_1cm': bad,
                 'grip_inside_cm': round(gin[0] * 100, 2), 'grip_inside_vert_samples': gin[1], 'wrap_deg_median': {f: int(np.median(v)) for f, v in wrap.items()}}
    print(clip, out[clip])
json.dump(out, open(sys.argv[2], 'w'), indent=1)
