#!/usr/bin/env python3
"""Faces the hands rest on or pass close to (after the Monk's hand_contact.py): the arm/hand gate's hand depth grew in Fidget
(1.2 -> 3.5 cm), Taunt and AttackRanged when the robe, torso and sleeves under the hands were cut. Every face of the cut
parts (robe, torso, sleeves, belt) of the installed LOD0 body primitive whose posed centroid comes within R m of a posed hand
vertex of either hand in any frame (every clip, 10 Hz), mirrored across x in the rest pose. Writes work/keep_hand.npy (bool
per body face, the GLB's order). Also the hand faces within R of the other hand (the hands meet in AttackRanged and
Resurrect: a 65 % left hand let the right hand's fingers 1.1 cm into it). Usage: hand_contact.py (env R, default 0.04; RH for hand to hand, default 0.012)"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
R = float(os.environ.get('R', '0.04'))
RH = float(os.environ.get('RH', '0.012'))      # hand to the other hand
m = Model(Glb(str(HERE / 'before' / 'mm9_nosferatu.glb')))
g = np.load(HERE / 'work' / 'glb_parts.npz'); names = [str(x) for x in g['names']]
T = np.asarray(m.primitives[0]['triangles']).reshape(-1, 3); nA = len(T)
part = g['part'][:nA]
hand_v = np.unique(T[part == names.index('hands')])
target = np.isin(part, [names.index(n) for n in ('robe', 'torso', 'sleeves', 'belt')])
hit = np.zeros(nA, bool)
rest0 = np.asarray(m.primitives[0]['positions'], float)
hand_f = part == names.index('hands'); left_f = rest0[T].mean(1)[:, 0] > 0
hv_l = np.unique(T[hand_f & left_f]); hv_r = np.unique(T[hand_f & ~left_f])
for c in m.clips:
    ts = m.clip_times(c); t1 = ts[-1]
    for t in np.append(np.arange(0, t1, 0.1), t1):
        P = np.asarray(m.skinned_positions(m.world(m.sample(c, t)))[0][0])
        d, _ = cKDTree(P[hand_v]).query(P[T].mean(1), distance_upper_bound=R)
        hit |= target & (d < R)
        C = P[T].mean(1)
        dl, _ = cKDTree(P[hv_r]).query(C, distance_upper_bound=RH)
        dr, _ = cKDTree(P[hv_l]).query(C, distance_upper_bound=RH)
        hit |= hand_f & ((left_f & (dl < RH)) | (~left_f & (dr < RH)))
n0 = int(hit.sum())
rest = np.asarray(m.primitives[0]['positions'], float); cen = rest[T].mean(1)
dist, nn = cKDTree(cen).query(cen[hit] * [-1, 1, 1])
hit[nn[dist < 0.01]] = True
hit &= target | hand_f
print('HANDCONTACT', n0, 'faces, mirrored', int(hit.sum()), {n: int((hit & (part == names.index(n))).sum()) for n in ('robe', 'torso', 'sleeves', 'belt', 'hands')})
np.save(HERE / 'work' / 'keep_hand.npy', hit)
