#!/usr/bin/env python3
"""Measure the installed Winged Mutant LOD0 before reducing: per primitive counts, mirror symmetry (x = 0), wing
back-face copies (same UV triple, 2 mm behind), wing weights by bone class, head face kinds (from the creature's
work/head_v6.npz: 1 skin, 2 eye, 3 hair, 4 tooth, 0 neck bridge). Writes work/glb_labels.npz (per GLB LOD0 face, in
primitive order Wmut, Wmut_Wing, Wmut_Head): prim, kind, back (wing back copy), front_of (back copy -> its front face)."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
g = Glb(sys.argv[1] if len(sys.argv) > 1 else str(HERE / 'before' / 'mm9_wingedmutant.glb'))
m = Model(g); doc = g.json
names = [doc['nodes'][j]['name'] for j in m.joints]
prims = doc['meshes'][0]['primitives']
P, T, UV, J, W = [], [], [], [], []
for p, e in zip(prims, m.primitives):
    P.append(e['positions']); T.append(e['triangles']); UV.append(g.accessor(p['attributes']['TEXCOORD_0']))
    J.append(e['joints']); W.append(e['weights'])
allp = np.vstack(P); size = np.ptp(allp, 0).max()
print('SIZE', np.ptp(allp, 0).round(3), 'tris', [len(t) for t in T])
mir = allp * [-1, 1, 1]; d, _ = cKDTree(allp).query(mir)
print('SYM vertex->mirrored vertex: median %.5f%% p99 %.5f%% max %.5f%%' % tuple(np.percentile(d, [50, 99, 100]) / size * 100))
print('on plane |x|<1e-5:', int((np.abs(allp[:, 0]) < 1e-5).sum()))
# wing back copies
wp, wt, wu = P[1], T[1], UV[1]
key = {}
for i, t in enumerate(wt):
    k = (bool(wp[t, 0].mean() > 0),) + tuple(sorted(tuple(np.round(wu[v], 6)) for v in t))
    key.setdefault(k, []).append(i)
back = np.zeros(len(wt), bool); front_of = -np.ones(len(wt), int)
fn = np.cross(wp[wt[:, 1]] - wp[wt[:, 0]], wp[wt[:, 2]] - wp[wt[:, 0]])
fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
cen = wp[wt].mean(1)
pairs = 0
for k, fs in key.items():
    if len(fs) == 2:
        a, b = fs
        off = cen[b] - cen[a]
        # the back copy lies behind the front along the front normal
        if np.dot(off, fn[a]) < 0:
            back[b] = True; front_of[b] = a
        else:
            back[a] = True; front_of[a] = b
        pairs += 1
print('WING faces', len(wt), 'pairs', pairs, 'back', back.sum(), 'groups>2', sum(len(f) > 2 for f in key.values()))
dd = np.linalg.norm(cen[back] - cen[front_of[back]], axis=1); print('  back offset mm p50/p99/max', np.percentile(dd, [50, 99, 100]).round(5) * 1000)
# wing weights by bone class
def cls(n):
    if not n.startswith('Yw'): return 'other'
    if 'mid' in n: return 'mid'
    if 'piv' in n: return 'piv'
    if n.startswith('Ywingarm'): return 'arm'
    return 'spar'
cl = np.array([cls(n) for n in names])
wv = np.unique(wt[~back])
share = {}
for c in ['spar', 'piv', 'mid', 'arm', 'other']:
    s = (W[1][wv] * (cl[J[1][wv]] == c)).sum(1); share[c] = s
    print(f'  wing front verts {len(wv)} {c}: mean {s.mean():.3f}  verts >0.5 {(s > .5).sum()}  >0.25 {(s > .25).sum()}')
dom = names_dom = np.array(names)[J[1][wv, W[1][wv].argmax(1)]]
u, c = np.unique(dom, return_counts=True); print('  dominant bones', dict(zip(u, c)))
# boundary edges of the front wing sheet
from collections import Counter
ec = Counter(tuple(sorted(e)) for t in wt[~back] for e in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])))
print('  front boundary edges (unwelded)', sum(1 for v in ec.values() if v == 1))
# components of front wing
# head kinds
h = np.load(HERE.parent / 'mm9_wingedmutant_claude' / 'work' / 'head_v6.npz')
hc = h['head_xyz'].mean(1)  # blender z-up
hc_g = np.stack([hc[:, 0], hc[:, 2], -hc[:, 1]], 1)
gc = P[2][T[2]].mean(1)
dist, nn = cKDTree(hc_g).query(gc)
print('HEAD match median %.2e max %.2e unique %d' % (np.median(dist), dist.max(), len(np.unique(nn))))
kind = h['head_kind'][nn]
u, c = np.unique(kind, return_counts=True); print('  head kinds', dict(zip(u.tolist(), c.tolist())))
bridge = h['head_bridge'][nn]; print('  bridge faces', bridge.sum())
# body: dominant bone classes
bv = T[0]
domb = np.array(names)[J[0][bv, W[0][bv].argmax(2)][:, 0] if False else J[0][bv[:, 0], W[0][bv[:, 0]].argmax(1)]]
def bcls(n):
    if 'tail' in n: return 'tail'
    if 'Thigh' in n: return 'thigh'
    if 'Calf' in n: return 'calf'
    if any(s in n for s in ('Foot', 'claw', 'toe', 'Xfoot')): return 'foot'
    if n.startswith('Yw'): return 'wingroot'
    return 'torso'
bc = np.array([bcls(n) for n in domb]); u, c = np.unique(bc, return_counts=True); print('BODY parts', dict(zip(u, c)))
hp = np.full(len(T[2]), -1)
kindall = np.concatenate([np.full(len(T[0]), -1), np.full(len(T[1]), -1), kind])
np.savez(HERE / 'work' / 'glb_labels.npz', prim=np.concatenate([np.full(len(t), i) for i, t in enumerate(T)]),
         kind=kindall, bridge=np.concatenate([np.zeros(len(T[0]) + len(T[1]), int), bridge]),
         back=np.concatenate([np.zeros(len(T[0]), bool), back, np.zeros(len(T[2]), bool)]),
         front_of=np.concatenate([-np.ones(len(T[0]), int), np.where(front_of >= 0, front_of + len(T[0]), -1), -np.ones(len(T[2]), int)]),
         bodypart=np.concatenate([bc, np.full(len(T[1]) + len(T[2]), '')]))
# helper share per front wing face
hv = share['piv'] + share['mid']
hmap = np.zeros(len(wp)); hmap[wv] = hv
ft = wt[~back]
for th in (0.5, 0.75, 0.9):
    print(f'  front faces with any vertex helper>{th}: {(hmap[ft] > th).any(1).sum()}  all: {(hmap[ft] > th).all(1).sum()}  verts {(hv > th).sum()}')
mv = np.zeros(len(wp)); mv[wv] = share['mid']
for th in (0.5, 0.75):
    print(f'  front faces with any vertex mid>{th}: {(mv[ft] > th).any(1).sum()}')
