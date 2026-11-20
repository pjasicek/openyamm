#!/usr/bin/env python3
"""Fre's nh_poke.py (../mm9_fre_claude/scripts/nh_poke.py, pass 7 hair poke gate) on a runtime GLB that may be a reduced candidate:
labels (asm row -> part, head piece, weights) come through the installed vertices (every candidate vertex is an installed one, matched
by position + UV per primitive), so before/after read the same vertices the same way. Run from the reduce project folder.
Original docstring follows.
Pass 7 hair poke gate (new head): what shows THROUGH the new hair. The hair (head set faces of piece 'hair' in work/nh/asm_nh.npz) is rigid
on Head; the parts that move against it are the neck (r72's neck band, the new neck's eased rows), the dress/feather collar and the braid.
Per clip at every key and 30 fps, each such vertex that the hair covers at rest (the ray from the hair's centre meets the hair before it,
or it lies within COVER m inside the first hit) is tested again: when it stands beyond the hair's first surface along that ray, it pokes
out. Reports the deepest poke beyond the bind pose's own reading (mm) and the frames with any vertex more than 2 mm out.
Args: <glb> <out json>   (project folder)"""
import sys, json, os
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor')); sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb_pose import Glb, Model
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'mm9_fre_claude' / 'scripts'))
from geo4 import raycast
FRE = Path(__file__).resolve().parents[2] / 'mm9_fre_claude'
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bglbio as gb
from scipy.spatial import cKDTree
M = Model(Glb(sys.argv[1])); A = np.load(FRE / 'work/nh/asm_nh.npz'); OUT = sys.argv[2]
d0, b0 = gb.read(Path(__file__).resolve().parents[1] / 'before' / 'mm9_fre.glb'); P0 = gb.prims(d0, b0, 0)
d1, b1 = gb.read(sys.argv[1]); P1 = gb.prims(d1, b1, next(n for n in d1['nodes'] if n.get('name') == 'Fre' and 'mesh' in n)['mesh'])
names = [str(x) for x in A['names']]; comp, hp, at, am = A['comp'], A['head_piece'], A['tri'], A['mat']
rows = []; T0 = []; off = 0
for m in range(len(M.primitives)):
    used = np.unique(at[am == m]); assert len(used) == len(P0[m]['POSITION'])
    dd, jj = cKDTree(np.c_[P0[m]['POSITION'], P0[m]['TEXCOORD_0'] * 0.01]).query(np.c_[P1[m]['POSITION'], P1[m]['TEXCOORD_0'] * 0.01])
    assert dd.max() < 1e-6, dd.max()
    rows.append(used[jj]); T0.append(M.primitives[m]['triangles'] + off); off += len(jj)
rows = np.concatenate(rows); T0 = np.vstack(T0); cp, hpr = comp[rows], hp[rows]
allpos = lambda p: np.vstack([a for a, _ in p])
hairv = hpr == 1; hairT = T0[hairv[T0].all(1)]
W = np.load(FRE / 'work/nh/weights_nh.npz'); HEAD = [str(x) for x in W['wnames']].index('FHP Head')
headw = np.where(W['wj'][rows] == HEAD, W['ww'][rows], 0).sum(1)
mov = ((hpr == 3) | ((hpr == 0) & (headw < 0.99)) | np.isin(cp, [names.index('dress'), names.index('braid2')]))
rest = allpos(M.skinned_positions(M.world({})))
c0 = rest[hairv].mean(0); cand = np.where(mov & (np.linalg.norm(rest - c0, axis=1) < 0.16))[0]
def poke(pts, idx):
    c = pts[hairv].mean(0); d = pts[idx] - c; r = np.linalg.norm(d, axis=1); u = d / r[:, None]
    t = raycast(c, u, pts, hairT); return np.where(np.isfinite(t), r - t, -1.0)
p0 = poke(rest, cand); test = cand[(p0 > -1.0) & (p0 <= 0)]; B0 = poke(rest, test)
print('TESTED', len(test), 'of', len(cand), 'moving vertices near the hair')
res = {}
for clip in M.clips:
    times = M.clip_times(clip); ts = np.unique(np.r_[times, np.arange(0, times[-1] + 1e-6, 1 / 30)])
    best, at_, n2 = 0.0, None, 0
    for t in ts:
        pts = allpos(M.skinned_positions(M.world(M.sample(clip, t))))
        p = poke(pts, test); e = np.where(p > 0, p - np.maximum(B0, 0), 0).max() if len(test) else 0.0
        if e > best: best, at_ = float(e), round(float(t), 3)
        if e > 0.002: n2 += 1
    res[clip] = {'max_mm': round(best * 1000, 1), 'at_s': at_, 'frames_over_2mm': n2, 'frames': int(len(ts))}
    print(f"{clip:10s} hair poke {res[clip]['max_mm']:5.1f} mm @{at_} ({n2}/{len(ts)} > 2 mm)")
json.dump(res, open(OUT, 'w'), indent=1)
