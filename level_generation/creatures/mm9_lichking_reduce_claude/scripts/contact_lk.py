#!/usr/bin/env python3
"""Contact faces of the Lich King's body primitive in the clips (after mm9_lich_reduce_claude/scripts/hand_contact.py):
- arm: every body face that is not hand, bracer or upper arm with a vertex within DIST of a hand or bracer vertex in any pose
  (every clip at HZ, corpse clips included: set a's Resurrect R forearm went 1.2 -> 1.8 cm into the body and Death3's R hand had
  6 frames over 1 cm, installed 4);
- leg: coat-outer and tabard faces with a vertex within DLEG of a trouser or boot vertex in any pose (cloth_gate2: set a's
  AttackMelee coat-on-leg 2.8 -> 3.1 cm).
-> work/contact_<tag>.npz (arm, leg per body face). Usage: contact_lk.py <tag>  (env DIST=0.03 DLEG=0.015 HZ=10)"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
DIST = float(os.environ.get('DIST', '0.03')); DLEG = float(os.environ.get('DLEG', '0.015')); HZ = float(os.environ.get('HZ', '10'))
m = Model(Glb(str(HERE / 'before' / 'mm9_lichking.glb')))
g = np.load(HERE / 'work' / 'glb_parts.npz'); names = [str(x) for x in g['names']]; PI = {n: i for i, n in enumerate(names)}
T = np.asarray(m.primitives[0]['triangles']).reshape(-1, 3); nA = len(T); part = g['part'][:nA]; inner = g['inner'][:nA]
isp = lambda *n: np.isin(part, [PI[x] for x in n])
armv = np.unique(T[isp('hands', 'bracers')]); legv = np.unique(T[isp('pants', 'boots')])
armfree = ~isp('hands', 'bracers', 'uarms'); cloth = (isp('torso') & ~inner) | isp('tabard')
arm = np.zeros(nA, bool); leg = np.zeros(nA, bool)
for clip in m.clips:
    t1 = m.clip_times(clip)[-1]
    for t in np.append(np.arange(0, t1, 1 / HZ), t1):
        P = np.asarray(m.skinned_positions(m.world(m.sample(clip, t)))[0][0])
        d = cKDTree(P[armv]).query(P[T].reshape(-1, 3), distance_upper_bound=DIST)[0].reshape(-1, 3).min(1)
        arm |= (d < DIST) & armfree
        d = cKDTree(P[legv]).query(P[T].reshape(-1, 3), distance_upper_bound=DLEG)[0].reshape(-1, 3).min(1)
        leg |= (d < DLEG) & cloth
np.savez(HERE / 'work' / f'contact_{sys.argv[1]}.npz', arm=arm, leg=leg)
print('CONTACT arm', int(arm.sum()), {names[p]: int((arm & (part == p)).sum()) for p in np.unique(part[arm])},
      'leg', int(leg.sum()), {names[p]: int((leg & (part == p)).sum()) for p in np.unique(part[leg])})
