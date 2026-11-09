#!/usr/bin/env python3
"""Close-up spots where an earlier candidate's LOD0 faces left the painted charts (reduction_uv_audit.py JSON): escaping face
centroids clustered greedily (radius 7 cm), the N heaviest clusters (colour error x area) with their mean normal, in Blender
coordinates. Usage: escape_spots.py <audit.json> <out.json> [N]"""
import json, sys
import numpy as np
d = json.load(open(sys.argv[1])); N = int(sys.argv[3]) if len(sys.argv) > 3 else 8
F = [f for node in (d['nodes'].values() if isinstance(d['nodes'], dict) else d['nodes']) for lod in node[:1] for p in lod for f in p['faces_list']]
c = np.array([f['centroid'] for f in F]); n = np.array([f['normal'] for f in F]); w = np.array([f['colour_err'] * f['area_mm2'] for f in F])
left = np.ones(len(F), bool); spots = []
while left.any():
    i = np.flatnonzero(left)[np.argmax(w[left])]; m = left & (np.linalg.norm(c - c[i], axis=1) < 0.07)
    nn = (n[m] * w[m, None]).sum(0); nn /= np.linalg.norm(nn) + 1e-12; p = c[m].mean(0)
    spots.append({'faces': int(m.sum()), 'weight': float(w[m].sum()), 'p': [p[0], -p[2], p[1]], 'n': [nn[0], -nn[2], nn[1]]}); left &= ~m
spots.sort(key=lambda s: -s['weight']); json.dump(spots[:N], open(sys.argv[2], 'w'), indent=1)
print('SPOTS', len(spots), 'clusters of', len(F), 'faces; kept', [(s['faces'], round(s['weight'])) for s in spots[:N]])
