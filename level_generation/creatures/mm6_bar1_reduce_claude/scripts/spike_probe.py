#!/usr/bin/env python3
"""Spike tips on the welded source (work/mesh_in.npz): interior vertices whose adjacent face angles sum to less than
LIMIT degrees (a smooth surface vertex sums to about 360) inside the hand regions (work/regions.npy 2 left, 3 right),
with the spike length (distance to the mean of its neighbours). Usage: spike_probe.py [limit=150]"""
import sys
import numpy as np
LIMIT = float(sys.argv[1]) if len(sys.argv) > 1 else 150
d = np.load('work/mesh_in.npz'); V, F = d['verts'], d['faces']; reg = np.load('work/regions.npy')
ang = np.zeros(len(V)); nb = [set() for _ in V]; edges = {}
for f in F:
    for k in range(3):
        a, b, c = f[k], f[(k + 1) % 3], f[(k + 2) % 3]
        u, v = V[b] - V[a], V[c] - V[a]
        ang[a] += np.degrees(np.arccos(np.clip(u @ v / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-12), -1, 1)))
        nb[a] |= {b, c}; e = tuple(sorted((a, b))); edges[e] = edges.get(e, 0) + 1
boundary = {v for e, n in edges.items() if n == 1 for v in e}
vreg = np.zeros(len(V), int)
for f, r in zip(F, reg): vreg[f] = np.maximum(vreg[f], r)
out = []
for v in range(len(V)):
    if v in boundary or vreg[v] not in (2, 3) or ang[v] >= LIMIT: continue
    length = np.linalg.norm(V[v] - V[list(nb[v])].mean(0))
    out.append((v, 'L' if vreg[v] == 2 else 'R', round(ang[v]), round(length * 1000, 1), np.round(V[v], 3)))
for o in sorted(out, key=lambda o: -o[3]): print(*o)
np.save('work/spike_tips.npy', np.array([o[0] for o in out], int))
print('SPIKES', len(out), 'boundary verts in hands', sum(1 for v in boundary if vreg[v] in (2, 3)))
