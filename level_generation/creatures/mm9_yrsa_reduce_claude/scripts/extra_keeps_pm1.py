#!/usr/bin/env python3
"""Extra keep faces for PeasantM1 set e (see-through of d70: the gate's growth was +1..+7 px on holes the installed already has,
at the sleeve ends, the jacket front edge, the left boot top and the collar; scripts/st_probe.py on six of those clip/frame/views,
installed and d70, work/probe/*.json): every body face (jacket, shirt front, boots) with its centroid within NEAR m of a face
the hole pixels hit in either GLB, plus the MPFB forearm skin (group 5, the hand-graft side of the sleeve ends).
Probe rest centroids are Blender's re-based import (glTF y = probe y + OFFSET, mpqem's BLENDER OFFSET).
-> work/keep_e.npy (per LOD0 face, glb_parts.npz order). Usage: extra_keeps_pm1.py"""
import glob, json, os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
_, _, _, D = glbio.load(HERE / 'before' / 'mm9_peasantm1.glb', 'PeasantM1')
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']
PR = ['PeasantM1_A', 'PeasantM1Head']
P = np.concatenate([D[k]['P'] for k in PR]); T = np.concatenate([D[k]['T'] + g['voff'][i] for i, k in enumerate(PR)])
C = P[T].mean(1); OFFSET = float(os.environ.get('OFFSET', '0.854568')); NEAR = float(os.environ.get('NEAR', '0.04'))
hits = []
for f in glob.glob(str(HERE / 'work' / 'probe' / '*.json')):
    for o in json.load(open(f))['faces']:
        x, y, z = o['rest_gltf']; hits.append((x, y + OFFSET, z))
hits = np.array(hits)
dist = cKDTree(C).query(hits)[0]
print('hit faces', len(hits), 'match to a GLB face centroid: p50 / max mm', np.round(np.median(dist) * 1000, 2), np.round(dist.max() * 1000, 2))
near = cKDTree(hits).query(C)[0] < NEAR
keep = (near & np.isin(part, (1, 3, 8)))
ss = np.load(HERE / 'work' / 'glb_sets_d.npz'); forearm = ss['group'] == 5
keep |= forearm
print('near', int((near & np.isin(part, (1, 3, 8))).sum()), {int(p): int((near & (part == p)).sum()) for p in (1, 3, 8)},
      'forearm skin', int(forearm.sum()), 'new beyond set d', int((keep & ~ss['keep']).sum()))
np.save(HERE / 'work' / 'keep_e.npy', keep)
