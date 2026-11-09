#!/usr/bin/env python3
"""Keep set and cut groups per installed LOD0 face (prim order PeasantDM4 body, PeasantDM4Head head + MPFB hands) for mpqem.py
-> work/glb_sets_<tag>.npz (keep, group, lining, lined, band) + review/sets_<tag>_{body,head}.png (flat views: grey cut at the
ladder ratio, red kept, green hands, orange hair/beard, blue cap, purple re-emitted lining's outer side, yellow legs).
Labels: work/glb_parts.npz (glb_parts_dm4.py: components, dominant joints), work/twins.npz (twins_dm4.py: lining pairs, bands).
Exact (keep): the face skin window on the head shell (|x| < FACE_X, FACE_Y0 < y < FACE_Y1, z > FACE_Z: eyes, brows, nose,
cheeks, moustache, lips; dilated RING rings), the neck-cap twins component, eyes/one-texel head faces, beard faces within
BEARD_D of the body (the beard's contact with the chest), body faces within COLLAR_D of the head set (collar under the beard),
the hands' forearm stubs (dominant Forearm: the hand-graft junction and stub caps inside the cuffs), soles (body faces within
SOLE of the floor), small components (<= SMALL faces), every one-texel body face that is not a paired lining (rim strips,
unmatched linings) and the painted faces within 6 mm of such an unmatched lining vertex (so no exact lining is left behind a
cut surface). Groups: 0 body cloth (ladder ratio), 1 hands + fingers, 2 hair + beard, 3 cap (lining re-emitted), 4 legs
(trousers and boots below LEG_Y). Usage: make_sets_dm4.py <tag>   (env overrides of the constants)"""
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio  # noqa: E402
from set_view import views  # noqa: E402
E = lambda k, d: float(os.environ.get(k, d))  # noqa: E731
FACE_X, FACE_Y0, FACE_Y1, FACE_Z = E('FACE_X', 0.078), E('FACE_Y0', 0.962), E('FACE_Y1', 1.078), E('FACE_Z', 0.02)
RING = int(E('RING', 1)); BEARD_D = E('BEARD_D', 0.02); COLLAR_D = E('COLLAR_D', 0.012); SOLE = E('SOLE', 0.012)
SMALL = int(E('SMALL', 80)); LEG_Y = E('LEG_Y', 0.30); KEEP_FOREARM = E('KEEP_FOREARM', 1)
# error locks: rest points (glTF, .npy) whose head-shell faces within LOCK_R stay exact (beard_culprits.py: beard edges that
# stretched past the installed maximum)
LOCKS = [np.load(x) for x in os.environ.get('LOCKS', '').split(',') if x]; LOCK_R = E('LOCK_R', 0.03)
# body error locks (BLOCKS, .npy rest points): body faces within BLOCK_R stay exact (arm gate: a re-emitted lining face read as
# the surface the Running forearm is inside of)
BLOCKS = [np.load(x) for x in os.environ.get('BLOCKS', '').split(',') if x]; BLOCK_R = E('BLOCK_R', 0.04)
tag = sys.argv[1]
doc, b = bglbio.read(HERE / 'before' / 'mm9_peasantdm4.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantDM4' and 'mesh' in n)
prims = bglbio.prims(doc, b, node['mesh'])
g = np.load(HERE / 'work' / 'glb_parts.npz'); tw = np.load(HERE / 'work' / 'twins.npz')
jn = [str(x) for x in g['jnames']]
nf = [len(p['T']) for p in prims]; off = np.cumsum([0] + nf)
keep = np.zeros(off[-1], bool); group = np.zeros(off[-1], np.int64)
lining, lined, band = tw['lining'].copy(), tw['lined'].copy(), tw['band'].copy()
comp, joint, cen = g['comp'], g['joint'], g['cen']
floor = min(p['POSITION'][:, 1].min() for p in prims)


