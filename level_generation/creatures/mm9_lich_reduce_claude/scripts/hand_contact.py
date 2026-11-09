#!/usr/bin/env python3
"""Faces the bony hands come near in the clips (after mm9_ghost_reduce_claude/scripts/hand_contact.py): every non-hand face of
Lich_A with a vertex within DIST of a hand vertex (parts 3, 10) in any pose (every clip at HZ, the corpse clips skipped), plus
hand faces within DIST_HH of the other hand. Why: the Lich's fingertips rest in the thigh in Fidget, ResurrectSpell and Taunt
(arm_hand_gate hand depth 5.3-5.5 cm, accepted); a coarser robe/pants surface there would change that depth.
-> work/hand_contact.npy (per Lich_A face). Usage: hand_contact.py  (env DIST=0.04 DIST_HH=0.015 HZ=15)"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
DIST = float(os.environ.get('DIST', '0.04')); DIST_HH = float(os.environ.get('DIST_HH', '0.008')); HZ = float(os.environ.get('HZ', '15'))
m = Model(Glb(str(HERE / 'before' / 'mm9_lich.glb')))
g = np.load(HERE / 'work' / 'glb_parts.npz')
T = np.asarray(m.primitives[0]['triangles']).reshape(-1, 3); nA = len(T); part = g['part'][:nA]
hv = {s: np.unique(T[part == p]) for s, p in (('A', 3), ('B', 10))}
hand = np.isin(part, (3, 10))
# each hand's own sleeve (cloak faces on its side, |x| > SLEEVE at rest; hand 3 is at -x, hand 10 at +x) is left out: the cuff
# hangs round the wrist in every pose
SLEEVE = float(os.environ.get('SLEEVE', '0.15'))
cx = np.asarray(m.primitives[0]['positions'])[T].mean(1)[:, 0]
own = {'A': (part == 2) & (cx < -SLEEVE), 'B': (part == 2) & (cx > SLEEVE)}
near = np.zeros(nA, bool); hh = np.zeros(nA, bool)
for clip in m.clips:
    if clip.startswith('Dea'):
        continue
    t1 = m.clip_times(clip)[-1]
    for t in np.append(np.arange(0, t1, 1 / HZ), t1):
        P = np.asarray(m.skinned_positions(m.world(m.sample(clip, t)))[0][0])
        for s, o in (('A', 'B'), ('B', 'A')):
            tree = cKDTree(P[hv[s]])
            d = tree.query(P[T].reshape(-1, 3), distance_upper_bound=DIST)[0].reshape(-1, 3).min(1)
            near |= (d < DIST) & ~hand & ~own[s]
            mo = np.isin(T, hv[o]).all(1)
            d = tree.query(P[T[mo]].reshape(-1, 3), distance_upper_bound=DIST_HH)[0].reshape(-1, 3).min(1)
            hh[np.flatnonzero(mo)[d < DIST_HH]] = True
np.save(HERE / 'work' / 'hand_contact.npy', near | hh)
print('HAND CONTACT body', int(near.sum()), {int(p): int((near & (part == p)).sum()) for p in np.unique(part[near])}, 'hand to hand', int(hh.sum()))
