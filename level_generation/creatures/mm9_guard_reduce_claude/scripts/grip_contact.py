#!/usr/bin/env python3
"""Grip contact of both fists (from mm9_lizardorc_reduce_claude, via the Highwayman's): hand faces of the installed LOD0 (Guard_A, weighted
to a hand or finger bone) whose centre comes within CONTACT m (default 1.5 cm) of the weapon surface (the halberd
vertices and face centres; work/gate_before.glb = installed body + halberd, merge_halberd.py) at 6 times of every clip. These stay exact while the rest of the hands is decimated (relaxed
prio-1 keep set). Writes work/grip_contact.npy (per GLB face, primitive order as glb_parts.py)."""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
C = float(os.environ.get('CONTACT', '0.015'))
m = Model(Glb(str(HERE / 'work' / 'gate_before.glb')))
nm = [n.get('name') for n in m.glb.json['nodes']]; jn = [nm[j] for j in m.joints]
hb = np.array([n.startswith('Bip01 R Finger') or n.startswith('Bip01 L Finger') or n in ('Bip01 R Hand', 'Bip01 L Hand')
               or any(n.startswith(f'Bip01 {s} {f}') for s in 'LR' for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) for n in jn])
print('hand bones', [n for n, h in zip(jn, hb) if h][:6], int(hb.sum()))
nf = [len(p['triangles']) for p in m.primitives[:2]]; off = np.cumsum([0] + nf)
p0 = m.primitives[0]
hw = (hb[p0['joints']] * p0['weights']).sum(1)[p0['triangles']].max(1)
cand = np.where(hw > 0.01)[0]; best = np.full(len(cand), 9.0)
for clip in m.clips:
    ts = m.clip_times(clip)
    for t in np.linspace(ts[0], ts[-1], 6):
        posed = m.skinned_positions(m.world(m.sample(clip, t)))
        wp, wt = posed[2]; tree = cKDTree(np.vstack([wp, wp[wt].mean(1)]))
        p, tr = posed[0]
        d, _ = tree.query(p[tr[cand]].mean(1)); best = np.minimum(best, d)
mask = np.zeros(off[-1], bool); mask[off[0] + cand[best < C]] = True
print('hand-weighted faces', len(cand), 'contact', int(mask.sum()))
np.save(HERE / 'work' / 'grip_contact.npy', mask)
