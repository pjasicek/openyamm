"""Per-creature settings for the batch-B robed-caster chain (work/../creature.json), shared by the scripts.
Garment numbering is the same for every creature of the batch:
 0 skin (head + hands)    1 robe top + sleeves      2 skirt               3 head-rigid (helmet, mask, cap)
 4 eyes (head set)        5 head-rigid small parts  6 collar (no arm wt)  7 chest-rigid ornaments (B_Spine2)
 8 hanging cords/strips that follow the robe chains (rope ends, stole)    9 back-rigid large (crescent)
10 simulated sheets (banners)  11 back-rigid small (rods, beads)  12 hair (head -> neck -> chest blend)
13 mantle / capelet (Meshy weights, arm share limited)                    14 held prop (rigid on a hand bone)"""
import json, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = json.load(open(os.path.join(HERE, 'work', 'source_creature.json')))
GARMENTS = {int(k): v for k, v in C['garments'].items()}
LAB = {p: g for g, ps in GARMENTS.items() for p in ps}
HANDS = C['hands']                                   # {"L": piece, "R": piece}
NOT_IN_RIG = set(C.get('not_in_rig_upload', [9, 10, 11]))


def hand_mask(co, pv, side, wrist, forearm, fade=0.025, reach=0.26):
    """Hand vertices of one side: the hand piece beyond (wrist plane - fade) within reach of the wrist on that side
    (hands may share one skin piece with the body and the other hand)."""
    import numpy as np
    d = (wrist - forearm) / np.linalg.norm(wrist - forearm)
    rel = co - wrist; along = rel @ d
    m = ((pv == HANDS[side]) & (along > -fade) & (np.linalg.norm(rel, axis=1) < reach)
         & (np.sign(co[:, 0]) == (1 if side == 'L' else -1)))
    if 'hand_axis_r' in C:                           # a hand fused with a hanging cape: stay near the forearm axis line
        m &= np.linalg.norm(rel - np.outer(along, d), axis=1) < C['hand_axis_r']
    return m
