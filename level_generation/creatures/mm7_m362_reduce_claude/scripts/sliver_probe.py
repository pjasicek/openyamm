#!/usr/bin/env python3
"""The source project's find_slivers.py / find_long_faces.py criteria (copied beside this script; they read a blend's
`piece` attribute) on rest meshes in npz form, source vs candidate: slivers = longest edge > MINLEN (0.025 m) with
altitude over it < MAXALT (4 mm), with the largest normal angle to a vertex-neighbour face; long faces = longest edge
> 3 cm and > RATIO (3) x the median edge length around its vertices. Candidate faces that are not source faces are
reported as new. Usage: sliver_probe.py <source npz> <candidate npz>"""
import os, sys
import numpy as np
MINLEN, MAXALT, RATIO = float(os.environ.get('MINLEN', '0.025')), float(os.environ.get('MAXALT', '0.004')), float(os.environ.get('RATIO', '3'))


def probe(path):
    d = np.load(path); v, f = d['verts'], d['faces']; t = v[f]
    e = np.stack([np.linalg.norm(t[:, (k + 1) % 3] - t[:, k], axis=1) for k in range(3)], 1); L = e.max(1)
    cr = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); area = np.linalg.norm(cr, axis=1) / 2
    n = cr / (2 * area[:, None] + 1e-12); alt = 2 * area / np.maximum(L, 1e-12)
    vf = [[] for _ in v]; ve = [[] for _ in v]
    for i, (a, b, c) in enumerate(f):
        for x in (a, b, c):
            vf[x].append(i)
        for x, y, l in ((a, b, e[i, 0]), (b, c, e[i, 1]), (c, a, e[i, 2])):
            ve[x].append(l); ve[y].append(l)
    sl, lg = [], []
    for i in np.flatnonzero((L > MINLEN) & (alt < MAXALT)):
        nb = {j for x in f[i] for j in vf[x]} - {i}
        dev = max((np.degrees(np.arccos(np.clip(n[i] @ n[j], -1, 1))) for j in nb), default=0)
        sl.append((i, L[i], alt[i], dev))
    for i in np.flatnonzero(L > 0.03):
        ring = np.median([x for y in f[i] for x in ve[y]])
        if L[i] > RATIO * ring:
            lg.append((i, L[i], L[i] / ring))
    key = {tuple(np.round(np.sort(t[i], 0).ravel(), 6)) for i in range(len(f))}
    return d, t, sl, lg, key


S = probe(sys.argv[1]); C = probe(sys.argv[2])
for name, (d, t, sl, lg, key) in (('source', S), ('candidate', C)):
    print(f'{name}: faces {len(t)} slivers {len(sl)} (normal dev > 60: {sum(x[3] > 60 for x in sl)}) long faces {len(lg)}')
skey = S[4]; t = C[1]
new = lambda i: tuple(np.round(np.sort(t[i], 0).ravel(), 6)) not in skey
for i, L, alt, dev in sorted(C[2], key=lambda x: -x[1]):
    if new(i):
        print(f'  NEW SLIVER {i} long {L * 100:.1f} cm alt {alt * 1000:.1f} mm dev {dev:.0f} at {np.round(t[i].mean(0), 3)}')
for i, L, r in sorted(C[3], key=lambda x: -x[2]):
    if new(i):
        print(f'  NEW LONGFACE {i} long {L * 100:.1f} cm ratio {r:.1f} at {np.round(t[i].mean(0), 3)}')
print('NEW slivers', sum(new(x[0]) for x in C[2]), 'NEW long faces', sum(new(x[0]) for x in C[3]))
