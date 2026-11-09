#!/usr/bin/env python3
"""Keep / group sets per installed LOD0 face of one half-orc woman (M=1|2; primitive order body PeasantHOF_A|C, then
PeasantHOFHead) for mpqem.py, written to work/hof$M/glb_sets_<tag>.npz (keep, group, lining, lined, part, mat, twinv, rim).

Parts come from the GLB itself (no pre-GLB mesh is needed): connected pieces welded by position, their dominant joints and
their place. Head primitive: head skin (face, scalp, neck seam: the largest Head piece in front), ears (294-face Head pieces at
the temples), hair shell, braids (Bone07-19 / Ponytail chains, HOF1), kerchief (HOF2: the Head/Ponytail piece with its inner
layer and rim), hands (MPFB, Hand/finger joints). Body: lining twins from lin_twins.py (rim_lining.py's reversed copies on one
dark texel), rim strips (one-texel faces touching an outer rim), skirt/apron (XCOM/x* joints), boots (Foot/Toe), legs
(Calf/Thigh), forearms, the rest of the dress.

Keep exactly (REDUCTION_BRIEF_20261104 relaxed set for prio-2 townsfolk, face exact; REDUCTION_AGENT_TOWNSFOLK.md):
- head skin, ears, kerchief (HOF2: its inner layer is a decimated copy, not a twin) and every head piece not cut on purpose;
- body faces within NECK m of a head-skin vertex (the neck seam and the r10 jaw/neck work), within HEADWEAR m of a hair,
  braid or kerchief vertex (DF rule: nothing pokes through what lies on it), the hand-graft junction (body faces within GRAFT
  m of a hand vertex) and the hands' forearm-weighted stub, soles (SOLE m), pieces of up to SMALL faces;
- rim strips and unmatched one-texel faces, the outer faces within RIMBAND m of a rim vertex (PeasantF8's hem band: the kept
  rim's lining corners came outside a coarser skirt), the outer faces within ORPHAN m of an unmatched lining face;
- MASKB=1: body faces whose UV triangle spans two region-mask classes (PeasantF8: wedges at the armholes).
Groups (MP_GROUPS ratios): 1 hands (fingers), 2 braids, 3 hair shell, 4 boots, 5 legs, 6 forearms, 7 skirt + apron; 0 = the rest
(bodice, shawl, sleeves) at the ladder ratio. Lining twins (role 2) are re-emitted from the surviving lined outer faces.
Usage: M=1 make_sets_phof.py <tag>"""
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
import lin_twins  # noqa: E402
tag = sys.argv[1]; M_ = os.environ['M']; WK = HERE / 'work' / f'hof{M_}'
E = lambda k, d: os.environ.get(k, d)
NECK = float(E('NECK', '0.03')); HEADWEAR = float(E('HEADWEAR', '0.02')); GRAFT = float(E('GRAFT', '0.02'))
SOLE = float(E('SOLE', '0.012')); SMALL = int(E('SMALL', '80')); RIMBAND = float(E('RIMBAND', '0.0'))
ORPHAN = float(E('ORPHAN', '0.015')); CUT_HAIR = E('CUT_HAIR', '1') == '1'; CUT_BRAIDS = E('CUT_BRAIDS', '1') == '1'
names = {0: 'dress', 1: 'hands', 2: 'braids', 3: 'hair', 4: 'boots', 5: 'legs', 6: 'forearms', 7: 'skirt', 8: 'lining',
         9: 'rim', 10: 'head skin', 11: 'ears', 12: 'kerchief', 13: 'small', 14: 'other head'}

doc, b = gb.read(HERE / 'before' / f'mm9_peasanthof{M_}.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantHOF' and 'mesh' in n)
jn = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
prims = gb.prims(doc, b, node['mesh'])
assert 'Head' not in prims[0]['material'] and prims[1]['material'] == 'PeasantHOFHead'


def pieces(P, T):
    _, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
    r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
    _, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
    return lab[FT[:, 0]]


def joint_acc(pr):
    T = pr['T']; J = pr['JOINTS_0'].astype(int); W = pr['WEIGHTS_0'].astype(float)
    acc = np.zeros((len(T), len(jn)))
    for c in range(3):
        for i in range(4):
            np.add.at(acc, (np.arange(len(T)), J[T[:, c], i]), W[T[:, c], i])
    return acc


