#!/usr/bin/env python3
"""Rest gaps between touching pieces after the whole cut (sweep_groups.py measures each group alone against the source, so two
reduced neighbours can open a joint together: d95 opened boot/knee 4 -> 11.5 mm, gauntlet/bracer 0.06 -> 1.8 mm). For every pair
of source pieces closer than NEAR at rest (mesh_in.npz, no linings), the gap in work/mesh_r<tag>.npz between the faces that came
from them (candidate faces mapped to source pieces by the nearest source face). Prints pairs whose gap grew by more than GROW mm
with their decimation groups. Usage: pair_gaps.py <tag> [GROW mm, default 1.0]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from pieces import pieces  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
NEAR = 0.005   # contact: rest gap under NEAR; candidates are found by vertices within SEARCH (large faces have far vertices)
SEARCH = 0.03
tag = sys.argv[1]; GROW = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
V, F, mat, comp, info = pieces(str(HERE / 'work'))
G = np.load(HERE / 'work' / 'groups.npy')
d = np.load(HERE / 'work' / f'mesh_r{tag}.npz'); CV, CF = d['verts'], d['faces']
_, near = cKDTree(V[F].mean(1)).query(CV[CF].mean(1)); ccomp = comp[near]


def gap(PA, FA, PB, FB):
    vs = PA[np.unique(FA)]
    k = min(64, len(FB)); _, nn = cKDTree(PB[FB].mean(1)).query(vs, k=k); f = nn.reshape(len(vs), -1).ravel()
    q, _ = closest_on_triangles(np.repeat(vs, k, 0), PB[FB[f, 0]], PB[FB[f, 1]], PB[FB[f, 2]])
    return float(np.linalg.norm(q - np.repeat(vs, k, 0), axis=1).min())


ks = [k for k in np.unique(comp) if info[int(k)]['mat'] != 2]
tree = cKDTree(V); out = []
for a in ks:
    sa = comp == a; va = np.unique(F[sa])
    hits = {int(comp[f]) for f in np.flatnonzero(np.isin(F, [j for h in tree.query_ball_point(V[va], SEARCH) for j in h]).any(1))}
    for b in sorted(hits):
        if b <= a or info[b]['mat'] == 2:
            continue
        sb = comp == b
        g0 = min(gap(V, F[sa], V, F[sb]), gap(V, F[sb], V, F[sa]))
        if g0 > NEAR:
            continue
        ca, cb = ccomp == a, ccomp == b
        if not ca.any() or not cb.any():
            continue
        g1 = min(gap(CV, CF[ca], CV, CF[cb]), gap(CV, CF[cb], CV, CF[ca]))
        ga, gb = sorted({int(x) for x in G[sa]}), sorted({int(x) for x in G[sb]})
        out.append((g1 - g0, a, b, g0, g1, ga, gb))
out.sort(reverse=True)
bad = [o for o in out if o[0] * 1000 > GROW]
import os
for dg, a, b, g0, g1, ga, gb in (out if os.environ.get("ALL") else bad):
    print(f"GROW {dg * 1000:5.2f} mm  {info[a]['bone']} n{info[a]['n']} groups {ga} | {info[b]['bone']} n{info[b]['n']} groups {gb}: {g0 * 1000:.2f} -> {g1 * 1000:.2f} mm")
print('PAIRS', len(out), 'grown over', GROW, 'mm:', len(bad))
json.dump([[float(o[0]), int(o[1]), int(o[2]), o[5], o[6]] for o in bad], open(HERE / 'work' / f'pair_gaps_{tag}.json', 'w'))
