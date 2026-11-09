#!/usr/bin/env python3
"""Keep / group sets per installed LOD0 face (primitive order PeasantF7_A, PeasantF7Head) for mpqem.py, relaxed keep set for prio-2
townsfolk (REDUCTION_BRIEF_20261104). Part labels from the creature's own build (pf7_parts.py: head, dress, skirt, hair, legs,
hands, bracelets, braids; `inner` = line_rims_pf7.py linings and caps).
Classes: dress, sleeve (dress faces on the upper arms), skirt, skirtin (Meshy's inner hem wall and shin floor), legs, hand (hand and
finger bones), forearm, upperarm (the MPFB arm hidden in the short sleeve), bracelets, head (face, scalp, neck, eyes: one shell),
hair, hairlining (the hair rim's lining), hairlined (hair faces in front of it), braids, cap (zero-UV caps of the dress waist loop
and the arm stubs).
Exact: head, caps, hair lining + lined faces, skirt inner wall, bracelets, soles (leg faces within SOLE m of the floor), skin under
and beside the bracelets (forearm/hand faces within BRACE m of a bracelet face), the neck seam (non-head faces within SEAM m of the
head shell's open border), the hairline (hair/braid faces within HAIRLINE m of the head shell), the sleeve hems (sleeve faces within
HEM m of an open sleeve border), extra keeps (KEEP_EXTRA=a,b: work/<a>.npy).
Groups: 0 dress + skirt (ladder ratio), 1 hand, 2 hair, 3 braids, 4 legs, 5 forearm, 6 upperarm, 7 sleeve, 8 skirt (if SKIRT_G=1).
Usage: make_sets_pf7.py <tag> -> work/glb_sets_<tag>.npz (keep, group, lining, lined, cls, mat), work/classes.json"""
import json
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
from weld import weld_ids  # noqa: E402
E = lambda k, d: os.environ.get(k, d)
tag = sys.argv[1]
SOLE = float(E('SOLE', '0.03')); SEAM = float(E('SEAM', '0.015')); HAIRLINE = float(E('HAIRLINE', '0.006'))
BRACE = float(E('BRACE', '0.012')); HEM = float(E('HEM', '0.012')); SKIRT_G = E('SKIRT_G', '0') == '1'
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantf7.glb', 'PeasantF7')
skin = doc['skins'][nd['skin']]; names = [doc['nodes'][j]['name'] for j in skin['joints']]
PR = ['PeasantF7_A', 'PeasantF7Head']
pp = np.load(HERE / 'work' / 'pf7_parts.npz'); PN = [str(x) for x in pp['names']]; part = pp['part']; inner = pp['inner'].astype(bool)
CLS = ['dress', 'sleeve', 'skirt', 'skirtin', 'legs', 'hand', 'forearm', 'upperarm', 'bracelets', 'head', 'hair', 'hairlining',
       'hairlined', 'braids', 'cap']
HANDJ = np.array([any(k in n for k in ('Hand', 'Finger', 'Index', 'Middle', 'Ring', 'Pinky', 'Thumb')) for n in names])
FOREJ = np.array(['Forearm' in n for n in names]); UPJ = np.array(['UpperArm' in n or 'Clavicle' in n for n in names])
FV = np.concatenate([D[n]['P'][D[n]['T']] for n in PR]); cen = FV.mean(1)
mat = np.concatenate([np.full(len(D[n]['T']), i) for i, n in enumerate(PR)])
Jall = [D[n]['J'] for n in PR]; Wall = [D[n]['W'] for n in PR]
o = 0; cls = np.full(len(part), -1)
pn = lambda f: PN[part[f]]
for k, name in enumerate(PR):
    P, T, J, W = (D[name][x] for x in ('P', 'T', 'J', 'W')); n = len(T); s = slice(o, o + n)
    pa = np.array([PN[x] for x in part[s]]); inn = inner[s]
    wsum = lambda m: (W * m[J]).sum(1)
    hw, fw, uw = wsum(HANDJ)[T].mean(1), wsum(FOREJ)[T].mean(1), wsum(UPJ)[T].mean(1)
    c = np.full(n, -1)
    c[pa == 'dress'] = CLS.index('dress'); c[(pa == 'dress') & (uw > 0.5)] = CLS.index('sleeve')
    c[pa == 'skirt'] = CLS.index('skirt'); c[(pa == 'skirt') & inn] = CLS.index('skirtin')
    c[pa == 'legs'] = CLS.index('legs'); c[pa == 'bracelets'] = CLS.index('bracelets')
    hp = pa == 'hands'
    c[hp] = CLS.index('upperarm'); c[hp & (fw >= uw)] = CLS.index('forearm'); c[hp & (hw > 0.5)] = CLS.index('hand')
    c[pa == 'head'] = CLS.index('head'); c[pa == 'braids'] = CLS.index('braids')
    c[pa == 'hair'] = CLS.index('hair'); c[(pa == 'hair') & inn] = CLS.index('hairlining')
    c[inn & np.isin(pa, ['dress', 'hands'])] = CLS.index('cap')
    if k == 1:
        # hair faces in front of the lining band (a lining face 0.5-6 mm behind, facing the other way)
        Pp, Tt = P, T; cc = Pp[Tt].mean(1)
        fn = np.cross(Pp[Tt[:, 1]] - Pp[Tt[:, 0]], Pp[Tt[:, 2]] - Pp[Tt[:, 0]]); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-20)
        li = np.flatnonzero(c == CLS.index('hairlining')); lt = cKDTree(cc[li])
        for f in np.flatnonzero(c == CLS.index('hair')):
            for j in lt.query_ball_point(cc[f], 0.012):
                g = li[j]; dv = cc[f] - cc[g]
                if np.dot(fn[f], fn[g]) < -0.5 and 0.0003 < np.dot(dv, fn[f]) < 0.006:
                    c[f] = CLS.index('hairlined'); break
        # plus faces whose every vertex coincides with a lining-band position (the shared rim strip)
        lv = cKDTree(Pp[np.unique(Tt[li])])
        near = lv.query(Pp)[0] < 1e-5
        c[(c == CLS.index('hair')) & near[Tt].all(1)] = CLS.index('hairlined')
    assert (c >= 0).all(), np.unique(pa[c < 0])
    cls[s] = c; o += n
