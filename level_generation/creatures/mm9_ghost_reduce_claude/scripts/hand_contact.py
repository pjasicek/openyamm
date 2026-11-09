#!/usr/bin/env python3
"""Faces the hands come near in the clips (after mm9_nosferatu_reduce_claude/scripts/hand_contact.py): every non-hand face of
the body and of the opposite arm with a vertex within DIST of a hand vertex in any pose (every clip at 30 Hz) ->
work/hand_contact.npz (per material bool per face). The own arm's sleeve is left out (the cuff is kept by make_sets.py).
Why: candidate Cr45 put the left hand 2.5 cm into the reduced jacket front in AttackMelee (installed 0.0, arm/hand gate).
Also hand faces within DIST_HH of the other hand: Cr45's coarser right thumb (R Thumb3 at 50 %) read the left fingertips
clasped against it in AttackMelee as 2.5 cm inside. Death and Dead are skipped (the Ghost shrinks to a speck).
Usage: hand_contact.py   (env DIST=0.04 DIST_HH=0.015)"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model  # noqa: E402
import glbio  # noqa: E402
SRC = HERE.parent / 'mm9_ghost_claude' / 'export' / 'mm9_ghost_runtime_lod0.glb'
DIST = float(os.environ.get('DIST', '0.04')); DIST_HH = float(os.environ.get('DIST_HH', '0.015'))
doc, b = glbio.read(SRC); prims = glbio.prims(doc, b, 0)
names = np.array([doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']])
ishand = np.array([n.startswith('Finger') or n.startswith('Zhand') or n.startswith('Zfing') for n in names])
right = np.array([('01' in n) or (' R ' in n) for n in names])
m = Model(Glb(str(SRC)))
info = []
for p in prims:
    J = p['JOINTS_0']; W = p['WEIGHTS_0'].astype(np.float64); dom = J[np.arange(len(J)), W.argmax(1)]
    fh = ishand[dom][p['T']].mean(1) > 0.5
    hv = {s: np.unique(p['T'][fh & ((right[dom][p['T']].mean(1) > 0.5) == (s == 'R'))]) for s in 'LR'}
    side = 'L' if p['material'] == 'GhostArmL' else 'R' if p['material'] == 'GhostArmR' else None
    info.append((fh, hv, side))
near = [np.zeros(len(p['T']), bool) for p in prims]
hh = [np.zeros(len(p['T']), bool) for p in prims]
for clip in m.clips:
    if clip in ('Death', 'Dead'):               # the Ghost shrinks to a speck: everything comes within DIST
        continue
    t1 = m.clip_times(clip)[-1]
    for t in np.append(np.arange(0, t1, 1 / 30), t1):
        posed = [q for q, _ in m.skinned_positions(m.world(m.sample(clip, t)))]
        for s in 'LR':
            H = np.concatenate([posed[i][info[i][1][s]] for i in range(len(prims)) if prims[i]['material'] != 'GhostHead'])
            if not len(H):
                continue
            tree = cKDTree(H)
            for i, p in enumerate(prims):
                if p['material'] == 'GhostHead' or info[i][2] == s:
                    continue
                d = tree.query(posed[i][p['T']].reshape(-1, 3), distance_upper_bound=DIST)[0].reshape(-1, 3).min(1)
                near[i] |= (d < DIST) & ~info[i][0]
            # hand faces of the other hand within DIST_HH of this hand (AttackMelee clasps them)
            for i, p in enumerate(prims):
                if p['material'] == 'GhostHead':
                    continue
                o = 'R' if s == 'L' else 'L'
                fo = np.zeros(len(p['T']), bool); fo[:] = False
                ov = info[i][1][o]
                if not len(ov):
                    continue
                mo = np.isin(p['T'], ov).all(1) & info[i][0]
                d = tree.query(posed[i][p['T'][mo]].reshape(-1, 3), distance_upper_bound=DIST_HH)[0].reshape(-1, 3).min(1)
                hh[i][np.flatnonzero(mo)[d < DIST_HH]] = True
np.savez(HERE / 'work' / 'hand_contact.npz', **{p['material']: n | h for p, n, h in zip(prims, near, hh)})
print('HAND CONTACT body', {p['material']: int(n.sum()) for p, n in zip(prims, near)}, 'hand to hand', {p['material']: int(h.sum()) for p, h in zip(prims, hh)})
