#!/usr/bin/env python3
"""The headdress's goose head and neck kept exactly (fix pass k70, chart guard: at 0.5 the beak came out straighter, pointier
and darker in every close-up): every hat-class face of the head set with every vertex above GOOSE_Y (rest, glTF y-up, the gold neck
starts at about 1.84 m). Usage: goose_keep.py <sets tag> <out name>  (env GOOSE_Y 1.838: the gold goose piece only)"""
import json, os, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
Y = float(os.environ.get('GOOSE_Y', '1.838')); tag, outn = sys.argv[1:3]
doc, b, nd, D = glbio.load(HERE / 'before' / 'mm9_honkf.glb', 'HonkF')
s = np.load(HERE / 'work' / f'glb_sets_{tag}.npz'); C = json.load(open(HERE / 'work' / 'classes.json'))['names']
n0 = len(D['HonkF_A']['T']); P, T = D['HonkFHead']['P'], D['HonkFHead']['T']
hit = (s['cls'][n0:] == C.index('hat')) & (P[T][:, :, 1].min(1) > Y)
out = np.zeros(len(s['cls']), bool); out[n0:] = hit; np.save(HERE / 'work' / f'{outn}.npy', out); print('GOOSE', int(hit.sum()))