C = lambda *ns: np.isin(cls, [CLS.index(x) for x in ns])
for ci, cn in enumerate(CLS):
    print(f'  {cn:10s} {int((cls == ci).sum()):5d}')
keep = C('head', 'cap', 'hairlining', 'hairlined', 'skirtin', 'bracelets')
floor = min(D[n]['P'][:, 1].min() for n in PR)
sole = C('legs') & (FV[:, :, 1].min(1) < floor + SOLE); keep |= sole
brace = C('forearm', 'hand', 'upperarm') & (cKDTree(FV[C('bracelets')].reshape(-1, 3)).query(FV.reshape(-1, 3))[0].reshape(-1, 3).min(1) < BRACE)
keep |= brace
# head shell's open border (neck bottom ring after the caps were dropped, forehead pinhole, skull opening)
P1, T1 = D['PeasantF7Head']['P'], D['PeasantF7Head']['T']; o1 = len(D['PeasantF7_A']['T'])
w1 = weld_ids(P1); FT1 = w1[T1]; hs = C('head')[o1:]
ed = np.sort(np.vstack([FT1[hs][:, [0, 1]], FT1[hs][:, [1, 2]], FT1[hs][:, [2, 0]]]), 1)
u, cc_ = np.unique(ed, axis=0, return_counts=True); rv = np.unique(u[cc_ == 1].ravel())
rep = np.zeros(w1.max() + 1, np.int64); rep[w1] = np.arange(len(P1)); ring = P1[rep[rv]]
dring = cKDTree(ring).query(FV.reshape(-1, 3))[0].reshape(-1, 3).min(1)
seam = ~C('head') & (dring < SEAM); keep |= seam
hd = cKDTree(FV[C('head')].reshape(-1, 3)).query(FV.reshape(-1, 3))[0].reshape(-1, 3).min(1)
hl = C('hair', 'braids') & (hd < HAIRLINE); keep |= hl
# sleeve hems: sleeve faces near an open border of the dress piece (the short sleeves' hems)
P0, T0 = D['PeasantF7_A']['P'], D['PeasantF7_A']['T']; n0 = len(T0); w0 = weld_ids(P0); FT0 = w0[T0]
ds = C('dress', 'sleeve')[:n0]
ed = np.sort(np.vstack([FT0[ds][:, [0, 1]], FT0[ds][:, [1, 2]], FT0[ds][:, [2, 0]]]), 1)
u, cc_ = np.unique(ed, axis=0, return_counts=True); bv = np.unique(u[cc_ == 1].ravel())
rep0 = np.zeros(w0.max() + 1, np.int64); rep0[w0] = np.arange(len(P0))
hem = np.zeros(len(cls), bool)
if len(bv):
    db = cKDTree(P0[rep0[bv]]).query(FV[:n0].reshape(-1, 3))[0].reshape(-1, 3).min(1)
    hem[:n0] = C('sleeve')[:n0] & (db < HEM)
keep |= hem
for nm in [x for x in E('KEEP_EXTRA', '').split(',') if x]:
    ex = np.load(HERE / 'work' / f'{nm}.npy'); keep |= ex; print('extra keep', nm, int(ex.sum()))
lining = np.zeros(len(cls), bool); lined = np.zeros(len(cls), bool)
group = np.zeros(len(cls), int)
for gi, ns in ((1, ('hand',)), (2, ('hair',)), (3, ('braids',)), (4, ('legs',)), (5, ('forearm',)), (6, ('upperarm',)),
               (7, ('sleeve',)), (8, ('skirt',) if SKIRT_G else ())):
    if ns:
        group[C(*ns) & ~keep] = gi
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=lining, lined=lined, cls=cls, mat=mat)
rows = {}
for ci, cn in enumerate(CLS):
    s = cls == ci
    rows[cn] = dict(faces=int(s.sum()), keep=int((s & keep).sum()), free=int((s & ~keep).sum()))
    print(f'{cn:10s} {s.sum():5d} keep {int((s & keep).sum()):5d} free {int((s & ~keep).sum()):5d}')
print('soles', int(sole.sum()), 'bracelet skin', int(brace.sum()), 'neck seam', int(seam.sum()), 'hairline', int(hl.sum()),
      'sleeve hems', int(hem.sum()), 'head ring verts', len(rv), 'dress border verts', len(bv))
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'free', int((~keep).sum()), 'of', len(cls),
      '| groups', {k: int((group[~keep] == k).sum()) for k in range(9)})
(HERE / 'work' / 'classes.json').write_text(json.dumps(dict(names=CLS, rows=rows), indent=1))
