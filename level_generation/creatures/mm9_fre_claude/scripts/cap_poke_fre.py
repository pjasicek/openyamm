#!/usr/bin/env python3
"""Fre cap poke gate (2026-11-04): what shows THROUGH the hair cap. Per clip at every key and 30 fps, every body vertex (head shell, neck,
bodice, old hood) is tested against the posed cap's outer surface along the ray from the cap's centre (the mean of its outer vertices):
when the ray meets the cap closer to the centre than the body vertex, that vertex stands outside the hair (visible through it). Reports the
deepest poke beyond the bind pose's own reading (mm) and the frames with any vertex more than 2 mm out. Old-hood vertices are the hidden
skull; they are reported separately. Args: <glb> <asm npz> <uv npz> <out json>"""
import sys, json
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor')); sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb_pose import Glb, Model
from geo4 import raycast
M = Model(Glb(sys.argv[1])); A = np.load(sys.argv[2]); U = np.load(sys.argv[3]); OUT = sys.argv[4]
names = [str(x) for x in A['names']]; comp = A['comp']; twin = A['f4_twin_v']; par = A['f4_param']
ut, um, uo = U['tri'], U['mat'], U['orig']; rows = []; T0 = []; off = 0
for m in range(len(M.primitives)):
    used = np.unique(ut[um == m]); rows.append(uo[used]); T0.append(M.primitives[m]['triangles'] + off); off += len(used)
rows = np.concatenate(rows); T0 = np.vstack(T0); cp = comp[rows]
allpos = lambda p: np.vstack([a for a, _ in p])
K = lambda n: names.index(n)
if 'hair2' in names: capv = (cp == K('hair2')) & ~A['hair2_tube'][rows]      # pass 4: PeasantF2's hair cap
else: capv = (cp == K('hood4')) & (twin[rows] < 0)
capT = T0[capv[T0].all(1)]
body = np.where(np.isin(cp, [K('head'), K('dress')]))[0]; old = np.where(cp == K('scarf'))[0]
rest = allpos(M.skinned_positions(M.world({})))
_c0 = rest[capv].mean(0); body = body[np.linalg.norm(rest[body] - _c0, axis=1) < 0.13]      # the neck and nape inside the hair's reach
def poke(pts, idx):
    c = pts[capv].mean(0); d = pts[idx] - c; r = np.linalg.norm(d, axis=1); u = d / r[:, None]
    t = raycast(c, u, pts, capT); return np.where(np.isfinite(t), r - t, -1.0)      # > 0: outside the cap
if 'hair2' in names:
    # pass 4: PeasantF2's hair rim lies on the skin (1.5 mm), so skin at the hairline is beside the rim, not under it: only vertices the
    # hair covers at rest (ray hit, inside) and that lie more than RIMSKIP from the cap's open rim are tested
    from scipy.spatial import cKDTree as _K
    _ct = T0[capv[T0].all(1)]; _key = np.round(rest, 5); _, _wi = np.unique(_key, axis=0, return_inverse=True); _wi = _wi.ravel()
    _e = np.sort(np.vstack([_wi[_ct[:, [0, 1]]], _wi[_ct[:, [1, 2]]], _wi[_ct[:, [2, 0]]]]), 1); _u, _cn = np.unique(_e, axis=0, return_counts=True)
    _rim = rest[np.isin(_wi, np.unique(_u[_cn == 1])) & capv]; _kd = _K(_rim)
    def _keep(idx):
        p0 = poke(rest, idx); dr, _ = _kd.query(rest[idx]); return idx[(p0 > -1.0) & (p0 <= 0) & (dr > float(__import__('os').environ.get('RIMSKIP', '0.008')))]
    body, old = _keep(body), _keep(old)
    print('TESTED body', len(body), 'old hood', len(old))
B0, O0 = poke(rest, body), poke(rest, old)
res = {}
for clip in M.clips:
    times = M.clip_times(clip); ts = np.unique(np.r_[times, np.arange(0, times[-1] + 1e-6, 1 / 30)])
    w = {'body': [0.0, None, 0], 'oldhood': [0.0, None, 0]}
    for t in ts:
        pts = allpos(M.skinned_positions(M.world(M.sample(clip, t))))
        for k, idx, base in (('body', body, B0), ('oldhood', old, O0)):
            p = poke(pts, idx); e = np.where(p > 0, p - np.maximum(base, 0), 0).max()
            if e > w[k][0]: w[k][0], w[k][1] = float(e), round(float(t), 3)
            if e > 0.002: w[k][2] += 1
    res[clip] = {k: {'max_mm': round(v[0] * 1000, 1), 'at_s': v[1], 'frames_over_2mm': v[2], 'frames': int(len(ts))} for k, v in w.items()}
    print(f'{clip:10s}', '  '.join(f"{k}: {v['max_mm']:5.1f} mm @{v['at_s']} ({v['frames_over_2mm']}/{v['frames']} > 2 mm)" for k, v in res[clip].items()))
json.dump(res, open(OUT, 'w'), indent=1)
