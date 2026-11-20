#!/usr/bin/env python3
"""Misplaced cap fans on the welded source (work/mesh_in.npz): around each vertex, its faces split into wedges
(faces joined through a shared non-hub vertex); a wedge whose rim is small but whose hub lies far from the rim
(hub distance > max(15 mm, 2.5 x rim radius)) is a hole cap fanned to a wrong point (the Meshy source capped twelve
left-hand holes with one shared vertex, drawn as a spike). -> work/hub_caps.json [{hub, faces, rim}]; prints them."""
import json
import numpy as np
d = np.load('work/mesh_in.npz'); V, F = d['verts'], d['faces']
vf = [[] for _ in V]
for i, f in enumerate(F):
    for v in f: vf[v].append(i)
caps = []
for h in range(len(V)):
    fs = vf[h]
    if len(fs) < 3: continue
    par = {f: f for f in fs}
    def find(a):
        while par[a] != a: a = par[a]
        return a
    for i in fs:
        for j in fs:
            if i < j and set(F[i]) & set(F[j]) - {h}: par[find(j)] = find(i)
    wedges = {}
    for f in fs: wedges.setdefault(find(f), []).append(f)
    if len(wedges) < 2: continue
    for w in wedges.values():
        rim = sorted(set(F[w].ravel()) - {h}); c = V[rim].mean(0)
        radius = max(np.linalg.norm(V[rim] - c, axis=1)); dist = np.linalg.norm(V[h] - c)
        if dist > max(.015, 2.5 * radius):
            caps.append({'hub': int(h), 'faces': [int(x) for x in w], 'rim': [int(x) for x in rim],
                         'dist_mm': round(float(dist) * 1000, 1), 'radius_mm': round(float(radius) * 1000, 1)})
for c in caps: print(c['hub'], len(c['faces']), 'faces, hub %.0f mm from rim of radius %.0f mm' % (c['dist_mm'], c['radius_mm']), np.round(V[c['rim']].mean(0), 3))
json.dump(caps, open('work/hub_caps.json', 'w')); print('CAPS', len(caps))
