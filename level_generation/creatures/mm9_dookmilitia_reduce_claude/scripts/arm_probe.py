#!/usr/bin/env python3
"""Where the arm gate's forearm depth comes from: runs ../mm9_lizardorc_claude/scripts/arm_hand_gate.py's setup (outer
faces, exact depth) on <glb> and prints, for <clip> at the given 48 fps frames, the deepest forearm vertices of <side>
with their rest position and the dominant joint of the body face they are behind. Run from the creature project.
Usage: arm_probe.py <glb> <side L|R> <clip> <frame,...>"""
import runpy, sys
import numpy as np
from scipy.spatial import cKDTree
glb, side, clip, frames = sys.argv[1:5]
sys.argv = ['g', glb, '/dev/null', '--side', "L= L ", '--side', "R= R ", '--outer-only', '--exact', '--clips', 'none']
g = runpy.run_path('scripts/arm_hand_gate.py')
d = g['SID'][side]; tris = g['tris']; dom = g['dom']; rest = g['rest']
for f in [int(x) for x in frames.split(',')]:
    w, X = g['posed'](clip, f / 48.0)
    dep = g['exact_depth'](X[d['fv']], X, d['body_f'])
    for k in np.argsort(-dep)[:4]:
        if dep[k] <= 0: continue
        v = d['fv'][k]; T = X[tris[d['body_f']]]; c = T.mean(1); _, j = cKDTree(c).query(X[v])
        fb = d['body_f'][j]
        print(f'{clip}@{f} depth {dep[k]*100:.1f} cm forearm vert rest {np.round(rest[v],3)} dom {dom[v]} | behind face dom {[dom[i] for i in tris[fb]]} rest {np.round(rest[tris[fb]].mean(0),3)}')
