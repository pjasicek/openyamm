#!/usr/bin/env python3
"""Why vertices of one mpqem_df group are locked (Prim's rules without poses): subset border (open edge), UV/normal seam,
lined/unlined border. Usage: lock_diag.py <sets tag> <prim index> <group>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio  # noqa: E402
tag, pi, gl = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
doc, b = bglbio.read(HERE / 'before' / 'mm9_peasantdf1.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantDF' and 'mesh' in n)
prs = bglbio.prims(doc, b, node['mesh']); pr = prs[pi]
sets = np.load(HERE / 'work' / f'glb_sets_{tag}.npz'); nb = len(prs[0]['T']); sl = slice(0, nb) if pi == 0 else slice(nb, None)
keep, group, lining, lined = (sets[k][sl] for k in ('keep', 'group', 'lining', 'lined'))
T = pr['T']; P = pr['POSITION'].astype(np.float64); J = pr['JOINTS_0']; W = pr['WEIGHTS_0'].astype(np.float64)
key = np.concatenate([np.round(P, 6), J.astype(np.float64), np.round(W, 4)], 1)
_, topo = np.unique(key, axis=0, return_inverse=True); topo = topo.ravel()
sub = np.flatnonzero(~keep & ~lining & (group == gl)); TF = topo[T[sub]]
edges = {}
for f, t in enumerate(TF):
    for a, c in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
        edges.setdefault((min(a, c), max(a, c)), []).append(f)
border = set()
for (a, c), fs in edges.items():
    if len(fs) != 2: border |= {a, c}
glbs = {}
for t, g in zip(TF.ravel(), T[sub].ravel()): glbs.setdefault(t, set()).add(g)
seam = {v for v, s in glbs.items() if len(s) > 1}
_, tp = np.unique(np.round(P, 6), axis=0, return_inverse=True); tp = tp.ravel()
inl = np.zeros(tp.max() + 1, bool); inl[tp[T[lined]].ravel()] = True
inu = np.zeros(tp.max() + 1, bool); inu[tp[T[~lined & ~lining]].ravel()] = True
lb = {topo[g] for g in np.flatnonzero((inl & inu)[tp])}
allv = set(TF.ravel().tolist())
free = allv - border - seam - lb
print(f'group {gl}: faces {len(sub)} verts {len(allv)} border {len(border & allv)} seam {len(seam)} lined-border {len(lb & allv)} '
      f'seam-only {len(seam - border - lb)} lb-only {len(lb & allv - border - seam)} free {len(free)}')
# faces with all three vertices locked can never be removed
lockedv = allv - free
print('faces with no free vertex', int(np.all(np.isin(TF, list(lockedv)), 1).sum()))
