#!/usr/bin/env python3
"""Keep / group / lining sets per installed LOD0 face of Fre (before/mm9_fre.glb, node Fre; prims Fre body, FreHead new head,
FreHair braid) for mpqem.py. Fre's body primitive is PeasantF4's body (same 6,657 vertices on F4's paid UV layout, matched exactly by
UV; positions differ <= 1.7 cm from Fre's geo chain), so its parts come from PeasantF4's accepted reduction sets
(../mm9_peasantf4_reduce_claude/work/glb_sets_<F4SETS>.npz, read only): keep (sleeve-tube rims and caps, job-8 bodice fills, placket
column, F4's painted trims, F1's short sleeves, F1's hidden skirt lining... see that README), groups (1 hands, 3 skirt, 4 sleeve tube
outer, 5 F1 skirt lining, 6 legs, 7 shoulders, 8 MPFB arm, 0 bodice), the sleeve-tube lining faces and their twin map. Fre's own:
- body faces with no F4 twin (51: Fre's bust/placket geometry) are kept;
- soles recomputed on Fre's positions (SOLE m), Fre's own bright painted trims (gold borders, feather collar edge) with TRIM luminance
  on pf_body_final (+ TRIM_RINGS rings), optional;
- FreHead (the new head: face, eyes, lids, hair bob, r72 neck band, bridge) kept whole;
- body faces within NEAR_BRAID m of the braid (its holder at bind for detached_parts_audit's root test) kept, optional;
- FreHair (the braid tube, 459): group 9 (BRAID=1) or kept; its tie/root inside the hair (rest height > BRAID_TOP m) kept.
Usage: make_sets_fre.py <tag>   -> work/glb_sets_<tag>.npz"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as g  # noqa: E402
tag = sys.argv[1]
E = lambda k, d: os.environ.get(k, d)
F4 = HERE.parent / 'mm9_peasantf4_reduce_claude'
d, b = g.read(HERE / 'before' / 'mm9_fre.glb'); prims = g.prims(d, b, 0)
assert [p['material'] for p in prims] == ['Fre', 'FreHead', 'FreHair']
d4, b4 = g.read(F4 / 'before' / 'mm9_peasantf4.glb')
n4 = next(n for n in d4['nodes'] if n.get('name') == 'PeasantF4' and 'mesh' in n); p4 = g.prims(d4, b4, n4['mesh'])
S4 = np.load(F4 / 'work' / f"glb_sets_{E('F4SETS', 'f')}.npz")
B, F = p4[0], prims[0]; nb4 = len(B['T'])
# vertex map Fre body -> F4 body by UV (exact), checked: bijection, same joints
dd, j = cKDTree(B['TEXCOORD_0'].astype(np.float64)).query(F['TEXCOORD_0'].astype(np.float64), 2)
assert dd[:, 0].max() < 1e-7, dd[:, 0].max()
amb = dd[:, 1] < 1e-7                       # several F4 vertices on one UV (lining twins, coincident seams): assign per UV group
j = j[:, 0].copy()
if amb.any():
    from scipy.optimize import linear_sum_assignment
    uk4 = np.round(B['TEXCOORD_0'].astype(np.float64), 7); ukf = np.round(F['TEXCOORD_0'].astype(np.float64), 7)
    feat = lambda p: np.c_[p['POSITION'].astype(np.float64), 0.02 * p['NORMAL'].astype(np.float64), 0.02 * p['WEIGHTS_0'].astype(np.float64)]
    f4, ff = feat(B), feat(F)
    _, g4 = np.unique(uk4, axis=0, return_inverse=True); g4 = g4.ravel()
    gmap = {}
    for i, k in enumerate(map(tuple, uk4)): gmap.setdefault(k, []).append(i)
    fgrp = {}
    for i in np.flatnonzero(amb): fgrp.setdefault(tuple(ukf[i]), []).append(i)
    for k, fi in fgrp.items():
        ci = gmap[k]; C = np.linalg.norm(ff[fi][:, None] - f4[ci][None], axis=-1)
        r, c = linear_sum_assignment(C); j[np.array(fi)[r]] = np.array(ci)[c]
print('UV-ambiguous vertices', int(amb.sum()), 'bijection', len(np.unique(j)) == len(j) == len(B['POSITION']))
assert len(np.unique(j)) == len(j)
inv = -np.ones(len(B['POSITION']), np.int64); inv[j] = np.arange(len(j))
key4 = {tuple(sorted(t)): i for i, t in enumerate(B['T'])}
fm = np.array([key4.get(tuple(sorted(t)), -1) for t in j[F['T']]])
print('body faces matched to F4', int((fm >= 0).sum()), 'of', len(fm))
nf = [len(p['T']) for p in prims]; nv = [len(p['POSITION']) for p in prims]; voff = np.cumsum([0] + nv); foff = np.cumsum([0] + nf)
N = sum(nf)
keep = np.zeros(N, bool); group = np.zeros(N, int); lining = np.zeros(N, bool); lined = np.zeros(N, bool); twin = -np.ones(voff[-1], np.int64)
part = np.zeros(N, int)        # 0 body, 1 head, 2 braid
ok = fm >= 0; fb = np.arange(nf[0])
keep[fb[ok]] = S4['keep'][fm[ok]]; group[fb[ok]] = S4['group'][fm[ok]]
lining[fb[ok]] = S4['lining'][fm[ok]]; lined[fb[ok]] = S4['lined'][fm[ok]]
keep[fb[~ok]] = True
tw4 = S4['twin'][:len(B['POSITION'])]
has = tw4[j] >= 0; twin[np.flatnonzero(has)] = inv[tw4[j[has]]]
# every lining face must still have its lined outer face (else keep it as plain geometry): lining corners are twins of lined corners
tvert = set(twin[twin >= 0].tolist())
lf = np.flatnonzero(lining)
bad = [f for f in lf if not set(F['T'][f].tolist()) <= tvert]
lining[bad] = False; keep[bad] = True
# each lined face's corners must have twins
lb = np.flatnonzero(lined); badl = [f for f in lb if (twin[F['T'][f]] < 0).any()]
print('lining faces', int(lining.sum()), '(dropped to keep', len(bad), ') lined', int(lined.sum()), 'lined without twins', len(badl))
assert not badl
# soles on Fre's own positions
P = F['POSITION'].astype(np.float64); fl = P[:, 1].min(); SOLE = float(E('SOLE', '0.03'))
sole = (group[:nf[0]] == 6) & (P[F['T']][:, :, 1].min(1) < fl + SOLE)
keep[:nf[0]] |= sole; print('soles kept (group 6 within', SOLE, 'm of the floor)', int(sole.sum()))
TRIM = float(E('TRIM', '0'))
if TRIM > 0:
    from PIL import Image
    tone = np.asarray(Image.open(HERE / 'work' / 'tex_pf_body_final.png').convert('RGB'), np.float64); th, tw_ = tone.shape[:2]
    UV = F['TEXCOORD_0'].astype(np.float64)
    Bt = np.array([[1, 1, 1], [4, 1, 1], [1, 4, 1], [1, 1, 4]], float); Bt /= Bt.sum(1, keepdims=True)
    su = np.einsum('sk,fkc->fsc', Bt, UV[F['T']]); c = tone[(su[..., 1] % 1 * th).astype(int), (su[..., 0] % 1 * tw_).astype(int)]
    lum = c.mean(-1).mean(1); gold = ((c[..., 0] > 150) & (c[..., 1] > 110) & (c[..., 2] < 90)).any(1)
    MODE = E('TRIM_MODE', 'gold')
    trim = (group[:nf[0]] == 0) & ~keep[:nf[0]] & ~lining[:nf[0]] & (gold if MODE == 'gold' else lum > TRIM)
    kp = np.round(P, 6); _, tv = np.unique(kp, axis=0, return_inverse=True); tv = tv.ravel(); TV = tv[F['T']]
    for _ in range(int(E('TRIM_RINGS', '0'))):
        hot = np.zeros(tv.max() + 1, bool); hot[TV[trim].ravel()] = True; trim |= (group[:nf[0]] == 0) & ~lining[:nf[0]] & hot[TV].any(1)
    keep[:nf[0]] |= trim; print('Fre trims kept', int(trim.sum()))
NB = float(E('NEAR_BRAID', '0'))
if NB > 0:                       # body faces within NB m of the braid at rest kept: the braid's holder at bind (detached audit root)
    bt = cKDTree(prims[2]['POSITION'].astype(np.float64)); dmin = bt.query(P[F['T']].reshape(-1, 3))[0].reshape(-1, 3).min(1)
    nb = (dmin < NB) & ~lining[:nf[0]]; keep[:nf[0]] |= nb; print('body faces near the braid kept', int(nb.sum()))
# head kept whole
part[foff[1]:foff[2]] = 1; keep[foff[1]:foff[2]] = True
# braid
part[foff[2]:] = 2
H = prims[2]; PH = H['POSITION'].astype(np.float64)
if E('BRAID', '1') == '1':
    group[foff[2]:] = 9
    top = PH[H['T']][:, :, 1].max(1) > float(E('BRAID_TOP', '9'))
    keep[foff[2]:] = top; print('braid faces', nf[2], 'kept at the root', int(top.sum()))
else:
    keep[foff[2]:] = True
group[keep | lining] = 0
for k, nm in enumerate(['body', 'head', 'braid']):
    s = part == k
    print(f'{nm:6s} {s.sum():6d} keep {int((s & keep).sum()):5d} lining {int((s & lining).sum()):4d} lined {int((s & lined).sum()):4d} '
          f'free {int((s & ~keep & ~lining).sum()):5d} groups {dict(zip(*np.unique(group[s & ~keep & ~lining], return_counts=True)))}')
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'lining', int(lining.sum()), 'free', int((~keep & ~lining).sum()), 'of', N)
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep & ~lining, group=group, lining=lining, lined=lined, twin=twin, part=part)
