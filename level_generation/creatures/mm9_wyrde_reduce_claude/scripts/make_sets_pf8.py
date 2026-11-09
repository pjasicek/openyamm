#!/usr/bin/env python3
"""Keep / group sets per installed GLB LOD0 face (work/glb_parts.npz order: PeasantF8_B then PeasantF8Head) for mpqem.py,
written to work/glb_sets_<tag>.npz (keep, group, lining, lined, part, mat, twinv, rim). PeasantF8 parts (uv_tex2.npz):
0 head (face skin, neck, scalp, eyes, teeth), 1 scarf (head cloth, hanging back on Ponytail11/12), 2 dress (bodice, long sleeves),
3 cuffs (over the wrists: the MPFB hand stub sits inside), 4 band (waistband), 5 skirt (with the apron), 6 legs (below the knee,
inside the skirt), 7 hands (MPFB hand, fingers, 6 cm forearm stub), 8 ears (procedural elf ears through the scarf), 9 lining
(skirt lining + hem rim). Adapted from PeasantF1's make_sets_pf1.py (F1 was built from F8's scripts: same lining construction).

The skirt lining (assemble_pf.lining) is the skirt's exact twin: lining face k = skirt face k reversed, every vertex 4 mm in
along the skirt's vertex normal, plus a two-face rim per hem edge. So the lining is not cut on its own: mpqem cuts the skirt and
re-emits the lining from the surviving skirt faces (twinv); the rim is kept exactly.

Keep exactly (REDUCTION_BRIEF_20261104, relaxed set for prio-2 townsfolk, face exact):
- head and ears (the whole head primitive);
- the scarf edge: scarf faces within HOODEDGE m of a head vertex, and within EARC m of an ear vertex (the ears pass through it);
- the collar: dress faces within COLLAR m of a head vertex; the sleeve ends: dress faces within CUFF m of a cuff vertex;
- the cuffs (CUFFS=keep) or group 6 (CUFFS=cut); the waistband (BAND=keep) or group 8 (BAND=cut);
- the hand stub (forearm-weighted hand faces, STUB=keep: F6 cut its stub and the vertices came through the sleeve at rest);
- soles: leg faces below floor + SOLE; connected pieces of up to SMALL faces; the lining rim.
Groups: 1 hand + fingers (seam slides), 2 scarf, 3 skirt (lined), 4 shoes (below SHOE m), 5 forearm stub, 6 cuffs, 7 hidden legs
(above SHOE m, inside the skirt), 8 band; 0 = dress (the ladder ratio).
Usage: make_sets_pf8.py <tag>"""
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
tag = sys.argv[1]
E = lambda k, d: os.environ.get(k, d)
HEAD, SCARF, DRESS, CUFFS, BAND, SKIRT, LEGS, HANDS, EARS, LINING = range(10)
HOODEDGE = float(E('HOODEDGE', '0.008')); EARC = float(E('EARC', '0.012')); COLLAR = float(E('COLLAR', '0.01'))
CUFF = float(E('CUFF', '0.012')); SOLE = float(E('SOLE', '0.012')); SHOE = float(E('SHOE', '0.14')); SMALL = int(E('SMALL', '80'))
SLV = float(E('SLEEVE', '0')); KCUFFS = E('CUFFS', 'keep') == 'keep'; KBAND = E('BAND', 'keep') == 'keep'
KSTUB = E('STUB', 'keep') == 'keep'
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantf8.glb', 'PeasantF8')
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']; jn = g['jnames']; joint = g['joint']; src = g['src']
PR = ['PeasantF8_B', 'PeasantF8Head']
P = np.concatenate([D[k]['P'] for k in PR]); offs = np.cumsum([0] + [len(D[k]['P']) for k in PR])
T = np.concatenate([D[k]['T'] + offs[i] for i, k in enumerate(PR)])
assert len(T) == len(part)
floor = P[:, 1].min()
V = P[T]
pv = lambda *n: np.unique(T[np.isin(part, n)].ravel())
near = lambda pts, r: cKDTree(P[pts]).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < r
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
keep = np.isin(part, (HEAD, EARS))
hood_edge = (part == SCARF) & near(pv(HEAD), HOODEDGE)
ear_contact = (part == SCARF) & near(pv(EARS), EARC)
collar = (part == DRESS) & near(pv(HEAD), COLLAR); cuff = (part == DRESS) & near(pv(CUFFS), CUFF)
sole = (part == LEGS) & (V[:, :, 1].min(1) < floor + SOLE)
sleeve = (part == DRESS) & (np.abs(V[:, :, 0]).min(1) > SLV) if SLV > 0 else np.zeros(len(T), bool)
handj = np.array([any(t in str(x) for t in (' Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) for x in jn])
stub = (part == HANDS) & ~handj[joint]
HOODHEM = float(E('HOODHEM', '0'))
hood_hem = np.zeros(len(T), bool)
if HOODHEM > 0:
    from collections import Counter
    ec = Counter(); ac = Counter()
    for f in range(len(T)):
        for a, b in ((0, 1), (1, 2), (2, 0)):
            e = tuple(sorted(w[T[f]][[a, b]].tolist())); ac[e] += 1
            if part[f] == SCARF:
                ec[e] += 1
    bv = np.unique([v for e, c in ec.items() if c == 1 and ac[e] == 1 for v in e])
    rep = np.zeros(w.max() + 1, int); rep[w] = np.arange(len(P))
    hood_hem = (part == SCARF) & near(rep[bv], HOODHEM)
    print('scarf hem open-boundary positions', len(bv), 'faces', int(hood_hem.sum()))
keep |= hood_edge | ear_contact | collar | cuff | sole | sleeve | hood_hem
# MASKB=1 (ladder b): dress faces whose UV triangle spans two region-mask classes (bodice R / sleeves B / unmasked trims and
# embroidery): a50 pulled a dark bodice wedge onto the sleeve at both armholes (review/crop_chest_c0_a50.png)
maskb = np.zeros(len(T), bool)
if E('MASKB', '0') == '1':
    from PIL import Image
    Mk = np.asarray(Image.open(HERE / 'work' / 'tex_PeasantF8_B_M.png').convert('RGB'), float) / 255; Hm, Wm = Mk.shape[:2]
    by = np.array([[1, 1, 1], [4, 1, 1], [1, 4, 1], [1, 1, 4], [1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [0, 1, 1], [1, 0, 1]], float)
    by /= by.sum(1, keepdims=True); UB = D['PeasantF8_B']['UV']; TBm = D['PeasantF8_B']['T']
    uvs = np.einsum('kc,fcd->fkd', by, UB[TBm])
    sm = Mk[np.clip((uvs[..., 1] * Hm).astype(int), 0, Hm - 1), np.clip((uvs[..., 0] * Wm).astype(int), 0, Wm - 1)]
    dom = np.where(sm.max(-1) > 0.35, sm.argmax(-1), 3)
    mixed = np.array([len(set(r)) > 1 for r in dom])
    maskb[:len(TBm)] = mixed & (part[:len(TBm)] == DRESS)
    print('mask-border dress faces', int(maskb.sum()))
keep |= maskb
if KCUFFS:
    keep |= part == CUFFS
if KBAND:
    keep |= part == BAND
if KSTUB:
    keep |= stub
# connected pieces (welded by position)
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl); small = cnt[fl] <= SMALL; keep |= small & (part != LINING)
for p_ in np.unique(part):
    s = part == p_; sz = np.bincount(fl[s]); print(f'  part {p_} pieces {sorted(sz[sz > 0].tolist(), reverse=True)[:12]}')

# ---- skirt -> lining twins (body primitive only, local indices)
s = np.load(HERE.parent / 'mm9_peasantf8_claude' / 'work' / 'uv_tex2.npz')
stri = s['tri']; sco = s['co'][:, [0, 2, 1]] * [-1, 1, -1]          # glb_parts' frame (x mirrored, y up)
sp = s['comp'][stri[:, 0]]; S_ = np.flatnonzero(sp == SKIRT); L_ = np.flatnonzero(sp == LINING)
s2l = {int(a): int(b) for a, b in zip(S_, L_[:len(S_)])}           # npz skirt face k -> npz lining face k (reversed)
nb = len(D['PeasantF8_B']['T']); TB = D['PeasantF8_B']['T']; PB = D['PeasantF8_B']['P']
bpart = part[:nb]; bsrc = src[:nb]
key = lambda q: tuple(np.round(q, 5))
lin_by_pos = {}
for f in np.flatnonzero(bpart == LINING):
    lin_by_pos.setdefault(frozenset(key(PB[v]) for v in TB[f]), []).append(int(f))
twinv = -np.ones((nb, 3), np.int64); twinf = -np.ones(nb, np.int64); bad = 0; resid = []; taken = set()
for f in np.flatnonzero(bpart == SKIRT):
    ns = int(bsrc[f]); nl = s2l[ns]
    # npz skirt corner j at the GLB corner k (exact positions); npz lining corner of skirt corner j is 2 - j
    js = [int(np.argmin(np.linalg.norm(sco[stri[ns]] - PB[TB[f, k]], axis=1))) for k in range(3)]
    want = [sco[stri[nl][2 - j]] for j in js]
    cands = sorted(lin_by_pos.get(frozenset(key(q) for q in want), []), key=lambda lf: lf in taken)
    best = None
    for lf in cands:
        corner = [int(np.argmin(np.linalg.norm(PB[TB[lf]] - q, axis=1))) for q in want]
        e = max(np.linalg.norm(PB[TB[lf, c]] - q) for c, q in zip(corner, want))
        if len(set(corner)) == 3 and (best is None or e < best[0] - 1e-9):
            best = (e, lf, corner)
    if best is None or best[0] > 1e-5:
        bad += 1; continue
    resid.append(best[0]); twinf[f] = best[1]; twinv[f] = TB[best[1], best[2]]; taken.add(best[1])
used = np.zeros(nb, bool); used[twinf[twinf >= 0]] = True
rim = (bpart == LINING) & ~used
print('twins: skirt faces', int((bpart == SKIRT).sum()), 'matched', int((twinf >= 0).sum()), 'unmatched', bad,
      'max corner residual', max(resid) if resid else None, '| lining faces twinned', int(used.sum()), 'rim', int(rim.sum()),
      '| lining faces used twice', int(len(twinf[twinf >= 0]) - len(np.unique(twinf[twinf >= 0]))))
assert bad == 0
# offset check: lining corner 4 mm from its skirt corner
dd = np.linalg.norm(PB[twinv[twinf >= 0]] - PB[TB[twinf >= 0]], axis=2)
print('twin offset mm min', dd.min() * 1000, 'max', dd.max() * 1000)

rimF = np.zeros(len(T), bool); rimF[:nb] = rim
# HEMBAND m (set c): skirt faces with a corner within HEMBAND of the lining's hem rim are kept (and their lining twins with them):
# a50 cut them and the kept rim's lining corners came 6.6 mm outside the coarser skirt at rest, 35 mm in Death (lining_probe.py);
# PeasantF6 c60 had the same at the hem (23 mm in Running) and kept its hem band
HEMBAND = float(E('HEMBAND', '0'))
hemband = np.zeros(len(T), bool)
if HEMBAND > 0:
    hemband = (part == SKIRT) & near(np.unique(T[:nb][rim].ravel()), HEMBAND)
    print('hem band skirt faces', int(hemband.sum()))
lining = np.zeros(len(T), bool); lining[:nb] = (bpart == LINING) & used
lined = part == SKIRT
keep |= rimF | hemband
group = np.zeros(len(T), int)
group[(part == HANDS) & handj[joint]] = 1; group[stub] = 5
group[part == SCARF] = 2; group[part == SKIRT] = 3; group[part == CUFFS] = 6; group[part == BAND] = 8
low = V[:, :, 1].max(1) < floor + SHOE
group[(part == LEGS) & low] = 4; group[(part == LEGS) & ~low] = 7
group[keep] = 0
names = g['names']
for p_ in np.unique(part):
    m = part == p_
    print(f'part {p_} {names[p_]:7s} {m.sum():5d} keep {int((m & keep).sum()):5d} free {int((m & ~keep & ~lining).sum()):5d} '
          f're-emitted {int((m & lining).sum()):5d} groups',
          {int(k): int((group[m & ~keep & ~lining] == k).sum()) for k in np.unique(group[m & ~keep & ~lining])})
print('ear contact', int((ear_contact & ~hood_edge).sum()), 'stub', int(stub.sum()), 'scarf hem', int((hood_hem & ~hood_edge).sum()), 'hood edge', int(hood_edge.sum()), 'collar', int(collar.sum()), 'cuff', int(cuff.sum()), 'sleeves', int(sleeve.sum()),
      'soles', int(sole.sum()), 'small', int((small & (part != LINING)).sum()), 'rim', int(rimF.sum()))
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'lining (follows the skirt)', int(lining.sum()),
      'free', int((~keep & ~lining).sum()), 'of', len(T))
twv = -np.ones((len(T), 3), np.int64); twv[:nb] = twinv
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=lining, lined=lined, part=part, mat=g['mat'],
         twinv=twv, rim=rimF)
