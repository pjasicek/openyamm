#!/usr/bin/env python3
"""Keep / group sets per installed GLB LOD0 face (work/glb_parts.npz order: Skraelos then SkraelosHead) for mpqem.py, written to
work/glb_sets_<tag>.npz (keep, group, lining, lined, part, mat, twinv, rim; no linings: the cloth material is doubleSided).
Parts (glb_parts.py): 0 robe (robe, tabard, sleeves), 1 hood, 2 hands (bone pieces), 3 cap, 4 head (skull), 5 cowl (neck tube),
6 necklace (cord + 21 fangs), 7 staff, 8 heldskull, 9 pendant.

Keep exactly (REDUCTION_AGENT_TOWNSFOLK: relaxed set, face exact; props and glow exact):
- the face: the whole skull (cranium, jaw, teeth, ember eyes = the emission), the cowl (neck tube into the collar) and the inner cap;
- the held props: the staff, the held skull (its socket fills), the pendant;
- the hood opening: hood faces on the hood's open boundary plus HRINGS rings, and hood faces within FACEEDGE m of a skull vertex;
- the collar: cloth faces within COLLAR m of a skull or cowl vertex (the neck seam);
- the grip: hand faces within GRIP m of the staff or the held skull in any pose (contact_sk.py), whole pieces of up to TIP faces
  (fingertips: every finger keeps its shape);
- sleeve ends and hand-on-robe: robe/hood faces within CUFF m of a hand vertex in any pose; robe within PROPC m of the staff or the
  held skull in any pose (prop gate); cloth under the necklace cord within JEWELC m of it in any pose;
- whole necklace pieces of up to FANG faces when FANGS=keep.
Groups: 1 hands (bone pieces), 2 hood, 3 necklace, 0 = robe (the ladder ratio).
Usage: make_sets_sk.py <tag>"""
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
ROBE, HOOD, HANDS, CAP, HEAD, COWL, NECK, STAFF, HSKULL, PEND = range(10)
FACEEDGE = float(E('FACEEDGE', '0.015')); COLLAR = float(E('COLLAR', '0.012')); CUFF = float(E('CUFF', '0.02'))
GRIP = float(E('GRIP', '0.008')); TIP = int(E('TIP', '16')); PROPC = float(E('PROPC', '0.02')); JEWELC = float(E('JEWELC', '0.006'))
HRINGS = int(E('HRINGS', '1')); FANG = int(E('FANG', '40'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_skraelos.glb', 'Skraelos')
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']
C = np.load(HERE / 'work' / 'contact.npz'); dmin = C['dmin']; srcs = [str(s) for s in C['srcs']]
dc = lambda s: dmin[:, srcs.index(s)]
PR = ['Skraelos', 'SkraelosHead']
P = np.concatenate([D[k]['P'] for k in PR]); offs = np.cumsum([0] + [len(D[k]['P']) for k in PR])
T = np.concatenate([D[k]['T'] + offs[i] for i, k in enumerate(PR)])
mat = np.r_[np.zeros(len(D[PR[0]]['T']), int), np.ones(len(D[PR[1]]['T']), int)]
assert len(T) == len(part)
V = P[T]
near = lambda pts, r: cKDTree(P[pts]).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < r
pv = lambda m: np.unique(T[m].ravel())
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl)

face = np.isin(part, (HEAD, COWL, CAP))
props = np.isin(part, (STAFF, HSKULL, PEND))
# hood opening: open boundary + rings, and hood near the skull
hoodf = part == HOOD
ec = {}
for f in np.flatnonzero(hoodf):
    t = FT[f]
    for a_, b_ in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
        ec.setdefault((min(a_, b_), max(a_, b_)), []).append(f)
bv = np.zeros(n, bool)
for (a_, b_), fs in ec.items():
    if len(fs) == 1:
        bv[a_] = bv[b_] = True
hl = hoodf & bv[FT].any(1)
for _ in range(HRINGS):
    vv = np.zeros(n, bool); vv[FT[hl].ravel()] = True; hl = hoodf & vv[FT].any(1)
hoodrim = hl | (hoodf & near(pv(part == HEAD), FACEEDGE))
cloth = np.isin(part, (ROBE, HOOD))
collar = cloth & near(pv(np.isin(part, (HEAD, COWL))), COLLAR)
grip = (part == HANDS) & ((dc('staff') < GRIP) | (dc('heldskull') < GRIP))
tips = (part == HANDS) & (cnt[fl] <= TIP)
cuff = cloth & (dc('hands') < CUFF)
propc = cloth & ((dc('staff') < PROPC) | (dc('heldskull') < PROPC))
jcont = cloth & (dc('necklace') < JEWELC)
fangs = (part == NECK) & (cnt[fl] <= FANG) if E('FANGS', 'reduce') == 'keep' else np.zeros(len(T), bool)
keep = face | props | hoodrim | collar | grip | tips | cuff | propc | jcont | fangs
group = np.zeros(len(T), int)
group[part == HANDS] = 1; group[part == HOOD] = 2; group[part == NECK] = 3
group[keep] = 0
names = g['names']
for p_ in range(10):
    m = part == p_
    print(f'part {p_} {names[p_]:9s} {m.sum():5d} keep {int((m & keep).sum()):5d} free {int((m & ~keep).sum()):5d} groups',
          {int(k): int((group[m & ~keep] == k).sum()) for k in np.unique(group[m & ~keep])})
print('face', int(face.sum()), 'props', int(props.sum()), 'hood rim', int(hoodrim.sum()), 'collar', int(collar.sum()), 'grip', int(grip.sum()),
      'tips', int(tips.sum()), 'cuff', int(cuff.sum()), 'prop contact', int(propc.sum()), 'necklace contact', int(jcont.sum()), 'fangs', int(fangs.sum()))
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'free', int((~keep).sum()), 'of', len(T))
z = np.zeros(len(T), bool)
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=z, lined=z, part=part, mat=mat,
         twinv=-np.ones((len(T), 3), np.int64), rim=z)
