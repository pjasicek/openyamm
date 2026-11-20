#!/usr/bin/env python3
"""Arm contact faces of the installed LOD0 (a74: the Sleep left forearm went 0.0 -> 1.1 cm into the body when the belly
and sleeves were decimated; the monk lesson): over every 2nd key time of every clip, body faces (limbs/torso primitives,
not arm) whose posed centroid comes within R m of a posed forearm/hand vertex, and arm faces whose centroid comes within
R m of a posed body vertex. Arm = dominant joint Forearm, Forearm_h, Hand or a finger. Writes work/arm_contact.npy
(per GLB face, primitives in order). Usage: arm_contact.py  (env R, default 0.02)"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
R = float(os.environ.get('R', '0.02'))
m = Model(Glb(str(HERE / 'before' / 'mm9_dookmilitia.glb')))
nm = [n.get('name') for n in m.glb.json['nodes']]; jn = [nm[j] for j in m.joints]
isarm = np.array([any(s in n for s in ('Forearm', 'Hand', 'Index', 'Middle', 'Ring', 'Pinky', 'Thumb', 'Finger')) for n in jn])
prims = m.primitives[:2]
dom = [np.asarray(p['joints'])[np.arange(len(p['weights'])), np.asarray(p['weights']).argmax(1)] for p in prims]
armv = [isarm[d] for d in dom]
T = [np.asarray(p['triangles']) for p in prims]
armf = [a[t].sum(1) >= 2 for a, t in zip(armv, T)]
hit = [np.zeros(len(t), bool) for t in T]
for clip in m.clips:
    for t in m.clip_times(clip)[::2]:
        posed = m.skinned_positions(m.world(m.sample(clip, t)))
        P = [np.asarray(posed[i][0]) for i in range(2)]
        av = np.vstack([P[i][armv[i]] for i in range(2)]); bv = np.vstack([P[i][~armv[i]] for i in range(2)])
        ta, tb = cKDTree(av), cKDTree(bv)
        for i in range(2):
            c = P[i][T[i]].mean(1)
            da, _ = ta.query(c, distance_upper_bound=R); db, _ = tb.query(c, distance_upper_bound=R)
            hit[i] |= (~armf[i] & (da < R)) | (armf[i] & (db < R))
nall = sum(len(p['triangles']) for p in m.primitives)
mask = np.zeros(nall, bool); mask[:len(T[0])] = hit[0]; mask[len(T[0]):len(T[0]) + len(T[1])] = hit[1]
print('ARMCONTACT body faces', int(sum((~a & h).sum() for a, h in zip(armf, hit))), 'arm faces', int(sum((a & h).sum() for a, h in zip(armf, hit))))
np.save(HERE / 'work' / 'arm_contact.npy', mask)
