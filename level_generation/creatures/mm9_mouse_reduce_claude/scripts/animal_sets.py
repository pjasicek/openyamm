#!/usr/bin/env python3
"""Survey + protected share of an installed MM9 animal LOD0 (all primitives of node NODE): work/glb_sets_<tag>.npz.
Exact: small pieces (components other than the largest of their primitive) unless SMALL_FREE=1; head-weighted skin (HEAD_BONES
summed weight > HEAD_W) grown FACE_RING rings; feet (dominant FOOT_BONES) grown FOOT_RING rings; soles (within SOLE m of the floor);
KEEP_PRIMS whole. Prints components, dominant bones with median edge, and the -15 % need.
Usage: animal_sets.py <glb> <node> <tag>  (env HEAD_BONES, FOOT_BONES, HEAD_W, FACE_RING, FOOT_RING, SOLE, SMALL_FREE, KEEP_PRIMS, VERBOSE)"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
E = lambda k, d: os.environ.get(k, d)
glb, NODE, tag = sys.argv[1], sys.argv[2], sys.argv[3]
FACE_RING = int(E('FACE_RING', '2')); FOOT_RING = int(E('FOOT_RING', '1')); SOLE = float(E('SOLE', '0.02'))
HEAD_W = float(E('HEAD_W', '0.5')); SMALL_FREE = E('SMALL_FREE', '0') == '1'; KEEP_PRIMS = [x for x in E('KEEP_PRIMS', '').split(',') if x]
doc, b = gb.read(glb)
node = next(n for n in doc['nodes'] if n.get('name') == NODE and 'mesh' in n)
joints = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
ji = lambda names: [joints.index(n) for n in names if n]
floor = min(p['POSITION'][:, 1].min() for p in gb.prims(doc, b, node['mesh']))
out = {}; tot = 0; totkeep = 0
for pi, pr in enumerate(gb.prims(doc, b, node['mesh'])):
    P, T, J, W = pr['POSITION'].astype(float), pr['T'], pr['JOINTS_0'], pr['WEIGHTS_0'].astype(float)
    nF = len(T); tot += nF
    key = np.round(P, 6); _, wv = np.unique(key, axis=0, return_inverse=True); wv = wv.ravel(); FT = wv[T]; nW = wv.max() + 1
    r_ = np.concatenate([FT[:, 0], FT[:, 1], FT[:, 2]]); c_ = np.concatenate([FT[:, 1], FT[:, 2], FT[:, 0]])
    nc, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(nW, nW)), directed=False)
    fl = lab[FT[:, 0]]; cnt = np.bincount(fl); main = cnt[fl] == cnt.max(); small = ~main
    fw = np.zeros((nF, len(joints)))
    for k in range(3):
        for c in range(4):
            np.add.at(fw, (np.arange(nF), J[T[:, k], c]), W[T[:, k], c])
    fw /= 3; dom = fw.argmax(1); cen = P[T].mean(1)
    el = np.linalg.norm(P[T] - P[T[:, [1, 2, 0]]], axis=2).mean(1)
    print(f'== prim {pi} {pr["material"]}: {nF} faces, bbox {P.min(0).round(3)} {P.max(0).round(3)}, components {nc}')
    if E('VERBOSE', '1') == '1':
        for c in np.argsort(-cnt)[:12]:
            s = fl == c
            bones = np.bincount(dom[s], minlength=len(joints)); top = np.argsort(-bones)[:3]
            print(f'   comp {int(s.sum()):5d} f, cen {cen[s].mean(0).round(3)}, bones {[(joints[t], int(bones[t])) for t in top if bones[t]]}, edge {np.median(el[s])*1000:.1f} mm')
        for n in joints:
            s = dom == joints.index(n)
            if s.sum(): print(f'   dom {n:12s} {int(s.sum()):5d}  median edge {np.median(el[s])*1000:5.1f} mm  main {int((s & main).sum())}')

    def grow(sel, rings):
        sel = sel.copy()
        for _ in range(rings):
            vm = np.zeros(nW, bool); vm[FT[sel].ravel()] = True; sel |= vm[FT].any(1)
        return sel
    headw = fw[:, ji(E('HEAD_BONES', '').split(','))].sum(1)
    head = headw > HEAD_W
    face = grow(head, FACE_RING)
    foot = grow(np.isin(dom, ji(E('FOOT_BONES', '').split(','))), FOOT_RING)
    sole = P[T][:, :, 1].min(1) < floor + SOLE
    keep = face | foot | sole | (small if not SMALL_FREE else np.zeros(nF, bool))
    if pr['material'] in KEEP_PRIMS:
        keep[:] = True
    for name in E('EXTRAS', '').split(','):
        if name:
            k = np.load(HERE / 'work' / f'keep_extra_{name}_p{pi}.npy'); keep |= k
    from collections import Counter
    ec = Counter(tuple(sorted(e)) for t in FT for e in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])))
    bnd = np.zeros(nW, bool)
    for (u, v), c in ec.items():
        if c != 2: bnd[u] = bnd[v] = True
    kv = np.zeros(nW, bool); kv[FT[keep].ravel()] = True
    fv = np.zeros(nW, bool); fv[FT[~keep].ravel()] = True
    movable = fv & ~kv & ~bnd
    print(f'   free-face vertices {int(fv.sum())}, movable (not kept, not on an open/non-manifold edge) {int(movable.sum())} '
          f'-> at most ~{2 * int(movable.sum())} faces removable')
    totkeep += keep.sum()
    print(f'   small {int(small.sum())}, head-w {int(head.sum())} (+rings {int(face.sum())}), feet {int(foot.sum())}, soles {int(sole.sum())}, '
          f'keep {int(keep.sum())}, free {int((~keep).sum())}, mean edge free {np.median(el[~keep])*1000 if (~keep).any() else 0:.1f} mm, kept {np.median(el[keep])*1000 if keep.any() else 0:.1f} mm')
    out.update({f'keep{pi}': keep, f'group{pi}': np.zeros(nF, int), f'face{pi}': face, f'foot{pi}': foot, f'sole{pi}': sole, f'small{pi}': small})
free = tot - totkeep
print(f'TOTAL {tot}: protected share {totkeep / tot * 100:.1f} % ({int(totkeep)}); free {int(free)}; -15 % = {int(round(.15 * tot))} tris = '
      f'{.15 * tot / max(1, free) * 100:.0f} % of the free faces')
nP = len([k for k in out if k.startswith('keep')])
cat = lambda k: np.concatenate([out[f'{k}{i}'] for i in range(nP)])
if tag != '-': np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=cat('keep'), group=cat('group'), lining=np.zeros(tot, bool), lined=np.zeros(tot, bool), **out)