jidx = lambda *keys: np.array([any(k in x for k in keys) for x in jn])
HANDJ = jidx(' Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
BRAIDJ = jidx('Bone0', 'Bone1', 'Hair_root', 'Ponytail')
SKIRTJ = np.array([x == 'XCOM_skirt' or x.startswith('x') for x in jn])
BOOTJ = jidx('Foot', 'Toe'); LEGJ = jidx('Calf', 'Thigh'); FOREJ = jidx('Forearm')

# ---- head primitive
H = prims[1]; HP = H['POSITION'].astype(float); HT = H['T']; hacc = joint_acc(H); hlab = pieces(HP, HT)
hpart = np.full(len(HT), 14)
for c in np.unique(hlab):
    m = hlab == c; a = hacc[m].sum(0); a /= a.sum(); cen = HP[HT[m]].mean((0, 1)); n = int(m.sum())
    if a[HANDJ | FOREJ].sum() > 0.5:
        p = 1
    elif n == 294 and a[jn.index('Bip01 Head')] > 0.99:
        p = 11
    elif a[BRAIDJ].sum() > 0.5:
        p = 2
    else:
        p = -1
    hpart[m] = p
rest = np.unique(hlab[hpart == -1])
# head skin: the largest remaining piece reaching furthest forward (the face); HOF2's kerchief: the remaining piece with the most
# faces behind the head; HOF1's/HOF2's hair shell: the remaining one
info = sorted(((int((hlab == c).sum()), HP[HT[hlab == c]][..., 2].max(), c) for c in rest), reverse=True)
front = max(info, key=lambda t: t[1])[2]
hpart[hlab == front] = 10
for n, zmax, c in info:
    if c == front:
        continue
    hpart[hlab == c] = 12 if (M_ == '2' and n > 1500) else 3
for c in np.unique(hlab):
    m = hlab == c
    print(f'head piece {c:2d} {m.sum():5d} -> {names[int(hpart[m][0])]}  cen {HP[HT[m]].mean((0, 1)).round(3)}')
handf = hpart == 1
stub = handf & ~(hacc[:, HANDJ].sum(1) > hacc.sum(1) * 0.5)        # forearm-weighted hand faces (the stub inside the cuff)

# ---- body primitive
B = prims[0]; P = B['POSITION'].astype(float); T = B['T']; UV = B['TEXCOORD_0'].astype(float)
J = B['JOINTS_0'].astype(int); W = B['WEIGHTS_0'].astype(float)
role, partner, twinv, zero = lin_twins.find_twins(P, UV, J, W, T)
bacc = joint_acc(B); blab = pieces(P, T)
key = lambda q: tuple(np.round(q, 5)); outer_pos = {key(P[v]) for v in np.unique(T[~zero].ravel())}
nco = np.array([sum(key(P[v]) in outer_pos for v in t) for t in T])
bpart = np.zeros(len(T), int)
for c in np.unique(blab):
    m = blab == c; a = bacc[m].sum(0); a /= a.sum()
    if a[SKIRTJ].sum() > 0.5:
        p = 7
    elif a[BOOTJ].sum() > 0.35:
        p = 4
    elif a[LEGJ].sum() > 0.5:
        p = 5
    elif a[FOREJ].sum() > 0.85:
        p = 6
    else:
        p = 0
    bpart[m] = p
    print(f'body piece {c:2d} {m.sum():5d} -> {names[p]:8s} outer {int((m & (role == 1)).sum()):4d} twins {int((m & (role == 2)).sum()):4d} '
          f'one-texel unmatched {int((m & zero & (role == 0)).sum()):4d} cen {P[T[m]].mean((0, 1)).round(3)}')
rimf = zero & (role == 0) & (nco > 0) & (nco < 3)
orphan = zero & (role == 0) & ~rimf
lining = role == 2
lined = role == 1

V = P[T]
near = lambda pts, r: (cKDTree(pts).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < r) if len(pts) else np.zeros(len(T), bool)
hv = lambda mask: HP[np.unique(HT[mask].ravel())]
keepb = np.zeros(len(T), bool)
why = {}
why['neck'] = near(hv(hpart == 10), NECK)
why['headwear'] = near(hv(np.isin(hpart, (2, 3, 12))), HEADWEAR)
why['graft'] = near(hv(handf), GRAFT)
floor = min(P[:, 1].min(), HP[:, 1].min())
why['sole'] = V[:, :, 1].min(1) < floor + SOLE
cnt = np.bincount(blab); why['small'] = cnt[blab] <= SMALL
why['rim'] = rimf; why['orphan'] = orphan
why['orphan_near'] = near(P[np.unique(T[orphan].ravel())], ORPHAN) & ~zero
if RIMBAND > 0:
    why['rimband'] = near(P[np.unique(T[rimf].ravel())], RIMBAND) & ~lining
if E('MASKB', '0') == '1':
    from PIL import Image
    Mk = np.asarray(Image.open(WK / f"tex_{B['material']}_M.png").convert('RGB'), float) / 255; Hm, Wm = Mk.shape[:2]
    by = np.array([[1, 1, 1], [4, 1, 1], [1, 4, 1], [1, 1, 4], [1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [0, 1, 1], [1, 0, 1]], float)
    by /= by.sum(1, keepdims=True)
    uvs = np.einsum('kc,fcd->fkd', by, UV[T])
    sm = Mk[np.clip((uvs[..., 1] * Hm).astype(int), 0, Hm - 1), np.clip((uvs[..., 0] * Wm).astype(int), 0, Wm - 1)]
    dom = np.where(sm.max(-1) > 0.35, sm.argmax(-1), 3)
    why['maskb'] = np.array([len(set(r)) > 1 for r in dom]) & ~zero
for k, v in why.items():
    keepb |= v
# a kept lined outer face keeps its twin; a kept twin keeps its outer face (the lining is never cut on its own)
k2 = keepb & lining; keepb[partner[k2]] = True
k1 = keepb & lined; keepb[partner[k1]] = True
for k, v in why.items():
    print(f'  keep {k:12s} {int(v.sum()):5d} by part', {names[int(q)]: int((v & (bpart == q) & ~lining).sum()) for q in np.unique(bpart)})

# ---- head keeps and groups
keeph = np.isin(hpart, (10, 11, 12, 14)) | stub
if not CUT_HAIR:
    keeph |= hpart == 3
if not CUT_BRAIDS:
    keeph |= hpart == 2
hcnt = np.bincount(hlab); keeph |= hcnt[hlab] <= SMALL
groupb = bpart.copy(); groupb[keepb | lining] = 0
grouph = np.where(np.isin(hpart, (1, 2, 3)), hpart, 0); grouph[keeph] = 0
partb = np.where(lining, 8, np.where(rimf | orphan, 9, np.where(why['small'], 13, bpart)))
part = np.r_[partb, hpart]
keep = np.r_[keepb & ~lining, keeph]
group = np.r_[groupb, grouph]
L = np.r_[lining, np.zeros(len(HT), bool)]
LD = np.r_[lined, np.zeros(len(HT), bool)]
# every lining face is re-emitted from its outer twin (kept outer faces give back their twins unchanged)
twv = -np.ones((len(part), 3), np.int64); twv[:len(T)] = twinv
for p_ in np.unique(part):
    s = part == p_
    print(f'part {p_:2d} {names[int(p_)]:10s} {s.sum():5d} keep {int((s & keep).sum()):5d} free {int((s & ~keep & ~L).sum()):5d} '
          f're-emitted {int((s & L).sum()):5d} groups', {int(k): int((group[s & ~keep & ~L] == k).sum()) for k in np.unique(group[s & ~keep & ~L])})
prot = int(keep.sum()) + int((lining & keepb).sum())
print(f'TOTAL {len(part)}: kept {int(keep.sum())} ({keep.mean() * 100:.1f} %), lining re-emitted {int(L.sum())}, '
      f'free {int((~keep & ~L).sum())}')
np.savez(WK / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=L, lined=LD,
         part=part, mat=np.r_[np.zeros(len(T), int), np.ones(len(HT), int)], twinv=twv, rim=np.r_[rimf, np.zeros(len(HT), bool)])
