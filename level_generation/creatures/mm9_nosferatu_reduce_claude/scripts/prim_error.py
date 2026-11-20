#!/usr/bin/env python3
"""(Nosferatu copy: per part of the body primitive, labels from work/glb_parts.npz.) Per-part deviation of pose-aware steps over every clip (10 Hz), without Blender: distance from every source vertex
to the step's surface of the same primitive (triangles sampled densely, so slightly high), p99 / max in mm and where.
Usage: prim_error.py <runtime_lod0.glb> <tag> [tag...]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model  # noqa: E402
import glbio  # noqa: E402
g = Glb(sys.argv[1]); model = Model(g); doc, b = glbio.read(sys.argv[1]); prims = glbio.prims(doc, b, 0)
names = [p['material'] for p in prims]
poses = []
for clip in model.clips:
    t1 = model.clip_times(clip)[-1]
    for t in np.append(np.arange(0, t1, 0.1), t1):
        poses.append((clip, round(float(t), 2), [p for p, _ in model.skinned_positions(model.world(model.sample(clip, t)))]))
n = 6; bary = np.array([(i / n, j / n, 1 - (i + j) / n) for i in range(n + 1) for j in range(n + 1 - i)])
gp = np.load(HERE / 'work' / 'glb_parts.npz'); pn = [str(x) for x in gp['names']]
P0 = prims[0]['T']; bpart = gp['part'][gp['mat'] == 0]
vpart = -np.ones(len(prims[0]['POSITION']), int)
for k in range(len(pn)):
    vpart[np.unique(P0[bpart == k])] = k
for tag in sys.argv[2:]:
    d = np.load(HERE / 'work' / f'mp_{tag}.npz')
    T0 = d['Nosferatu_A']; tpart = vpart[T0[:, 0]]
    for k, name in enumerate(pn):
        T = T0[tpart == k]
        if len(T) == (bpart == k).sum():
            continue
        used = np.unique(P0[bpart == k])
        worst = []; allv = []
        for clip, t, pz in poses:
            X = pz[0]; pts = np.einsum('bk,fkd->fbd', bary, X[T]).reshape(-1, 3)
            dist = cKDTree(pts).query(X[used])[0]
            allv.append(dist); worst.append((dist.max(), clip, t))
        allv = np.concatenate(allv); w = max(worst)
        print(f'{tag} {name:10s} tris {len(T):5d} p99 {np.percentile(allv, 99) * 1000:6.2f} max {w[0] * 1000:6.2f} at {w[1]}:{w[2]}', flush=True)
