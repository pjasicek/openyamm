#!/usr/bin/env python3
"""Keep / group / drop sets per face of work/mesh_in.npz (welded source, Blender frame) for decimate_tex.py, from the creature
project's part labels on the installed GLB (work/glb_parts.npz, glb_parts.py) and the GLB's skin weights.
Kept exactly (route A and B): the head material (face, coif, eyes, braids: the IgridHead primitive is not even swapped),
hands, jewel (clasp ribbons and brooches), legs' soles (lowest 6 cm), the gown (skirt: 1,424 of its 1,462 faces are lining pairs),
the sleeve ends (robe faces within SLEEVE m behind the wrist joint and 16 cm of the forearm axis: the r42-r45 taper, rim,
recentred bell, cuff and undersleeve), the undersleeve tubes (robe faces within 5 cm of the wrist-elbow-upper-arm axis),
robe pieces of up to 300 faces, and around the hood opening (BOXES region of linings_wo.sh, widened 3 cm).
Route A (default): also every lining twin, rim strip and lined outer face exactly.
Route B (ROUTE=B): lining twins and rim strips outside the kept zones are dropped (DROP), their outer faces decimated with
the rest; reline.py re-derives them on the reduced surface.
Groups: 1 = hood (robe faces >50 % Head/Neck) at its own ratio; 2 = shins/shoes above the soles.
Writes work/keep_<tag>.npy, work/groups_<tag>.npy, work/drop_<tag>.npy, work/lined_src_<tag>.npy (outer faces whose twin was dropped)."""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
tag = sys.argv[1]; ROUTE = os.environ.get('ROUTE', 'A'); SLEEVE = float(os.environ.get('SLEEVE', '0.25'))
d = np.load(HERE / 'work' / 'mesh_in.npz'); V, F = d['verts'], d['faces']
g = np.load(HERE / 'work' / 'glb_parts.npz'); names = [str(x) for x in g['names']]
gc = g['cen'][:, [0, 2, 1]] * [1, -1, 1]                      # glTF y-up -> Blender z-up
fc = V[F].mean(1)
dist, nn = cKDTree(gc).query(fc); assert dist.max() < 1e-5, dist.max()
part = g['part'][nn]; inner = g['inner'][nn].astype(bool); mat = g['mat'][nn]
P = lambda n: part == names.index(n)
# weights per glb vertex -> per glb face -> mesh_in face
m = Model(Glb(str(HERE / 'before' / 'mm9_wyrdold.glb')))
nm = [n.get('name') for n in m.glb.json['nodes']]; jn = [nm[j] for j in m.joints]
J = np.vstack([p['joints'] for p in m.primitives]); W = np.vstack([p['weights'] for p in m.primitives])
offs = np.cumsum([0] + [len(p['positions']) for p in m.primitives]); gt = np.vstack([p['triangles'] + o for p, o in zip(m.primitives, offs)])
ws = lambda subs: (np.isin(J, [i for i, n in enumerate(jn) if any(s in n for s in subs)]) * W).sum(1)[gt].mean(1)[nn]
fhead = ws(['Head', 'Neck'])
jp = np.linalg.inv(m.inverse_binds)[:, :3, 3][:, [0, 2, 1]] * [1, -1, 1]
J3 = lambda n: jp[jn.index(n)]
keep = np.zeros(len(F), bool); drop = np.zeros(len(F), bool)
keep |= mat == 1; keep |= P('hands') | P('jewel') | P('skirt') | P('braids')
floor = V[:, 2].min(); keep |= P('legs') & (V[F][:, :, 2].min(1) < floor + 0.06)
robe = P('robe')
sl = np.zeros(len(F), bool)
for s in ('L', 'R'):
    w, e, u = J3(f'FHP {s} Hand'), J3(f'FHP {s} Forearm'), J3(f'FHP {s} UpperArm')
    ax = (w - e) / np.linalg.norm(w - e); t = (fc - w) @ ax; r = np.linalg.norm(fc - w - t[:, None] * ax, axis=1)
    sl |= robe & (t > -SLEEVE) & (r < 0.16)
    for a, b in ((w, e), (e, e + 0.06 * (u - e) / np.linalg.norm(u - e))):     # undersleeve tube: wrist -> elbow -> 6 cm up
        ab = b - a; tt = np.clip((fc - a) @ ab / (ab @ ab), 0, 1); dd = np.linalg.norm(fc - a - tt[:, None] * ab, axis=1)
        sl |= robe & (dd < 0.05)
