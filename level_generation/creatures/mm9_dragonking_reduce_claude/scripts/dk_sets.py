#!/usr/bin/env python3
"""Per-face keep / group sets on the installed Dragon King LOD0 (primitives DragonKing body, DragonKing_Head) for mpqem.py:
work/glb_sets_<tag>.npz (one entry per GLB face, body faces then head faces; lining/lined all False: the membrane is one
double-sided sheet, no shell twins). The head primitive is kept whole by mpqem (MP_KEPT_PRIMS).
Body keep (faces touching a vertex of):
  neck    within NECK of a head-primitive vertex (the neck seam and the head-set border);
  claw    class 4 (claw / horn / wing claw / tail tip) faces of the class map, whole;
  floor   within FLOOR of the lowest point of any sampled pose of any clip (feet, corpse side, wing tips at the downstroke);
  root    wing attachment: wing (Y*) weight and non-wing weight both above ROOTW;
  helper  helper bones that weight no vertex rigidly (Ydbase*, Ywspanpiv*, Ybpart*) summing >= HELPW;
  tips    rest extremes (TIPS per axis end) and spike/claw tips (angle sum around the vertex < TIPANG degrees);
  extra   any work/keep_<name>.npy (body face mask) named on the command line.
Groups: 0 skin (ladder ratio), 2 wing skin (wing-dominant, not membrane), 3 membrane (class 3).
Usage: dk_sets.py <tag> [extra names...]   env NECK FLOOR ROOTW HELPW TIPS TIPANG"""
import os, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts')); sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
import bglbio as gb
from glb_pose import Glb, Model
from scipy.spatial import cKDTree
tag = sys.argv[1]; extra = sys.argv[2:]
NECK = float(os.environ.get('NECK', '0.15')); FLOOR = float(os.environ.get('FLOOR', '0.05'))
ROOTW = float(os.environ.get('ROOTW', '0.05')); HELPW = float(os.environ.get('HELPW', '0.25'))
TIPS = int(os.environ.get('TIPS', '3')); TIPANG = float(os.environ.get('TIPANG', '250'))
src = HERE / 'before' / 'mm9_dragonking.glb'
doc, b = gb.read(src)
node = next(n for n in doc['nodes'] if n.get('name') == 'DragonKing' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh']); assert [p['material'] for p in pr] == ['DragonKing', 'DragonKing_Head']
fi = np.load(HERE / 'work' / 'face_info.npz'); fcls = fi['fcls']; M = fi['M']; names = [str(n) for n in fi['names']]
body, head = pr
P = body['POSITION'].astype(float); T = body['T']; nf = len(T)
_, tp = np.unique(np.round(P, 6), axis=0, return_inverse=True); tp = tp.reshape(-1)
def faces_of(vmask):
    # by position class, so every GLB copy of a topological vertex counts
    tm = np.zeros(tp.max() + 1, bool); tm[tp[vmask]] = True
    return tm[tp[T]].any(1)
sets = {}
d, _ = cKDTree(head['POSITION'].astype(float)).query(P)
sets['neck'] = faces_of(d < NECK)
sets['claw'] = fcls == 4
m = Model(Glb(str(src))); low = np.zeros(len(P), bool)
for clip in m.clips:
    t1 = m.clip_times(clip)[-1]
    for t in np.append(np.arange(0, t1, 0.1), t1):
        posed = m.skinned_positions(m.world(m.sample(clip, t)))
        lo = min(pz[:, 1].min() for pz, _ in posed)
        low |= posed[0][0][:, 1] < lo + FLOOR
sets['floor'] = faces_of(low)
wing = np.array([n.startswith('Y') for n in names]); ww = M[:, wing].sum(1); nw = M[:, ~wing].sum(1)
sets['root'] = faces_of((ww > ROOTW) & (nw > ROOTW))
helper = np.array([n.startswith(('Ydbase', 'Ywspanpiv', 'Ybpart')) for n in names])
sets['helper'] = faces_of(M[:, helper].sum(1) >= HELPW)
tipv = np.zeros(len(P), bool)
for ax in range(3):
    o = np.argsort(P[:, ax]); tipv[o[:TIPS]] = True; tipv[o[-TIPS:]] = True
# angle sum per topological vertex (tips of spikes and claws: a sharp cone has a small total angle)
TF = tp[T]; ang = np.zeros(tp.max() + 1); bnd = np.zeros(tp.max() + 1, bool)
X = np.zeros((tp.max() + 1, 3)); X[tp] = P
for k in range(3):
    a, b_, c = X[TF[:, k]], X[TF[:, (k + 1) % 3]], X[TF[:, (k + 2) % 3]]
    u, v = b_ - a, c - a
    cs = (u * v).sum(1) / np.maximum(np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1), 1e-20)
    np.add.at(ang, TF[:, k], np.degrees(np.arccos(np.clip(cs, -1, 1))))
E = np.sort(np.r_[TF[:, [0, 1]], TF[:, [1, 2]], TF[:, [2, 0]]], 1); ue, cnt = np.unique(E, axis=0, return_counts=True)
bnd[ue[cnt == 1].ravel()] = True
sharp = (ang < TIPANG) & ~bnd
tipv |= sharp[tp]
sets['tips'] = faces_of(tipv)
for e in extra:
    sets[e] = np.load(HERE / 'work' / f'keep_{e}.npy'); assert len(sets[e]) == nf
keep = np.zeros(nf, bool)
for k, v in sets.items():
    keep |= v; print(f'{k:8s} {int(v.sum()):5d} faces')
print('sharp tip vertices', int(sharp.sum()))
group = np.zeros(nf, np.int64)
wdom = ww[T].mean(1) > 0.5
group[wdom] = 2; group[fcls == 3] = 3
for g in (0, 2, 3):
    print(f'group {g}: {int((group == g).sum())} faces, free {int(((group == g) & ~keep).sum())}')
nh = len(head['T'])
K = np.r_[keep, np.ones(nh, bool)]; Gr = np.r_[group, np.zeros(nh, np.int64)]; Z = np.zeros(nf + nh, bool)
print('KEEP body', int(keep.sum()), 'of', nf, '; protected share of LOD0', round((keep.sum() + nh) / (nf + nh) * 100, 1), '%')
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=K, group=Gr, lining=Z, lined=Z, **{f'set_{k}': v for k, v in sets.items()})
