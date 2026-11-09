#!/usr/bin/env python3
"""Extra keep sets for the arm/hand and jitter gates (first build i68: Death L hand 3.9 -> 4.5 cm, AttackMelee L shoulder skin
0.14 -> 2.27 mm/f2 over the 2.0 limit).
- shoulder: every body face touching a vertex dominated by a Clavicle or UpperArm bone (the jitter gate's shoulder-skin set; kept
  whole, the set and its motion are the installed ones);
- contact: body faces (not arm-dominated) whose posed centroid lies within R of the side's hand/forearm vertices at the frames
  where the installed arm/hand gate reports the arm inside the body (review/gates_before/arm_hand.json, 48 fps), +-2 frames.
Writes work/keep_extra_<tag>.npy (per GLB face, both primitives). Usage: contact_lock.py <tag> [R] [gate dirs...]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model
import bglbio
tag = sys.argv[1]; R = float(sys.argv[2]) if len(sys.argv) > 2 else 0.05
f = HERE / 'before' / 'mm9_lesserdemon.glb'; m = Model(Glb(str(f))); doc, b = bglbio.read(f)
jn = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]; pr = bglbio.prims(doc, b, 0)
B = pr[0]; T = B['T']; nB = len(T); nH = len(pr[1]['T'])
dom = np.array([jn[j] for j in B['JOINTS_0'][np.arange(len(B['POSITION'])), B['WEIGHTS_0'].argmax(1)]])
shoulder = np.array([d.endswith('Clavicle') or d.endswith('UpperArm') for d in dom])
keep = np.zeros(nB + nH, bool); keep[:nB] = shoulder[T].any(1); n_sh = int(keep.sum())
arm = {s: np.array([f' {s} ' in d and any(k in d for k in ('Hand', 'Finger', 'Forearm')) for d in dom]) for s in 'LR'}
armany = arm['L'] | arm['R'] | np.array(['UpperArm' in d for d in dom])
host = ~armany[T].any(1)
events = set()
for gd in sys.argv[3:] or ['before']:     # the installed gate and the candidates' gates: their worst frames
    for clip, sides in json.load(open(HERE / 'review' / f'gates_{gd}' / 'arm_hand.json'))['clips'].items():
        for s in 'LR':
            g = sides[s]
            for part in ('hand', 'forearm'):
                if g[f'{part}_in_body_cm'] > 0.1:
                    events.add((clip, s, g[f'{part}_frame48']))
events = sorted(events)
print('EVENTS', events)
cont = np.zeros(nB, bool)
for clip, s, fr in events:
    for df in (-2, -1, 0, 1, 2):
        t = min(max((fr + df) / 48.0, 0), m.clip_times(clip)[-1])
        X = m.skinned_positions(m.world(m.sample(clip, t)))[0][0]
        d, _ = cKDTree(X[arm[s]]).query(X[T].mean(1)); cont |= host & (d < R)
keep[:nB] |= cont
print('KEEP extra', tag, 'shoulder faces', n_sh, 'contact faces', int(cont.sum()), 'total', int(keep.sum()))
np.save(HERE / 'work' / f'keep_extra_{tag}.npy', keep)
