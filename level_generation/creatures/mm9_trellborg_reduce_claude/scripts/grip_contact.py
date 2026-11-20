#!/usr/bin/env python3
"""Grip contact of the right (cutlass) hand: body faces of the installed LOD0 weighted to the right hand or fingers whose
centre comes within CONTACT m (default 1.5 cm) of the cutlass surface (its vertices and face centres) at any of 6 times
of every clip. These stay exact when the rest of the hand is decimated (relaxed prio-1 keep set: "hands at 0.6-0.75
keeping every finger, the grip contact and the hand-graft junction"). Writes work/grip_contact.npy (per GLB face)."""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
C = float(os.environ.get('CONTACT', '0.015'))
m = Model(Glb(str(HERE / 'before' / 'mm9_lizardorc.glb')))
nm = [n.get('name') for n in m.glb.json['nodes']]; jn = [nm[j] for j in m.joints]
rh = np.array([n.startswith('Bip01 R Finger') or n == 'Bip01 R Hand' for n in jn])
nf = [len(p['triangles']) for p in m.primitives]; off = np.cumsum([0] + nf)
hw = [(rh[p['joints']] * p['weights']).sum(1)[p['triangles']].max(1) for p in m.primitives]
cand = [np.where(h > 0.01)[0] if i < 2 else np.zeros(0, int) for i, h in enumerate(hw)]
best = [np.full(len(c), 9.0) for c in cand]
for clip in m.clips:
    ts = m.clip_times(clip); 
    for t in np.linspace(ts[0], ts[-1], 6):
        posed = m.skinned_positions(m.world(m.sample(clip, t)))
        wp, wt = posed[3]; tree = cKDTree(np.vstack([wp, wp[wt].mean(1)]))
        for i in (0, 1):
            p, tr = posed[i]
            d, _ = tree.query(p[tr[cand[i]]].mean(1)); best[i] = np.minimum(best[i], d)
mask = np.zeros(off[-1], bool)
for i in (0, 1):
    mask[off[i] + cand[i][best[i] < C]] = True
print('right hand faces', sum(len(c) for c in cand), 'contact', int(mask.sum()))
np.save(HERE / 'work' / 'grip_contact.npy', mask)
