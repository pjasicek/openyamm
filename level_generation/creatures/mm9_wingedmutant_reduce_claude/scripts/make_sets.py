#!/usr/bin/env python3
"""Per-face sets over work/mesh_in.npz (GLB face order, checked by analyse.py's labels): side of the symmetry plane,
wing back copies (regenerated after the cut), exact keep set and cut groups.
Keep exactly: head skin (the creature's HeadUV gives every skin face the dense face density, so all of it counts as
face), eyes, teeth, the neck bridge ring; wing faces touching a vertex the membrane helpers (Yw*piv / Yw*mid) weight over
HELPER_W (brief: helper-driven parts keep their heavily weighted vertices); foot claw/toe tips (CLAW_TIP m of each claw
chain's far end) so the lowest point (hover, corpse) stays.
KEEP_EXTRA=<npy,...> adds error locks. Groups: 0 body (ladder ratio), 1 hair, 2 wing front sheet, 3 feet.
Writes work/sets.npz (side, back, keep, group, src_front_of)."""
import os, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
d = np.load(HERE / 'work' / 'mesh_in.npz'); L = np.load(HERE / 'work' / 'glb_labels.npz')
sw = np.load(HERE / 'work' / 'src_weights.npz'); W = sw['weights']; names = [str(n) for n in sw['names']]
v, f = d['verts'], d['faces']; n = len(f)
HELPER_W = float(os.environ.get('HELPER_W', '0.75'))
cx = v[f][:, :, 0]
side = np.where((cx > 1e-6).all(1) | ((cx > -1e-6).all(1) & (cx > 1e-6).any(1)), 1, 0)
side = np.where((cx < -1e-6).all(1) | ((cx < 1e-6).all(1) & (cx < -1e-6).any(1)), -1, side)
print('SIDE +', (side == 1).sum(), '-', (side == -1).sum(), 'plane', (side == 0).sum())
prim, kind, back = L['prim'], L['kind'], L['back']
keep = (prim == 2) & np.isin(kind, [0, 1, 2, 4])
col = lambda pred: np.array([pred(nm) for nm in names])
helper = W[:, col(lambda s: s.startswith('Yw') and ('piv' in s or 'mid' in s) and not s.startswith('Ywingpiv'))].sum(1)
heavy = helper > HELPER_W
wing_front = (prim == 1) & ~back
keep_wing = wing_front & heavy[f].any(1)
# KEEP_SPAR=<w>: the wing arm tube along the leading edge (spar bones YwingA-E, Ywingpiv, Ywingarm weigh over w on
# average): a 5-6 sided tube with knuckle bumps that any collapse flattens (ladder f: 511 of 798 failing wing faces)
spar = W[:, col(lambda s: s.startswith('Yw') and not ('piv' in s or 'mid' in s) or s.startswith('Ywingpiv'))].sum(1)
if os.environ.get('KEEP_SPAR'):
    ks = wing_front & (spar[f].mean(1) > float(os.environ['KEEP_SPAR']))
    print('KEEP spar tube', int((ks & ~keep_wing).sum()), 'more'); keep_wing |= ks
foot_bones = col(lambda s: any(k in s for k in ('Foot', 'claw', 'toe', 'Xfoot')))
footw = W[:, foot_bones].sum(1)
# claw tips: vertices far out on the claw chains (Xclaw*mid / Xtoemid dominant)
tipb = col(lambda s: ('mid' in s and (s.startswith('Xclaw') or s.startswith('Xtoe'))))
tip = W[:, tipb].sum(1) > 0.5
group = np.zeros(n, int)
group[prim == 2] = 1   # hair (non-hair head faces are kept)
group[wing_front] = 2
group[(prim == 0) & (footw[f].mean(1) > 0.5)] = 3
keep_claw = (prim == 0) & tip[f].any(1)
keep = keep | keep_wing | keep_claw | (side == 0)
for extra in [x for x in os.environ.get('KEEP_EXTRA', '').split(',') if x]:   # error locks (rest_lock.py, err_lock.py)
    e = np.load(extra); print('KEEP_EXTRA', extra, int((e & ~keep).sum()), 'more'); keep |= e
print('KEEP head', ((prim == 2) & keep).sum(), 'wing heavy', keep_wing.sum(), f'(helper>{HELPER_W}; Ywingpiv is the arm root, not a helper)',
      'claw tips', keep_claw.sum(), 'plane', (side == 0).sum(), 'total', keep.sum())
for gname, gi in (('body', 0), ('hair', 1), ('wing', 2), ('feet', 3)):
    s = (group == gi) & ~keep & ~back
    print(f'GROUP {gi} {gname}: free {s.sum()} (+x {(s & (side == 1)).sum()})')
print('BACK', back.sum())
np.savez(HERE / 'work' / 'sets.npz', side=side, back=back, keep=keep, group=group, front_of=L['front_of'], helper=helper)
