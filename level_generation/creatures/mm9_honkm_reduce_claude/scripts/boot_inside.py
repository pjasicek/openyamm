#!/usr/bin/env python3
"""Boot vertices that sit 'inside' another body-set piece at bind by detached_parts_audit's sign rule (nearest surface point,
signed by that face's normal): the audit's root contact for boots hanging in the robe tube (a cut that removed them moved
the right boot's bind gap 0 -> 3.1 cm). Writes work/bootin.npy: boot faces using such a vertex, plus one welded ring.
Usage: boot_inside.py <sets tag>"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
from weld import weld_ids  # noqa: E402
doc, b, nd, D = glbio.load(HERE / 'before' / 'mm9_honkm.glb', 'HonkM')
s = np.load(HERE / 'work' / f'glb_sets_{sys.argv[1]}.npz'); C = json.load(open(HERE / 'work' / 'classes.json'))['names']
P, T = D['HonkM_A']['P'], D['HonkM_A']['T']; n = len(T); cls = s['cls'][:n]
boot = cls == C.index('boots'); To = T[~boot]
k = 10; i, j = np.meshgrid(np.arange(k + 1), np.arange(k + 1)); m = i + j <= k
bw = np.stack([i[m], j[m], k - i[m] - j[m]], 1) / k
S = np.einsum('sk,fkc->fsc', bw, P[To]); fn = np.cross(P[To[:, 1]] - P[To[:, 0]], P[To[:, 2]] - P[To[:, 0]])
fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-20); SN = np.repeat(fn, S.shape[1], 0); S = S.reshape(-1, 3)
bv = np.unique(T[boot]); d, q = cKDTree(S).query(P[bv]); sd = ((P[bv] - S[q]) * SN[q]).sum(1)
inside = bv[sd < 0.004]
print('boot vertices inside/within 4 mm', len(inside), 'of', len(bv), 'x sides', np.unique(np.sign(P[inside, 0]), return_counts=True))
iv = np.zeros(len(P), bool); iv[inside] = True
x = boot & iv[T].any(1)
w = weld_ids(P); vh = np.zeros(w.max() + 1, bool); vh[w[T[x]].ravel()] = True; x |= boot & vh[w[T]].any(1)
out = np.zeros(len(s['cls']), bool); out[:n] = x; np.save(HERE / 'work' / 'bootin.npy', out); print('BOOTIN faces', int(x.sum()))
