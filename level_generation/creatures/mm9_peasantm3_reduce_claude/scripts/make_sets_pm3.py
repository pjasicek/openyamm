#!/usr/bin/env python3
"""Keep set and cut groups per installed LOD0 face of PeasantM3 (prim order PeasantM3_A body, PeasantM3Head head set: face
shell, hair shell and the two MPFB hands) for mpqem.py -> work/glb_sets_<tag>.npz (keep, group, lining, lined, band) +
review/sets_<tag>_{body,head,hands}.png (grey cut at the ladder ratio, red kept, green hands, orange hair, purple lined cloth
whose lining is re-emitted, yellow legs). PeasantDM4's make_sets_dm4.py adapted to this body (glb_parts_dm4.py components,
twins_dm4.py pairs and bands; component ids are those of before/mm9_peasantm3.glb).
Exact (keep):
  head set: the whole face shell (100003: face, ears, scalp, neck, mouth caps) and its 3-face piece (100001); the hair shell's
  hairline (hair faces within HAIRLINE of the hair's open rim); the hands' forearm stubs (dominant Forearm: the hand-graft
  junction inside the cuffs).
  body: the neck strip under the head set (component 8, all Neck: the neck seam), body faces within COLLAR_D of the head set,
  soles (within SOLE of the floor), small components (<= SMALL faces), every one-texel face that is not a paired lining (rim
  strips, unmatched linings), every painted face of the twin shells (components 1, 6) that has no outer partner, and the painted
  unlined faces within 6 mm of such an exact lining vertex (no exact lining left behind a cut surface).
Groups: 0 tunic and skirt cloth (ladder ratio), 1 hands + fingers, 2 hair, 4 legs (boots and breeches cuffs below LEG_Y).
Usage: make_sets_pm3.py <tag>   (env overrides of the constants; KEEP_COMPS=7,9 whole components kept; EXTRA=<npy of GLB face indices, prim order> kept as well;
BLOCKS=<npy rest points> body faces within BLOCK_R kept)"""
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio  # noqa: E402
from set_view import views  # noqa: E402
E = lambda k, d: float(os.environ.get(k, d))  # noqa: E731
HAIRLINE = E('HAIRLINE', 0.012); COLLAR_D = E('COLLAR_D', 0.012); SOLE = E('SOLE', 0.012)
SMALL = int(E('SMALL', 80)); LEG_Y = E('LEG_Y', 0.48); KEEP_FOREARM = E('KEEP_FOREARM', 1)
TWIN_COMPS = (1, 6)
BROOCH = int(E('BROOCH_GROUP', 0))   # 0: the brooch (component 8, rigid on Neck) kept whole; 3: cut as group 3
NECK_COMPS = () if BROOCH else (8,)
FACE_COMPS = (100001, 100003); HAIR_COMPS = (100002,); HAND_COMPS = (100000, 100004)
BLOCK_R = E('BLOCK_R', 0.04)   # BLOCKS entries 'file.npy' or 'file.npy:radius'
BLOCKS = [(np.load(x.split(':')[0]), float(x.split(':')[1]) if ':' in x else BLOCK_R) for x in os.environ.get('BLOCKS', '').split(',') if x]
EXTRA = [np.load(x) for x in os.environ.get('EXTRA', '').split(',') if x]
KEEP_COMPS = [int(x) for x in os.environ.get('KEEP_COMPS', '').split(',') if x]   # whole components kept (7 belt, 9 strap/buckle)
tag = sys.argv[1]
doc, b = bglbio.read(HERE / 'before' / 'mm9_peasantm3.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantM3' and 'mesh' in n)
prims = bglbio.prims(doc, b, node['mesh'])
assert [p['material'] for p in prims] == ['PeasantM3_A', 'PeasantM3Head'], [p['material'] for p in prims]
g = np.load(HERE / 'work' / 'glb_parts.npz'); tw = np.load(HERE / 'work' / 'twins.npz')
jn = [str(x) for x in g['jnames']]
nf = [len(p['T']) for p in prims]; off = np.cumsum([0] + nf)
keep = np.zeros(off[-1], bool); group = np.zeros(off[-1], np.int64)
lining, lined, band = tw['lining'].copy(), tw['lined'].copy(), tw['band'].copy()
comp, joint, cen = g['comp'], g['joint'], g['cen']
floor = min(p['POSITION'][:, 1].min() for p in prims)


def boundary_vertices(TF):
    e = np.sort(np.concatenate([TF[:, [0, 1]], TF[:, [1, 2]], TF[:, [2, 0]]]), 1)
    u, c = np.unique(e, axis=0, return_counts=True)
    return np.unique(u[c == 1])


