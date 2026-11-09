#!/usr/bin/env python3
"""Error lock for the next ladder: removed source vertices of earlier steps (work/err_<step>.npz from err_regions.py) whose
largest distance to the candidate surface over every clip exceeded T mm keep every body face touching them (all GLB copies
at the same position). Usage: err_keep.py <name> <T mm> <err npz> [...]  -> work/keep_<name>.npy (body face mask)"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb
name, T = sys.argv[1], float(sys.argv[2]) / 1000
doc, b = gb.read(HERE / 'before' / 'mm9_dragonking.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'DragonKing' and 'mesh' in n)
body = gb.prims(doc, b, node['mesh'])[0]; P = body['POSITION'].astype(float); F = body['T']
_, tp = np.unique(np.round(P, 6), axis=0, return_inverse=True); tp = tp.reshape(-1)
bad = np.zeros(tp.max() + 1, bool); n = 0
for f in sys.argv[3:]:
    e = np.load(HERE / 'work' / f); r = e['removed']; m = (e['maxd'] > T) & (r < len(P))
    bad[tp[r[m]]] = True; n += int(m.sum())
keep = bad[tp[F]].any(1)
print(f'{name}: {n} removed vertices over {T * 1000:.0f} mm -> {int(bad.sum())} positions, {int(keep.sum())} body faces kept')
np.save(HERE / 'work' / f'keep_{name}.npy', keep)
