#!/usr/bin/env python3
"""PeasantF2 keep set and groups per installed GLB face (primitive order PeasantF2_A, PeasantF2Head), for mpqem.py:
work/glb_sets_<tag>.npz (keep, group, lining, lined, part, mat).

Kept exactly (brief: face exact; cuffs, linings and rim caps, soles, small pieces, hand-graft junction):
- the head primitive's head part (face skin, neck, skull, both eyes) and every inner face (caps, hair rim lining);
- the 30 beads, the buckle, the sole pieces and leg faces within SOLE of the floor;
- hairline (cap faces within HAIRLINE of head skin) and the cap's rim band (within RIMBAND of its rim lining);
- the hand-graft junction (hand faces with Forearm weight >= 0.3 at a vertex or within JUNC of a stub cap);
- the bell cuffs (dress faces within CUFF of the hand stub caps) and the neckline (dress faces within NECK of the head);
- the skirt lining's hem rim strip and every non-skirt inner face (waist cap, stub caps) with faces within 1 cm of them.
Groups: 1 hands, 2 hair cap, 3 skirt outer shell (lined: its lining is re-emitted from the twins), 4 shins, 5 braid,
6 nape tie; 0 = the rest (bodice, sleeves) at the ladder ratio. Env: BRAID_KEEP=1 keeps the braid, TIE_KEEP=1 the tie.
Usage: make_sets_pf2.py <tag>"""
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as g  # noqa: E402

tag = sys.argv[1]
E = lambda k, d: float(os.environ.get(k, d))  # noqa: E731
SOLE, HAIRLINE, RIMBAND, JUNC, CUFF, NECK = E('SOLE', 0.03), E('HAIRLINE', 0.006), E('RIMBAND', 0.010), E('JUNC', 0.02), E('CUFF', 0.10), E('NECK', 0.015)
doc, b = g.read(HERE / 'before' / 'mm9_peasantf2.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantF2' and 'mesh' in n)
prims = g.prims(doc, b, node['mesh'])
jn = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
L = np.load(HERE / 'work' / 'glb_parts.npz'); names = [str(x) for x in L['names']]; PID = {n: i for i, n in enumerate(names)}
part, inner, mat, piece = L['part'], L['inner'], L['mat'], L['piece']
nf = [len(p['T']) for p in prims]; off = np.cumsum([0] + nf)
# global face arrays
Pv = [p['POSITION'].astype(float) for p in prims]
tri = [Pv[k][p['T']] for k, p in enumerate(prims)]
TRI = np.concatenate(tri)                        # (F,3,3) rest corners
cen = TRI.mean(1)
W = [p['WEIGHTS_0'].astype(float) for p in prims]; J = [p['JOINTS_0'] for p in prims]
F = len(cen); keep = np.zeros(F, bool); group = np.zeros(F, np.int64)
body = mat == 0; head = mat == 1
floor = min(P[:, 1].min() for P in Pv)


def near(mask_from, mask_to, r):
    """faces in mask_to with any corner within r of any corner of faces in mask_from"""
    if not mask_from.any():
        return np.zeros(F, bool)
    t = cKDTree(TRI[mask_from].reshape(-1, 3)); d, _ = t.query(TRI[mask_to].reshape(-1, 3))
    out = np.zeros(F, bool); out[np.flatnonzero(mask_to)] = (d.reshape(-1, 3) <= r).any(1); return out


# skirt lining: twin faces vs the hem rim strip (rim faces have a corner at an outer skirt vertex position)
lin = part == PID['lining']; skirt = part == PID['skirt']
sk_pos = cKDTree(TRI[skirt].reshape(-1, 3))
dl, _ = sk_pos.query(TRI[lin].reshape(-1, 3)); rim = np.zeros(F, bool); rim[np.flatnonzero(lin)] = (dl.reshape(-1, 3) < 1e-6).any(1)
lining = lin & ~rim; lined = skirt.copy()
keep |= rim
# head part and every non-skirt inner face (+ 1 cm round them)
keep |= head & (part == PID['head'])
other_inner = inner & ~lin
keep |= other_inner
keep |= near(other_inner & body, body & ~lin, 0.01)
for nm in ('necklace', 'buckle'):
    keep |= part == PID[nm]
# soles: the separate sole pieces and leg faces near the floor
legs = part == PID['legs']
keep |= legs & (TRI[..., 1].min(1) < floor + SOLE)
for c in np.unique(piece[legs & body]):
    m = legs & body & (piece == c)
    if m.sum() <= 100:
        keep |= m
# hair: hairline and rim band
hair = part == PID['hair']
skin = head & (part == PID['head']) & ~inner
keep |= near(skin, hair & ~inner, HAIRLINE)
keep |= near(inner & hair, hair & ~inner, RIMBAND)
# hands: junction (forearm-weighted corners or near the stub caps)
hands = part == PID['hands']
fa = np.zeros(F, bool)
k0 = 0; T0 = prims[0]['T']
wf = np.zeros(len(Pv[0]))
for s in range(4):
    wf += np.where(np.array([('Forearm' in jn[j]) for j in J[0][:, s]]), W[0][:, s], 0)
fa[:nf[0]] = (wf[T0] >= 0.3).any(1)
stubcap = hands & inner
keep |= hands & fa
keep |= near(stubcap, hands, JUNC)
# cuffs: dress faces near the stub caps; neckline: dress faces near the head primitive
dress = part == PID['dress']
keep |= near(stubcap, dress & ~inner, CUFF)
keep |= near(head & ~inner, dress & ~inner, NECK)
# groups
group[hands] = 1
cap_piece = np.unique(piece[head & hair & inner]) if (head & hair & inner).any() else []
braid_piece = [c for c in np.unique(piece[head & hair]) if (piece[head & hair] == c).sum() > 1500]
tie_piece = [c for c in np.unique(piece[head & hair]) if c not in braid_piece and (head & hair & (piece == c) & inner).sum() == 0]
for c in np.unique(piece[head & hair]):
    m = head & hair & (piece == c)
    group[m] = 5 if c in braid_piece else 6 if c in tie_piece else 2
group[skirt] = 3
group[legs] = 4
if os.environ.get('BRAID_KEEP', '1') == '1':
    keep |= group == 5
if os.environ.get('TIE_KEEP', '1') == '1':
    keep |= group == 6
keep &= ~lining
group[keep] = 0
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=lining, lined=lined & ~keep | (lined & keep),
         part=part, mat=mat)
free = ~keep & ~lining
print('SETS', tag, 'faces', F, 'keep', int(keep.sum()), f'({keep.sum() / F * 100:.1f} %)', 'lining', int(lining.sum()),
      'rim', int(rim.sum()), 'lined', int(lined.sum()), 'free by group', {int(k): int((group[free] == k).sum()) for k in np.unique(group[free])})
for nm in names:
    m = part == PID[nm]
    print(f'  {nm:9s} {int(m.sum()):5d} kept {int((keep & m).sum()):5d}')
