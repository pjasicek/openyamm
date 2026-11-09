#!/usr/bin/env python3
"""Per-piece decimation plan for the skeleton (separate rigid bone pieces, each closed, each its own group):
work/groups.npy (int per mesh_in face: 0 kept exactly, k >= 1 one decimation group) and work/group_plan.json
({group: [base ratio, category, faces]}). decimate_pieces.py scales the base ratios per ladder step.
Kept exactly: the head set except the cranium's back dome (skull face: sockets, brow, cheekbones, nasal opening,
upper teeth row, mandible, eyes, the 20 teeth, the neck pieces), the dagger, the hip strips and every piece of
KEEP_N faces or fewer. Env overrides of the base ratios: R_HAND, R_FOOT_BIG, R_FOOT, R_LIMB_LONG, R_LIMB,
R_TORSO_BIG, R_TORSO, R_SHEET, R_DOME; DOME_Y / DOME_Z (cranium faces behind Blender y 0.0 or above z 0.60, the forehead over the brow, are the dome)."""
import json, os, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
from pieces import pieces  # noqa: E402
E = lambda k, v: float(os.environ.get(k, v))
KEEP_N = int(E('KEEP_N', 30))
R = dict(hand=E('R_HAND', .7), foot_big=E('R_FOOT_BIG', .5), foot=E('R_FOOT', .65), limb_long=E('R_LIMB_LONG', .4),
         limb=E('R_LIMB', .55), torso_big=E('R_TORSO_BIG', .4), torso=E('R_TORSO', .55), sheet=E('R_SHEET', .55),
         dome=E('R_DOME', .6))
DOME_Y = E('DOME_Y', 0.0); DOME_Z = E('DOME_Z', 0.60)
V, F, mat, comp, info = pieces(str(HERE / 'work'))
groups = np.zeros(len(F), int); plan = {}; g = 0
cranium = max((i['n'], k) for k, i in info.items() if i['cat'] == 'head')[1]
for k, i in sorted(info.items()):
    s = np.where(comp == k)[0]; cat = i['cat']; n = i['n']
    if k == cranium:
        dome = s[((V[F[s]][:, :, 1] > DOME_Y) | (V[F[s]][:, :, 2] > DOME_Z)).all(1)]
        g += 1; groups[dome] = g; plan[g] = [R['dome'], 'dome', len(dome)]
        continue
    if cat in ('head', 'dagger') or n <= KEEP_N:
        continue
    if cat == 'hand':
        r = R['hand']
    elif cat == 'foot':
        r = R['foot_big'] if n >= 50 else R['foot']
    elif cat == 'limb':
        r = R['limb_long'] if i['size'] >= 0.15 else R['limb']
    elif cat == 'torso':
        r = R['torso_big'] if n >= 100 else R['torso']
    elif cat == 'sheet':
        r = R['sheet']
    g += 1; groups[s] = g; plan[g] = [r, cat, n]
np.save(HERE / 'work' / 'groups.npy', groups)
# lined faces: the outer face of every installed lining pair (strip_lining.py), matched by centroid; the whole piece
# of such a face is a sheet (vest flanks, strap, back panel, the hip strips) and gets its lining back on export
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402
m0 = Model(Glb(str(HERE / 'before' / 'mm9_skeleton.glb'))).primitives[0]
lin = np.load(HERE / 'work' / 'lining.npy'); lc = m0['positions'][m0['triangles'][lin]].mean(1)
lc = np.c_[lc[:, 0], -lc[:, 2], lc[:, 1] - 1.10451340675354]   # glTF y-up -> Blender z-up, the MM9_Rig node's offset
dist, _ = cKDTree(lc).query(V[F].mean(1)); outer = dist < 1e-5
print('LINED outer faces', int(outer.sum()), 'of', int(lin.sum()))
sheet = np.isin(comp, np.unique(comp[outer]))
np.save(HERE / 'work' / 'sheet_faces.npy', sheet)
json.dump(plan, open(HERE / 'work' / 'group_plan.json', 'w'))
tot = len(F); kept = int((groups == 0).sum())
est = kept + sum(int(round(v[2] * v[0])) for v in plan.values())
cats = {}
for v in plan.values():
    c = cats.setdefault(v[1], [0, 0]); c[0] += v[2]; c[1] += int(round(v[2] * v[0]))
print('GROUPS', g, 'kept faces', kept, f'({kept / tot:.1%})', 'estimate at s=1:', est, 'of', tot, '(+ lining)')
for c, (a, b) in cats.items():
    print(f'  {c:8s} {a:5d} -> {b:5d}')
