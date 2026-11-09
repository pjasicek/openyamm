#!/usr/bin/env python3
"""Shoulder cloth keep (PeasantM2d's lesson for the jitter gate's shoulder-skin sample: p95 over the vertices dominated by a
Clavicle or UpperArm joint; a cut leaves fewer, and the p95 moves onto the fast minority): every body-prim face touching such a
vertex -> work/keep_shoulder.npy (GLB face indices, prim order). Usage: keep_shoulder.py"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio  # noqa: E402
doc, b = bglbio.read(HERE / 'before' / 'mm9_peasantm3.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantM3' and 'mesh' in n)
pr = bglbio.prims(doc, b, node['mesh'])[0]
jn = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
J, W, T = pr['JOINTS_0'].astype(int), pr['WEIGHTS_0'].astype(float), pr['T']
acc = np.zeros((len(J), len(jn)))
for i in range(4):
    np.add.at(acc, (np.arange(len(J)), J[:, i]), W[:, i])
dom = acc.argmax(1)
sh = np.array([jn[j].endswith('Clavicle') or jn[j].endswith('UpperArm') for j in dom])
f = np.flatnonzero(sh[T].any(1))
print('SHOULDER vertices', int(sh.sum()), 'faces', len(f)); np.save(HERE / 'work' / 'keep_shoulder.npy', f)
