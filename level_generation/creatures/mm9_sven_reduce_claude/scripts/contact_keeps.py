#!/usr/bin/env python3
"""Contact keeps (after a55: Applause R hand 2.1 -> 4.0 cm into the other hand, Fidget R forearm 2.9 -> 3.6 cm, both with the
hands cut at 0.6): every sampled pose of every clip (HZ, default 6), installed LOD0 posed by claude_shared/floor/glb_pose:
- hand faces (part 0) whose posed centroid comes within R m of a vertex of the OTHER hand or of any non-hand part;
- non-hand faces whose posed centroid comes within R m of a hand vertex.
-> work/keep_contact[_<MODE>].npy (glb_parts.npz face order). Usage: contact_keeps.py  (env R default 0.03, HZ, MODE, CLIPS)"""
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model  # noqa: E402
import glbio, cfg  # noqa: E402
R = float(os.environ.get('R', '0.03')); HZ = float(os.environ.get('HZ', '6'))
MODE = os.environ.get('MODE', 'all')   # all | hands (only hand faces near the OTHER hand: the Applause clap) | arm (below)
CLIPS = [c for c in os.environ.get('CLIPS', '').split(',') if c]
doc, binary, nd, D = glbio.load(HERE / 'before' / cfg.GLB, cfg.NODE)
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']; voff = g['voff']
T = np.concatenate([D[k]['T'] + voff[i] for i, k in enumerate(cfg.PR)])
P0 = np.concatenate([D[k]['P'] for k in cfg.PR])
hand = part == 0
hv = np.unique(T[hand])
# split the two hands by rest x sign (MPFB hands are separate pieces at +-x)
side_v = np.sign(P0[:, 0]); side_f = np.sign(P0[T].mean(1)[:, 0])
other_v = np.unique(T[~hand])
m = Model(Glb(str(HERE / 'before' / cfg.GLB)))
keep = np.zeros(len(T), bool)
# MODE=arm (after b65: Fidget R forearm 2.9 -> 3.6 cm into the fur lapels fused into the hair shell): faces with no
# arm-dominated vertex whose posed centroid comes within R m of a vertex dominated by a Forearm/Hand/finger joint
jn = [str(x) for x in g['jnames']]
Jall = np.concatenate([D[k]['J'] for k in cfg.PR]); Wall = np.concatenate([D[k]['W'] for k in cfg.PR])
domv = np.array(jn)[Jall[np.arange(len(Jall)), Wall.argmax(1)]] if len(jn) > Jall.max() else None
armv = np.array([any(k in x for k in ('Forearm', 'Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) for x in domv])
armup = np.array([any(k in x for k in ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Twist')) for x in domv])
nonarm_f = ~armv[T].any(1); armvi = np.flatnonzero(armv)  # faces touching a forearm/hand vertex are the arm itself
for clip in (CLIPS or m.clips):
    t1 = m.clip_times(clip)[-1]
    for t in np.append(np.arange(0, t1, 1 / HZ), t1):
        pz = m.skinned_positions(m.world(m.sample(clip, t)))
        X = np.concatenate([p for p, _ in pz]); C = X[T].mean(1)
        if MODE == 'arm':
            d, _ = cKDTree(X[armvi]).query(C[nonarm_f], distance_upper_bound=R); keep[np.flatnonzero(nonarm_f)[d < R]] = True
            continue
        for s in (-1, 1):
            own = hand & (side_f == s)
            tgt = hv[side_v[hv] == -s] if MODE == 'hands' else np.concatenate([hv[side_v[hv] == -s], other_v])
            d, _ = cKDTree(X[tgt]).query(C[own], distance_upper_bound=R); keep[np.flatnonzero(own)[d < R]] = True
        if MODE != 'hands':
            d, _ = cKDTree(X[hv]).query(C[~hand], distance_upper_bound=R); keep[np.flatnonzero(~hand)[d < R]] = True
np.save(HERE / 'work' / ('keep_contact.npy' if MODE == 'all' else f'keep_contact_{MODE}.npy'), keep)
print('contact keep', int(keep.sum()), {int(p): int((keep & (part == p)).sum()) for p in np.unique(part[keep])})
