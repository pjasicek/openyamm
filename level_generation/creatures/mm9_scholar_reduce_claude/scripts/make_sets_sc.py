#!/usr/bin/env python3
"""Keep / group sets per installed GLB LOD0 face (work/glb_parts.npz order: Scholar_A then ScholarHead) for mpqem.py, written to
work/glb_sets_<tag>.npz (keep, group, lining, lined, part, mat, twinv, rim). Scholar copy of the Wyrde's make_sets_wy.py (the
Scholar's linings are linings_wy.py's too). Parts (glb_parts.py): 0 robe (with stole, sleeves), 1 head (face shell, eyes, neck),
2 hair (hair + beard shell), 3 cap, 4 jewel (chain beads, medallion, buckle), 5 legs (low shoes + shin stub), 6 hands (MPFB,
forearm stub).

Linings (linings_wy.py): every lining face is its outer face reversed, each corner 2 mm behind along the asm normal with the outer
corner's UV and weights, plus two-face rim strips at the open edges. Matched here by UV and position (twin corner = lining vertex
with the outer corner's UV within OFF m); mpqem cuts the outer cloth and re-emits the lining from the surviving lined faces
(twinv); rim strips are kept exactly. Lined and unlined faces of one part go into separate groups (their border stays).

Keep exactly (REDUCTION_AGENT_TOWNSFOLK: relaxed set, face exact):
- the face: the whole head part (face shell skin, lips, ears under the hair, eyes, neck);
- the hairline and the beard edge: hair faces on the outer hair shell's open boundary plus HRINGS rings, and hair faces within
  FACEEDGE m of a head-part vertex (moustache over the lips);
- the collar: body faces within COLLAR m of a head-part vertex (the neck seam);
- hand-in-sleeve: the forearm stub (forearm-weighted hand faces) and robe faces within CUFF m of a hand vertex (sleeve ends);
- the jewellery (JEWEL=keep) and cloth faces within JEWELC m of it (beads and medallion sit on the stole);
- region-mask border faces (MASKB=1: a body face whose UV triangle spans two classes of R robe blue / unmasked stole, trim);
- hand contact (HANDC=<npy> from hand_contact.py: robe faces the resting hands touch in any frame);
- soles: leg faces within SOLE m of the floor; pieces of up to SMALL faces; lining rim strips.
Groups: 1 hands + fingers, 2 hair unlined, 3 hair lined, 4 robe lined, 5 cap, 6 shoes (below SHOE m above the floor),
7 hidden shins, 0 = robe (the ladder ratio).
Usage: make_sets_sc.py <tag>"""
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
ROBE, HEAD, HAIR, CAP, JEWEL, LEGS, HANDS = range(7)
FACEEDGE = float(E('FACEEDGE', '0.012')); COLLAR = float(E('COLLAR', '0.01')); CUFF = float(E('CUFF', '0.02'))
SOLE = float(E('SOLE', '0.012')); SHOE = float(E('SHOE', '0.06')); HRINGS = int(E('HRINGS', '1')); SMALL = int(E('SMALL', '80')); JEWELC = float(E('JEWELC', '0.006'))
OFF = float(E('OFF', '0.0035'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_scholar.glb', 'Scholar')
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']; jn = g['jnames']; joint = g['joint']; inner = g['inner']; sub = g['sub']
PR = ['Scholar_A', 'ScholarHead']
P = np.concatenate([D[k]['P'] for k in PR]); UVa = np.concatenate([D[k]['UV'] for k in PR]); offs = np.cumsum([0] + [len(D[k]['P']) for k in PR])
T = np.concatenate([D[k]['T'] + offs[i] for i, k in enumerate(PR)])
mat = np.r_[np.zeros(len(D[PR[0]]['T']), int), np.ones(len(D[PR[1]]['T']), int)]
assert len(T) == len(part)
nb = len(D[PR[0]]['T'])
floor = P[:, 1].min()
V = P[T]
near = lambda pts, r: cKDTree(P[pts]).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < r
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1

# ---- linings: twin faces (inner, matched to an outer face) and rim strips (inner, unmatched)
twinf = -np.ones(len(T), np.int64); twinv = -np.ones((len(T), 3), np.int64)
uvkey = lambda f: frozenset(tuple(np.round(UVa[v], 5)) for v in T[f])
outer_by_uv = {}
for f in np.flatnonzero(~inner):
    outer_by_uv.setdefault((mat[f], uvkey(f)), []).append(int(f))
resid = []; twice = np.zeros(len(T), bool)
for lf in np.flatnonzero(inner):
    best = None
    for of in outer_by_uv.get((mat[lf], uvkey(lf)), []):
        # each outer corner -> the lining corner with the same UV, nearest in position
        cs = []
        for v in T[of]:
            same = [u for u in T[lf] if np.allclose(UVa[u], UVa[v], atol=1e-5)]
            if not same:
                break
            u = min(same, key=lambda u: np.linalg.norm(P[u] - P[v])); cs.append((u, np.linalg.norm(P[u] - P[v])))
        if len(cs) < 3 or len({c[0] for c in cs}) < 3:
            continue
        e = max(c[1] for c in cs)
        if e <= OFF and (best is None or e < best[0]):
            best = (e, of, [c[0] for c in cs])
    if best is None:
        continue
    if twinf[best[1]] >= 0:
        twice[best[1]] = True; print('outer face with two linings', best[1], '(kept, the second lining stays as a rim face)'); continue
    twinf[best[1]] = lf; twinv[best[1]] = best[2]; resid.append(best[0])
lining = np.zeros(len(T), bool); lining[twinf[twinf >= 0]] = True
rim = inner & ~lining
lined = twinf >= 0
print('linings: inner', int(inner.sum()), 'twins', int(lining.sum()), 'rim', int(rim.sum()), 'offset mm min/max',
      round(min(resid) * 1000, 2), round(max(resid) * 1000, 2))
for p_ in range(7):
    print(f'  part {p_} lined outer {int((lined & (part == p_)).sum())} twins {int((lining & (part == p_)).sum())} rim {int((rim & (part == p_)).sum())}')
# winding check: lining normal opposite to its outer
fn = lambda f: np.cross(P[T[f, 1]] - P[T[f, 0]], P[T[f, 2]] - P[T[f, 0]])
lo = np.flatnonzero(lined)
dots = np.einsum('ij,ij->i', np.array([fn(f) for f in lo]), np.array([fn(twinf[f]) for f in lo]))
print('  twin winding reversed', int((dots < 0).sum()), 'of', len(lo), '; the others are kept with their outer face')
odd = lo[dots >= 0]; twice[odd] = True
lining[twinf[odd]] = False; twinf[odd] = -1; twinv[odd] = -1
rim = inner & ~lining; lined = twinf >= 0

# ---- keep sets
pv = lambda m: np.unique(T[m].ravel())
headp = part == HEAD
face = headp.copy()
# hair boundary (outer shell open edges, by welded position) + HRINGS rings, and hair near the face skin
hairo = (part == HAIR) & ~inner
ec = {}
for f in np.flatnonzero(hairo):
    t = FT[f]
    for a_, b_ in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
        ec.setdefault((min(a_, b_), max(a_, b_)), []).append(f)
bv = np.zeros(n, bool)
for (a_, b_), fs in ec.items():
    if len(fs) == 1:
        bv[a_] = bv[b_] = True
hl = hairo & bv[FT].any(1)
for _ in range(HRINGS):
    vv = np.zeros(n, bool); vv[FT[hl].ravel()] = True; hl = hairo & vv[FT].any(1)
hairline = hl | ((part == HAIR) & ~inner & near(pv(headp), FACEEDGE))
collar = ~headp & (part != HAIR) & near(pv(headp), COLLAR)
handj = np.array([any(t in str(x) for t in (' Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Finger', 'Zfing', 'Zhand')) for x in jn])
stub = (part == HANDS) & ~handj[joint]
cuff = (part == ROBE) & near(pv(part == HANDS), CUFF)
jewel = (part == JEWEL) if E('JEWEL', 'keep') == 'keep' else np.zeros(len(T), bool)
jcont = (part != JEWEL) & ~headp & (part != HAIR) & near(pv(part == JEWEL), JEWELC)
sole = (part == LEGS) & (V[:, :, 1].min(1) < floor + SOLE)
handc = np.zeros(len(T), bool)
if E('HANDC', ''):
    handc = np.load(HERE / E('HANDC', '')) & (part == ROBE)
maskb = np.zeros(len(T), bool)
if E('MASKB', '1') == '1':
    from PIL import Image
    Mk = np.asarray(Image.open(HERE / 'work' / 'tex_Scholar_A_M.png').convert('RGB'), float)[..., :1] / 255
    Hm, Wm = Mk.shape[:2]
    by = np.array([[1, 1, 1], [4, 1, 1], [1, 4, 1], [1, 1, 4], [1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [0, 1, 1], [1, 0, 1]], float)
    by /= by.sum(1, keepdims=True); UB = D[PR[0]]['UV']; TBm = D[PR[0]]['T']
    uvs = np.einsum('kc,fcd->fkd', by, UB[TBm])
    sm = Mk[np.clip((uvs[..., 1] * Hm).astype(int), 0, Hm - 1), np.clip((uvs[..., 0] * Wm).astype(int), 0, Wm - 1)][..., 0]
    dom = sm > 0.5
    mixed = dom.any(1) & ~dom.all(1)
    maskb[:nb] = mixed & (part[:nb] == ROBE) & ~inner[:nb]
    print('mask-border robe faces', int(maskb.sum()))
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl); small = (cnt[fl] <= SMALL) & ~lining
keep = twice | face | hairline | collar | stub | cuff | jewel | jcont | sole | maskb | handc | small | rim
if E('CAP', '') == 'keep':
    keep |= part == CAP
# a lined outer face that is kept keeps its twin (re-emitted from the kept face); a twin is never cut on its own
group = np.zeros(len(T), int)
group[(part == HANDS) & handj[joint]] = 1
group[(part == HAIR) & ~lined] = 2; group[(part == HAIR) & lined] = 3
group[(part == ROBE) & lined] = 4
group[part == CAP] = 5
low = V[:, :, 1].max(1) < floor + SHOE
group[(part == LEGS) & low] = 6; group[(part == LEGS) & ~low] = 7
group[(part == HANDS) & lined] = 9
group[keep | lining] = 0
names = g['names']
for p_ in range(7):
    m = part == p_
    print(f'part {p_} {names[p_]:7s} {m.sum():5d} keep {int((m & keep).sum()):5d} free {int((m & ~keep & ~lining).sum()):5d} '
          f're-emitted {int((m & lining).sum()):5d} groups',
          {int(k): int((group[m & ~keep & ~lining] == k).sum()) for k in np.unique(group[m & ~keep & ~lining])})
print('face', int(face.sum()), 'hairline', int(hairline.sum()), 'collar', int(collar.sum()), 'stub', int(stub.sum()), 'cuff', int(cuff.sum()),
      'jewel', int(jewel.sum()), 'jewel contact', int(jcont.sum()), 'soles', int(sole.sum()), 'mask border', int(maskb.sum()),
      'small', int(small.sum()), 'rim', int(rim.sum()), 'hand contact', int(handc.sum()))
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'lining (follows its outer)', int(lining.sum()),
      'free', int((~keep & ~lining).sum()), 'of', len(T))
twl = np.where(twinv >= 0, twinv - offs[mat][:, None], -1)      # primitive-local lining vertex per corner
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=lining, lined=lined, part=part, mat=mat,
         twinv=twl, rim=rim)