for k, pr in enumerate(prims):
    sl = slice(off[k], off[k + 1]); T = pr['T']; P = pr['POSITION'].astype(float)
    _, tp = np.unique(np.round(P, 6), axis=0, return_inverse=True); tp = tp.ravel(); TF = tp[T]
    c = cen[sl]; cm = comp[sl]; jt = joint[sl]
    kp = np.zeros(len(T), bool); gr = np.zeros(len(T), np.int64)
    ln, ld = lining[sl], lined[sl]
    zero = tw[f'zero_{pr["material"]}']
    sizes = dict(zip(*np.unique(cm, return_counts=True)))
    small = np.array([sizes[x] <= SMALL for x in cm])
    kp |= small & ~ln & ~ld
    if k == 0:
        kp |= c[:, 1] - floor < SOLE
        kp |= zero & ~ln                                       # rim strips, unmatched linings
        uv = np.unique(TF[zero & ~ln]); X = np.zeros((tp.max() + 1, 3)); X[tp] = P
        near = np.zeros(tp.max() + 1, bool)
        if len(uv):
            d, _ = cKDTree(X[uv]).query(X, distance_upper_bound=0.006); near = np.isfinite(d)
        kp |= ~zero & ~ld & ~ln & near[TF].any(1)              # painted unlined faces over an exact lining
        hp = prims[1]['POSITION'].astype(float)
        d, _ = cKDTree(hp).query(P); kp |= (d[T] < COLLAR_D).any(1) & ~ln
        gr[c[:, 1] < LEG_Y] = 4
        for L in BLOCKS:
            dl, _ = cKDTree(L).query(P); kp |= (dl[T] < BLOCK_R).any(1)
    else:
        names = np.array([jn[j] for j in jt])
        hand = np.isin(cm, [100000, 100005]); shell = cm == 100001; neck = cm == 100002; cap = np.isin(cm, [100003, 100004])
        fx = shell & (np.abs(c[:, 0]) < FACE_X) & (c[:, 1] > FACE_Y0) & (c[:, 1] < FACE_Y1) & (c[:, 2] > FACE_Z)
        for _ in range(RING):
            vv = np.zeros(tp.max() + 1, bool); vv[TF[fx].ravel()] = True; fx = shell & vv[TF].any(1)
        kp |= fx | neck | (zero & ~ln)
        bp = prims[0]['POSITION'].astype(float)
        d, _ = cKDTree(bp).query(P); kp |= shell & (d[T] < BEARD_D).any(1)
        for L in LOCKS:
            if len(L):
                dl, _ = cKDTree(L).query(P); kp |= shell & (dl[T] < LOCK_R).any(1)
        if KEEP_FOREARM:
            kp |= hand & (np.char.find(names.astype(str), 'Forearm') >= 0)
        gr[hand] = 1; gr[shell] = 2; gr[cap] = 3
    kp &= ~ln
    keep[sl] = kp; group[sl] = gr
# a pair with any kept face leaves the re-emission: every face of it (outer and lining) stays exact
pair = tw['pair']
kp_pairs = np.unique(pair[keep & (pair >= 0)])
m = np.isin(pair, kp_pairs) & (pair >= 0)
keep |= m; lining &= ~m; lined &= ~m
# a lining face whose outer face was not re-emittable: the unmatched case above keeps it; check every lining has a lined
# partner left in its band
for k, pr in enumerate(prims):
    sl = slice(off[k], off[k + 1])
    lb = set(np.unique(band[sl][lining[sl]]).tolist()); db = set(np.unique(band[sl][lined[sl]]).tolist())
    assert lb <= db, (pr['material'], lb - db)
group[keep] = 0
cnt = lambda m: int(m.sum())  # noqa: E731
print('SETS', tag, 'faces', off[-1], 'keep', cnt(keep), f'({100 * keep.mean():.1f} %)', 'lining (re-emitted)', cnt(lining),
      'lined', cnt(lined), 'groups', {int(x): cnt(~keep & ~lining & (group == x)) for x in np.unique(group)})
for k, pr in enumerate(prims):
    sl = slice(off[k], off[k + 1])
    print(' ', pr['material'], 'keep', cnt(keep[sl]), 'lining', cnt(lining[sl]), 'lined', cnt(lined[sl]),
          {int(x): cnt(~keep[sl] & ~lining[sl] & (group[sl] == x)) for x in np.unique(group[sl])})
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=lining, lined=lined, band=band)
COL = {0: (150, 150, 150), 1: (40, 200, 40), 2: (240, 140, 30), 3: (60, 90, 230), 4: (220, 210, 60)}
for k, pr in enumerate(prims):
    sl = slice(off[k], off[k + 1]); T = pr['T']; P = pr['POSITION'].astype(float)
    rgb = np.array([COL[int(x)] for x in group[sl]]); rgb[lined[sl] & (group[sl] == 0)] = (170, 110, 200)
    rgb[keep[sl]] = (220, 40, 40)
    vis = ~lining[sl]
    if k == 0:
        views(P, T[vis], rgb[vis], (-0.55, 0.55, -0.01, 1.0), HERE / 'review' / f'sets_{tag}_body.png', size=520)
    else:
        sh = np.isin(comp[sl], [100001, 100002, 100003, 100004])
        views(P, T[vis & sh], rgb[vis & sh], (-0.15, 0.15, 0.83, 1.25), HERE / 'review' / f'sets_{tag}_head.png', size=420)
        views(P, T[vis & ~sh], rgb[vis & ~sh], (-0.72, 0.72, 0.5, 0.75), HERE / 'review' / f'sets_{tag}_hands.png', size=520)