keep |= sl
# hood opening round the face (linings_wo.sh BOXES robe:-0.12,0.12:-0.15,0.2:0.40,0.52 in the npz frame = this frame mirrored in x)
box = robe & (np.abs(fc[:, 0]) < 0.15) & (fc[:, 1] > -0.18) & (fc[:, 1] < 0.23) & (fc[:, 2] > 0.37) & (fc[:, 2] < 0.55)
keep |= box
# small robe pieces
key = np.round(V, 6); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel(); t_ = inv[F]; n_ = inv.max() + 1
r_ = np.concatenate([t_[:, 0], t_[:, 1], t_[:, 2]]); c_ = np.concatenate([t_[:, 1], t_[:, 2], t_[:, 0]])
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n_, n_)), directed=False)
fl = lab[t_[:, 0]]
small = np.zeros(len(F), bool)
for k in np.unique(fl[robe]):
    s = robe & (fl == k)
    if s.sum() <= 300: small |= s
keep |= small
# linings: twin <-> outer (same vertex positions offset; matched through the creature npz's orig triples, glb_parts src)
u = np.load(HERE.parent / 'mm9_wyrdold_claude' / 'work' / 'uv_tex.npz', allow_pickle=True)
orig, utri, uinner = u['orig'], u['tri'], u['inner']
okey = [tuple(sorted(orig[t])) for t in utri]; outer_of = {}
for f, k in enumerate(okey):
    if not uinner[f]: outer_of.setdefault(k, f)
src = g['src'][nn]                                                   # creature npz face per mesh_in face
npz2mi = {int(s_): i for i, s_ in enumerate(src)}
twin_outer = -np.ones(len(F), int); rim = np.zeros(len(F), bool)
for i in np.where(inner)[0]:
    k = okey[src[i]]
    if len(set(k)) < 3: rim[i] = True
    else: twin_outer[i] = npz2mi.get(outer_of[k], -1)
lined_outer = np.zeros(len(F), bool); lined_outer[twin_outer[twin_outer >= 0]] = True
if ROUTE == 'A':
    keep |= inner | lined_outer
    lined_src = np.zeros(len(F), bool)
else:
    # a twin stays when its outer face is kept; rims stay when touching a kept twin's vertices, else dropped
    tw_keep = (twin_outer >= 0) & keep[np.maximum(twin_outer, 0)]
    keep |= tw_keep
    kept_v = np.zeros(len(V) + 1, bool); kept_v[np.unique(inv[F[tw_keep | (keep & ~inner)]])] = True
    rim_keep = rim & kept_v[inv[F]].all(1)
    keep |= rim_keep
    drop = inner & ~tw_keep & ~rim_keep
    lined_src = lined_outer & ~keep
    keep &= ~drop
groups = np.zeros(len(F), int)
groups[robe & (fhead > 0.5) & ~keep & ~drop] = 1
groups[P('legs') & ~keep] = 2
for n in names:
    s = P(n); print(f'{n:7s} {s.sum():6d} keep {int((s & keep).sum()):6d} drop {int((s & drop).sum()):5d} free {int((s & ~keep & ~drop).sum()):5d}')
print('sleeve', int(sl.sum()), 'hood box', int(box.sum()), 'small', int(small.sum()), 'hood group', int((groups == 1).sum()),
      'legs group', int((groups == 2).sum()), 'lined src (relined later)', int(lined_src.sum()))
print('TOTAL keep', int(keep.sum()), 'drop', int(drop.sum()), 'free', int((~keep & ~drop).sum()), 'of', len(F))
for k_, a_ in (('keep', keep), ('groups', groups), ('drop', drop), ('lined_src', lined_src)):
    np.save(HERE / 'work' / f'{k_}_{tag}.npy', a_)
