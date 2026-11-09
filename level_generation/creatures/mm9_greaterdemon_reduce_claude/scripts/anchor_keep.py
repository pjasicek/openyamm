#!/usr/bin/env python3
"""Wing attachment keep (the creature's wing_review gap gate measures how far the buried wing root and the membrane's body
line come out of the posed body): wing-bone faces with a vertex that carries any non-wing bone weight (the root segment
blended from the body weights) and body-skin faces within RADIUS m of such a vertex or of a membrane vertex with body
weights (the body line) are kept exactly. Writes work/keep_extra_anchor.npy (GLB faces of all primitives).
Usage: anchor_keep.py [radius]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
R = float(sys.argv[1]) if len(sys.argv) > 1 else 0.05
doc, b = gb.read(HERE / 'before' / 'mm9_greaterdemon.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'GreaterDemon' and 'mesh' in n)
joints = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
wingj = np.array([n.startswith(('Xwing', 'Xwarm')) for n in joints])
pr = gb.prims(doc, b, node['mesh'])
sets = np.load(HERE / 'work' / 'glb_sets_a.npz')
nB, nW, nH = (len(p['T']) for p in pr)
wb = sets['wingbone'][:nB]
out = []
anchors = []
for k, p in enumerate(pr[:2]):
    J, W = p['JOINTS_0'], p['WEIGHTS_0'].astype(float)
    nonwing = (W * ~wingj[J]).sum(1) > 0.01
    T = p['T']
    if k == 0:
        sel = wb & nonwing[T].any(1)
        anchors.append(p['POSITION'][np.unique(T[sel])])
        tube = sel
    else:
        anchors.append(p['POSITION'][nonwing])
A = np.vstack(anchors).astype(float)
P = pr[0]['POSITION'].astype(float); T = pr[0]['T']
d = cKDTree(A).query(P)[0]
near = (d[T] < R).any(1) & ~wb
keep = np.r_[tube | near, np.zeros(nW + nH, bool)]
print(f'anchor vertices {len(A)}; kept wing-root faces {int(tube.sum())}, body skin near anchors {int(near.sum())}')
np.save(HERE / 'work' / 'keep_extra_anchor.npy', keep)
