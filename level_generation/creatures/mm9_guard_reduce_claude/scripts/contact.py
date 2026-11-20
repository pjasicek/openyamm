#!/usr/bin/env python3
"""Body faces something rests on or passes close to (gates of the first candidate b55: left hand into the tunic in Death/Dead
0.3 -> 1.4 cm, right fist into the helmet in CowerLoop/CowerEnd, halberd against the right shoulder in Sleep 4 -> 12 frames):
every installed LOD0 face (both primitives; hands and linings excluded) whose posed centroid comes within R m of a posed hand
vertex in the hand-rest clips, or within RH m of the halberd in any clip (every 2nd key time), plus their mirror images.
Uses work/gate_before.glb (installed body + halberd, merge_halberd.py). -> work/contact.npy (per GLB face, Guard_A then
GuardHead_A). Env R (default 0.04), RH (0.03), CLIPS."""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
R = float(os.environ.get('R', '0.04')); RH = float(os.environ.get('RH', '0.03'))
CLIPS = os.environ.get('CLIPS', 'Standing,Fidget,Fidget2,Taunt,Hit,Hit2,AttackMelee,AttackMelee2,Death,Death2,Dead,Sleep,Aware,'
                       'Cower,CowerStart,CowerEnd,CowerLoop,BackpedalRun').split(',')
m = Model(Glb(str(HERE / 'work' / 'gate_before.glb')))
g = np.load(HERE / 'work' / 'glb_parts.npz')
T0 = m.primitives[0]['triangles']; T1 = m.primitives[1]['triangles']; nA = len(T0)
part = g['part']; lin = g['lining'].astype(bool)
hand_v = np.unique(T0[part[:nA] == 0])
target = ~np.isin(part, (0, 8)) & ~lin                      # hands and gauntlets (always next to the hands) excluded
hit = np.zeros(len(part), bool); hal = np.zeros(len(part), bool)
for c in m.clips:
    ts = m.clip_times(c)
    for t in ts[::2]:
        sp = m.skinned_positions(m.world(m.sample(c, t)))
        P0, P1, PH = sp[0][0], sp[1][0], sp[2][0]
        cen = np.vstack([P0[T0].mean(1), P1[T1].mean(1)])
        if c in CLIPS:
            d, _ = cKDTree(P0[hand_v]).query(cen, distance_upper_bound=R); hit |= target & (d < R)
        d, _ = cKDTree(PH).query(cen, distance_upper_bound=RH); hal |= target & (d < RH)
both = hit | hal
gc = g['cen']; mir = gc[both] * [-1, 1, 1]
d, _ = cKDTree(mir).query(gc); both |= target & (d < 0.004)
print('CONTACT hands', int(hit.sum()), 'halberd', int(hal.sum()), 'with mirror', int(both.sum()),
      'by part', {int(p): int((both & (part == p)).sum()) for p in np.unique(part[both])})
np.save(HERE / 'work' / 'contact.npy', both)
