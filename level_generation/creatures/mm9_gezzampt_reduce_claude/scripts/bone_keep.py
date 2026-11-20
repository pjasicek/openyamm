#!/usr/bin/env python3
"""Extra keep set: GLB faces (both LOD0 primitives, in order) with a vertex that a bone matching REGEX weights at least WMIN.
Usage: bone_keep.py <name> <regex> [wmin]  -> work/keep_extra_<name>.npy"""
import re, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
name, rx = sys.argv[1], re.compile(sys.argv[2]); wmin = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
doc, b = gb.read(HERE / 'before' / 'mm9_gezzampt.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Gezzampt' and 'mesh' in n)
joints = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
sel = [i for i, n in enumerate(joints) if rx.search(n)]; print('bones', [joints[i] for i in sel])
out = []
for p in gb.prims(doc, b, node['mesh']):
    J, W, T = p['JOINTS_0'], p['WEIGHTS_0'].astype(float), p['T']
    w = sum((W * (J == i)).sum(1) for i in sel); out.append((w[T] >= wmin).any(1))
k = np.concatenate(out); np.save(HERE / 'work' / f'keep_extra_{name}.npy', k); print('faces', int(k.sum()))
