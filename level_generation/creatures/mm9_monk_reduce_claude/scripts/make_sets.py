#!/usr/bin/env python3
"""Keep / group sets per face of work/mesh_in.npz (welded source, Blender frame) for decimate_tex.py, from the creature
project's part labels on the installed GLB (work/glb_parts.npz, glb_parts.py).
Kept exactly: the head material (face, beard, eyeballs: the MonkHead primitive is restored byte for byte on export),
hands (MPFB, forearm stub), cords (thin tubes), shins (hidden), the robe's inner faces (hood lining, sleeve cups, hem cap)
and the outer robe faces within RINGS face rings of them (hood opening, cuffs, hem: the outer shell may not dip under its lining
near a rim), soles (shoe faces below floor + 6 cm; SHOES=1, the default, keeps the whole shoes), connected pieces of up to SMALL faces.
Optional: ELBOW=1 keeps the robe faces within ELBOW_R of the elbow joints (refine.py's four rings per elbow).
Groups (own ratio in decimate_tex.py): 1 = shoes above the soles, 2 = belt, 3 = knots, 4 = hands (HANDS=group). Label 0 = the robe's outer rest.
Writes work/keep_<tag>.npy, work/groups_<tag>.npy. Usage: make_sets.py <tag>"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
tag = sys.argv[1]
RINGS = int(os.environ.get('RINGS', '2')); SMALL = int(os.environ.get('SMALL', '80'))
d = np.load(HERE / 'work' / 'mesh_in.npz'); V, F = d['verts'], d['faces']
g = np.load(HERE / 'work' / 'glb_parts.npz'); names = [str(x) for x in g['names']]
gc = g['cen'][:, [0, 2, 1]] * [1, -1, 1]                      # glTF y-up -> Blender z-up
fc = V[F].mean(1)
dist, nn = cKDTree(gc).query(fc); print('face match max', dist.max()); assert dist.max() < 1e-4
part = g['part'][nn]; inner = g['inner'][nn].astype(bool); mat = g['mat'][nn]
P = lambda n: part == names.index(n)
keep = np.zeros(len(F), bool)
keep |= mat == 1; keep |= P('cords') | P('shins')
# HANDS=group: hands decimated on their own (group 4; prio-1 relaxed keep set: 0.6-0.75, every finger kept)
if os.environ.get('HANDS', 'keep') == 'keep':
    keep |= P('hands')
robe = P('robe'); keep |= robe & inner
# rim: outer robe faces within RINGS face rings of an inner face (by welded position; a Euclidean radius took the whole
# thin hood shell)
kk = np.round(V, 6); _, wv = np.unique(kk, axis=0, return_inverse=True); wv = wv.ravel(); FT = wv[F]
reach = robe & inner
for _ in range(RINGS):
    hot = np.zeros(wv.max() + 1, bool); hot[FT[reach].ravel()] = True
    reach = reach | (robe & hot[FT].any(1))
rim = reach & ~inner; keep |= rim
floor = V[:, 2].min(); sole = P('shoes') & (V[F][:, :, 2].min(1) < floor + 0.06); keep |= sole
# SHOES=1 (default): whole shoes kept (a 60 % shoe upper lost 48 mm of the raised left shoe in Death2, ladder A)
if os.environ.get('SHOES', '1') == '1':
    keep |= P('shoes')
# connected pieces (by welded position)
key = np.round(V, 6); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel(); t_ = inv[F]; n_ = inv.max() + 1
r_ = np.concatenate([t_[:, 0], t_[:, 1], t_[:, 2]]); c_ = np.concatenate([t_[:, 1], t_[:, 2], t_[:, 0]])
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n_, n_)), directed=False)
fl = lab[t_[:, 0]]; cnt = np.bincount(fl)
small = cnt[fl] <= SMALL; keep |= small
for n in names:
    s = P(n); sizes = sorted(np.bincount(fl[s])[np.bincount(fl[s]) > 0].tolist(), reverse=True)
    print(f'  {n:6s} pieces {sizes[:12]}')
elbow = np.zeros(len(F), bool)
if os.environ.get('ELBOW'):
    doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_monk.glb')
    sk = doc['skins'][nd['skin']]; ibm = glbio.arr(doc, binary, sk['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
    jn = [doc['nodes'][j]['name'] for j in sk['joints']]; jp = np.linalg.inv(ibm)[:, :3, 3][:, [0, 2, 1]] * [1, -1, 1]
    R_ = float(os.environ.get('ELBOW_R', '0.08'))
    for s in ('L', 'R'):
        e = jp[jn.index(f'Bip01 {s} Forearm')]
        elbow |= robe & (np.linalg.norm(fc - e, axis=1) < R_)
    keep |= elbow
groups = np.zeros(len(F), int)
groups[P('shoes') & ~keep] = 1; groups[P('belt') & ~keep] = 2; groups[P('knots') & ~keep] = 3; groups[P('hands') & ~keep] = 4
for n in names:
    s = P(n); print(f'{n:6s} {s.sum():6d} keep {int((s & keep).sum()):6d} free {int((s & ~keep).sum()):5d}')
print('robe inner', int((robe & inner).sum()), 'rim', int(rim.sum()), 'soles', int(sole.sum()), 'small', int(small.sum()),
      'elbow', int(elbow.sum()))
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'free', int((~keep).sum()), 'of', len(F),
      '| groups', {k: int((groups == k).sum()) for k in (1, 2, 3, 4)})
np.save(HERE / 'work' / f'keep_{tag}.npy', keep); np.save(HERE / 'work' / f'groups_{tag}.npy', groups)