for k, pr in enumerate(prims):
    sl = slice(off[k], off[k + 1]); T = pr['T']; P = pr['POSITION'].astype(float)
    _, tp = np.unique(np.round(P, 6), axis=0, return_inverse=True); tp = tp.ravel(); TF = tp[T]
    X = np.zeros((tp.max() + 1, 3)); X[tp] = P
    c = cen[sl]; cm = comp[sl]; jt = joint[sl]
    kp = np.zeros(len(T), bool); gr = np.zeros(len(T), np.int64)
    ln, ld = lining[sl], lined[sl]
    zero = tw[f'zero_{pr["material"]}']
    sizes = dict(zip(*np.unique(cm, return_counts=True)))
    small = np.array([sizes[x] <= SMALL for x in cm])
    kp |= small & ~ln & ~ld
    if k == 0:
        kp |= c[:, 1] - floor < SOLE
        kp |= np.isin(cm, NECK_COMPS)
        exact_lin = (zero & ~ln) | (np.isin(cm, TWIN_COMPS) & ~ln & ~ld)    # rim strips, unmatched linings and twins
        kp |= exact_lin
        uv = np.unique(TF[exact_lin]); near = np.zeros(tp.max() + 1, bool)
        if len(uv):
            d, _ = cKDTree(X[uv]).query(X, distance_upper_bound=0.006); near = np.isfinite(d)
        kp |= ~zero & ~ld & ~ln & ~np.isin(cm, TWIN_COMPS) & near[TF].any(1)   # painted unlined faces over an exact lining
        hp = prims[1]['POSITION'].astype(float)
        d, _ = cKDTree(hp).query(P); kp |= (d[T] < COLLAR_D).any(1) & ~ln
        gr[c[:, 1] < LEG_Y] = 4
        if BROOCH:
            gr[cm == 8] = 3
        for L, br in BLOCKS:
            dl, _ = cKDTree(L).query(P); kp |= (dl[T] < br).any(1)
    else:
        names = np.array([jn[j] for j in jt])
        hand = np.isin(cm, HAND_COMPS); hair = np.isin(cm, HAIR_COMPS)
        kp |= np.isin(cm, FACE_COMPS) | (zero & ~ln)
        hb = boundary_vertices(TF[hair])
        if len(hb) and HAIRLINE > 0:
            d, _ = cKDTree(X[hb]).query(X); kp |= hair & (d[TF] < HAIRLINE).any(1)
        if KEEP_FOREARM:
            kp |= hand & (np.char.find(names.astype(str), 'Forearm') >= 0)
        gr[hand] = 1; gr[hair] = 2
    kp &= ~ln
    keep[sl] = kp; group[sl] = gr
for x in EXTRA:
    keep[x] = True
keep |= np.isin(comp, KEEP_COMPS)
keep &= ~lining
# a pair with any kept face leaves the re-emission: every face of it (outer and lining) stays exact
pair = tw['pair']
kp_pairs = np.unique(pair[keep & (pair >= 0)])
m = np.isin(pair, kp_pairs) & (pair >= 0)
keep |= m; lining &= ~m; lined &= ~m
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
for c_ in np.unique(comp):
    mm = comp == c_
    print(f'   comp {c_}: {cnt(mm)} keep {cnt(keep & mm)} lining {cnt(lining & mm)} lined {cnt(lined & mm)} free {cnt(mm & ~keep & ~lining)}')
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=lining, lined=lined, band=band)
COL = {0: (150, 150, 150), 1: (40, 200, 40), 2: (240, 140, 30), 3: (60, 90, 230), 4: (220, 210, 60)}
for k, pr in enumerate(prims):
    sl = slice(off[k], off[k + 1]); T = pr['T']; P = pr['POSITION'].astype(float)
    rgb = np.array([COL[int(x)] for x in group[sl]]); rgb[lined[sl] & (group[sl] == 0)] = (170, 110, 200)
    rgb[keep[sl]] = (220, 40, 40)
    vis = ~lining[sl]
    if k == 0:
        views(P, T[vis], rgb[vis], (-0.7, 0.7, -0.01, 1.6), HERE / 'review' / f'sets_{tag}_body.png', size=520)
    else:
        sh = ~np.isin(comp[sl], HAND_COMPS)
        views(P, T[vis & sh], rgb[vis & sh], (-0.15, 0.15, 1.5, 1.82), HERE / 'review' / f'sets_{tag}_head.png', size=420)
        views(P, T[vis & ~sh], rgb[vis & ~sh], (-0.78, 0.78, 0.85, 1.2), HERE / 'review' / f'sets_{tag}_hands.png', size=520)
