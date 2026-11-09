#!/usr/bin/env python3
"""Crest and helmet-top points for the LOD build (playbook: thin top features vanish in the coarse LODs and pull the
picking bounds down; the Titan's crest top is the model's top, 711 units at the binding scale 374.06, the helmet top
655 units against the descriptor's 650): the crest's outermost vertex in every 10-degree sector of its fan (y-z
plane about the fan's lowest centre) on its upper half, on both faces of the fan (x < and > the crest's mid plane),
every crest vertex above 1.85 m,
and the helmet dome's highest vertex plus its highest vertex on each side (|x| > 1 cm, beside the crest).
Rest-pose Blender coordinates from work/mesh_in.npz (crest top band and helmet gold kept exactly at LOD0).
-> work/spike_points.json"""
import json
import numpy as np
d = np.load('work/mesh_in.npz'); v, f = d['verts'], d['faces']; p = np.load('work/pieces.npy')
cv = np.unique(f[p == 10]); ctr = np.array([v[cv, 1].mean(), v[cv, 2].min()])
ang = np.degrees(np.arctan2(v[cv, 2] - ctr[1], v[cv, 1] - ctr[0])); rad = np.hypot(v[cv, 2] - ctr[1], v[cv, 1] - ctr[0])
xm = np.median(v[cv, 0]); pts = [v[cv[np.argmax(v[cv, 2])]]]
for a0 in range(0, 180, 10):
    for side in (v[cv, 0] < xm, v[cv, 0] >= xm):
        m = (ang >= a0) & (ang < a0 + 10) & side
        if m.any():
            pts.append(v[cv[m][np.argmax(rad[m])]])
# every crest vertex above 1.85 m too (with the sector points alone LOD1-3 rose 0.8 mm above the crest top)
pts += list(v[cv[v[cv, 2] > 1.85]])
hv = np.unique(f[p == 8])
pts.append(v[hv[np.argmax(v[hv, 2])]])
for s in (-1, 1):
    m = hv[s * v[hv, 0] > 0.01]; pts.append(v[m[np.argmax(v[m, 2])]])
pts = np.unique(np.round(np.array(pts), 6), axis=0)
json.dump(pts.tolist(), open('work/spike_points.json', 'w'), indent=1)
print('SPIKE POINTS', len(pts), 'crest top z', round(float(v[cv, 2].max()), 4), 'helmet top z', round(float(v[hv, 2].max()), 4))
