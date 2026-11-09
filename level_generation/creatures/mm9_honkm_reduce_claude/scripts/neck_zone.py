#!/usr/bin/env python3
"""Robe faces round the neckline kept exactly (f65's Elder profile: a pale fleck at the blue collar's edge grew when the robe
faces under it were collapsed; the neckline carries the skin ellipse, the Elder's blue collar and paint residue that the
per-face samples miss): every robe/lined face whose rest centroid lies within RNECK m of the Bip01 Neck bind position.
Usage: neck_zone.py <sets tag> <out name>  (env RNECK 0.18)"""
import json, os, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
R = float(os.environ.get('RNECK', '0.18')); tag, outn = sys.argv[1:3]
doc, b, nd, D = glbio.load(HERE / 'before' / 'mm9_honkm.glb', 'HonkM')
s = np.load(HERE / 'work' / f'glb_sets_{tag}.npz'); C = json.load(open(HERE / 'work' / 'classes.json'))['names']
P, T = D['HonkM_A']['P'], D['HonkM_A']['T']; n = len(T)
skin = doc['skins'][nd['skin']]; names = [doc['nodes'][j]['name'] for j in skin['joints']]
ibm = glbio.arr(doc, b, skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
neck = np.linalg.inv(ibm[names.index('Bip01 Neck')])[:3, 3]
hit = np.isin(s['cls'][:n], [C.index('robe'), C.index('lined')]) & (np.linalg.norm(P[T].mean(1) - neck, axis=1) < R)
out = np.zeros(len(s['cls']), bool); out[:n] = hit; np.save(HERE / 'work' / f'{outn}.npy', out); print('NECKZONE', int(hit.sum()))
