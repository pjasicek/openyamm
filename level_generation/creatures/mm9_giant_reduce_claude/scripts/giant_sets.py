#!/usr/bin/env python3
"""Face sets in GLB order for mpqem.py (fix pass): the keep mask and group labels of make_groups.py live on
work/mesh_in.npz faces (Blender import order); each GLB LOD0 face (primitives concatenated) is matched to its mesh_in face
by centroid (glTF -> Blender axes, plus the importer's re-basing offset). Writes work/glb_sets_<SETS>.npz (keep, group,
lining, lined). Usage: giant_sets.py <keep .npy> <groups .npy> <SETS label>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bglbio as glbio  # noqa: E402
keep_f, grp_f, label = sys.argv[1:4]
d = np.load('work/mesh_in.npz'); cen = d['verts'][d['faces']].mean(1)
doc, binary = glbio.read('before/mm9_giant.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Giant' and 'mesh' in n)
prims = glbio.prims(doc, binary, node['mesh'])
allp = np.concatenate([pr['POSITION'].astype(np.float64) for pr in prims]); allb = np.c_[allp[:, 0], -allp[:, 2], allp[:, 1]]
offset = d['verts'].min(0) - allb.min(0)
gc = np.concatenate([(lambda P, T: np.c_[P[:, 0], -P[:, 2], P[:, 1]][T].mean(1))(pr['POSITION'].astype(np.float64), pr['T']) for pr in prims]) + offset
dist, idx = cKDTree(cen).query(gc)
print('MATCH max dist', dist.max(), 'identity order', bool((idx == np.arange(len(idx))).all()), 'unique', len(np.unique(idx)) == len(idx))
keep, grp = np.load(keep_f)[idx], np.load(grp_f)[idx]
z = np.zeros(len(idx), bool)
np.savez(f'work/glb_sets_{label}.npz', keep=keep, group=grp, lining=z, lined=z)
print('SETS', label, 'keep', int(keep.sum()), 'groups', {int(g): int(((grp == g) & ~keep).sum()) for g in np.unique(grp)})
