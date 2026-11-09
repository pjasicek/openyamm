#!/usr/bin/env python3
"""Folded fins on the welded source (work/mesh_in.npz): interior edges in the hand regions (work/regions.npy 2 left,
3 right, faces within REGION_PAD of a hand face count too) whose two faces bend by more than LIMIT degrees
(a flat surface 0, a knife-edge fold about 180). Prints edges with length and position; saves work/fold_faces.npy
(faces on those edges). Usage: fold_probe.py [limit=140]"""
import sys
import numpy as np
LIMIT = float(sys.argv[1]) if len(sys.argv) > 1 else 140
d = np.load('work/mesh_in.npz'); V, F = d['verts'], d['faces']; reg = np.load('work/regions.npy')
n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
ef = {}
for i, f in enumerate(F):
    for k in range(3): ef.setdefault(tuple(sorted((f[k], f[(k + 1) % 3]))), []).append(i)
hand = np.isin(reg, [2, 3])
bad = set(); rows = []
for e, fs in ef.items():
    if len(fs) != 2 or not hand[fs].any(): continue
    a = np.degrees(np.arccos(np.clip(n[fs[0]] @ n[fs[1]], -1, 1)))
    if a > LIMIT:
        bad |= set(fs); L = np.linalg.norm(V[e[0]] - V[e[1]])
        rows.append((round(a), round(L * 1000, 1), 'L' if (reg[fs] == 2).any() else 'R', fs, np.round((V[e[0]] + V[e[1]]) / 2, 3)))
for r in sorted(rows, key=lambda r: -r[1]): print(*r)
np.save('work/fold_faces.npy', np.array(sorted(bad), int)); print('FOLD EDGES', len(rows), 'faces', len(bad))
