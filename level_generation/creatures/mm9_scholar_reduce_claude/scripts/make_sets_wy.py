#!/usr/bin/env python3
"""Keep / group sets per installed GLB LOD0 face (work/glb_parts.npz order: Scholar_A then ScholarHead) for mpqem.py, written to
work/glb_sets_<tag>.npz (keep, group, lining, lined, part, mat, twinv, rim). Parts (glb_parts.py): 0 head set, 1 mantle, 2 dress
(gown, sleeves, closed cuff caps), 3 jewel, 4 skirt (underskirt), 5 legs (below the knee, inside the skirt), 6 hands (MPFB, 6 cm
forearm stub through the cuff caps). Head sub-labels: 0 face skin, 1 hair, 2 hood, 3 eye.

Linings (linings_wy.py): every lining face is its outer face reversed, each corner 2 mm behind along the asm normal with the outer
corner's UV and weights, plus two-face rim strips at the open edges. Matched here by UV and position (twin corner = lining vertex
with the outer corner's UV within OFF m); mpqem cuts the outer cloth and re-emits the lining from the surviving lined faces
(twinv); rim strips are kept exactly. Lined and unlined faces of one part go into separate groups (their border stays).

Keep exactly (REDUCTION_AGENT_TOWNSFOLK: relaxed set, face exact):
- the face: every head face that is not Verdandi's green cloth colour (skin, neck, lips, circlet, its jewel; head_colour.py) or is
  seg 'head' (face skin) or an eye, plus hair/hood faces within FACEEDGE m of it;
- the collar: body faces within COLLAR m of a head-primitive vertex (the head-set / mantle seam);
- hand-in-sleeve: the forearm stub (forearm-weighted hand faces) and dress faces within CUFF m of a hand vertex (the closed cuff
  caps and sleeve ends);
- the jewellery (899, rigid gold and beads: JEWEL=keep) and cloth faces within JEWELC m of it (beads sit on the cloth);
- region-mask border faces (MASKB=1: a body face whose UV triangle spans two classes of R mantle / G gown / B damask / A cord /
  unmasked gold);
- soles: leg faces within SOLE m of the floor; pieces of up to SMALL faces; lining rim strips.
Groups: 1 hands + fingers (seam slides), 2 head cloth unlined, 3 head cloth lined, 4 body cloth lined (mantle, dress, skirt),
5 skirt, 6 shoes (below SHOE m), 7 hidden shins, 8 mantle, 0 = dress (the ladder ratio).
Usage: make_sets_wy.py <tag>"""
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
HEAD, MANTLE, DRESS, JEWEL, SKIRT, LEGS, HANDS = range(7)
FACEEDGE = float(E('FACEEDGE', '0.008')); COLLAR = float(E('COLLAR', '0.01')); CUFF = float(E('CUFF', '0.02'))
SOLE = float(E('SOLE', '0.012')); SHOE = float(E('SHOE', '0.14')); SMALL = int(E('SMALL', '80')); JEWELC = float(E('JEWELC', '0.006'))
OFF = float(E('OFF', '0.0035'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_scholar.glb', 'Scholar')
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']; jn = g['jnames']; joint = g['joint']; inner = g['inner']; sub = g['sub']
hc = np.load(HERE / 'work' / 'head_colour.npz')
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
green = np.zeros(len(T), bool); green[nb:] = hc['green_frac'] > 0.5
face_core = (part == HEAD) & ~inner & (~green | (sub == 0) | (sub == 3))
face = face_core | ((part == HEAD) & ~inner & near(pv(face_core), FACEEDGE))
collar = (part != HEAD) & near(pv(part == HEAD), COLLAR)
handj = np.array([any(t in str(x) for t in (' Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) for x in jn])
stub = (part == HANDS) & ~handj[joint]
cuff = (part == DRESS) & near(pv(part == HANDS), CUFF)
jewel = (part == JEWEL) if E('JEWEL', 'keep') == 'keep' else np.zeros(len(T), bool)
jcont = (part != JEWEL) & (part != HEAD) & near(pv(part == JEWEL), JEWELC)
sole = (part == LEGS) & (V[:, :, 1].min(1) < floor + SOLE)
maskb = np.zeros(len(T), bool)
if E('MASKB', '1') == '1':
    from PIL import Image
    Mk = np.asarray(Image.open(HERE / 'work' / 'tex_Scholar_A_M.png').convert('RGB'), float) / 255
    Mn = np.asarray(Image.open(HERE / 'work' / 'tex_Scholar_A_N.png').convert('L'), float)[..., None] / 255
    Mk = np.concatenate([Mk, Mn], -1); Hm, Wm = Mk.shape[:2]
    by = np.array([[1, 1, 1], [4, 1, 1], [1, 4, 1], [1, 1, 4], [1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [0, 1, 1], [1, 0, 1]], float)
    by /= by.sum(1, keepdims=True); UB = D[PR[0]]['UV']; TBm = D[PR[0]]['T']
    uvs = np.einsum('kc,fcd->fkd', by, UB[TBm])
    sm = Mk[np.clip((uvs[..., 1] * Hm).astype(int), 0, Hm - 1), np.clip((uvs[..., 0] * Wm).astype(int), 0, Wm - 1)]
    dom = np.where(sm.max(-1) > 0.35, sm.argmax(-1), 4)
    mixed = np.array([len(set(r)) > 1 for r in dom])
    maskb[:nb] = mixed & np.isin(part[:nb], (MANTLE, DRESS, SKIRT)) & ~inner[:nb]
    print('mask-border cloth faces', int(maskb.sum()), 'by part', {int(p_): int((maskb & (part == p_)).sum()) for p_ in (1, 2, 4)})
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl); small = (cnt[fl] <= SMALL) & ~lining
keep = twice | face | collar | stub | cuff | jewel | jcont | sole | maskb | small | rim | (sub == 3)
# a lined outer face that is kept keeps its twin (re-emitted from the kept face); a twin is never cut on its own
group = np.zeros(len(T), int)
group[(part == HANDS) & handj[joint]] = 1
group[(part == HEAD) & ~lined] = 2; group[(part == HEAD) & lined] = 3
group[np.isin(part, (MANTLE, DRESS, SKIRT)) & lined] = 4
group[(part == SKIRT) & ~lined] = 5
low = V[:, :, 1].max(1) < floor + SHOE
group[(part == LEGS) & low] = 6; group[(part == LEGS) & ~low] = 7
group[(part == MANTLE) & ~lined] = 8
group[(part == HANDS) & lined] = 9
group[keep | lining] = 0
names = g['names']
for p_ in range(7):
    m = part == p_
    print(f'part {p_} {names[p_]:7s} {m.sum():5d} keep {int((m & keep).sum()):5d} free {int((m & ~keep & ~lining).sum()):5d} '
          f're-emitted {int((m & lining).sum()):5d} groups',
          {int(k): int((group[m & ~keep & ~lining] == k).sum()) for k in np.unique(group[m & ~keep & ~lining])})
print('face', int(face.sum()), '(core', int(face_core.sum()), ') collar', int(collar.sum()), 'stub', int(stub.sum()), 'cuff', int(cuff.sum()),
      'jewel', int(jewel.sum()), 'jewel contact', int(jcont.sum()), 'soles', int(sole.sum()), 'mask border', int(maskb.sum()),
      'small', int(small.sum()), 'rim', int(rim.sum()))
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'lining (follows its outer)', int(lining.sum()),
      'free', int((~keep & ~lining).sum()), 'of', len(T))
twl = np.where(twinv >= 0, twinv - offs[mat][:, None], -1)      # primitive-local lining vertex per corner
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=lining, lined=lined, part=part, mat=mat,
         twinv=twl, rim=rim)
