#!/usr/bin/env python3
"""Faces with a vertex the half-rotation helpers (*_h, matching HELPERS) weight at least WMIN, as an extra keep set (the c r55
ladder stopped on the back of the left knee: 34.6 mm in Death2 at a Calf/Calf_h vertex; brief: keep every vertex the helper bones
weight heavily). Usage: helper_keep.py <out name>  (env HELPERS default 'Calf_h', WMIN default 0.3) -> work/<out>.npy"""
import os, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_zombie.glb', 'Zombie')
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
H = np.array([any(h in n for h in os.environ.get('HELPERS', 'Calf_h').split(',')) for n in names])
WMIN = float(os.environ.get('WMIN', '0.3')); out = []
for k in ('Zombie_A', 'ZombieHead_A', 'ZombieTorso'):
    w = (D[k]['W'] * H[D[k]['J']]).sum(1); f = (w[D[k]['T']] >= WMIN).any(1); out.append(f); print(k, int(f.sum()))
np.save(HERE / 'work' / f'{sys.argv[1]}.npy', np.concatenate(out))
