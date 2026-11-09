#!/usr/bin/env python3
"""Boot faces that another piece's surface passes through at bind (detached_parts_audit's contact for a part hanging inside the
robe tube: an edge of the other piece crossing a boot face, or a boot edge crossing another piece's face), plus one welded ring.
Usage: boot_cross.py <sets tag> -> work/bootcross.npy per GLB face"""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
from weld import weld_ids  # noqa: E402
doc, b, nd, D = glbio.load(HERE / 'before' / 'mm9_honkm.glb', 'HonkM')
s = np.load(HERE / 'work' / f'glb_sets_{sys.argv[1]}.npz'); C = json.load(open(HERE / 'work' / 'classes.json'))['names']
P, T = D['HonkM_A']['P'], D['HonkM_A']['T']; n = len(T); cls = s['cls'][:n]
boot = cls == C.index('boots')


def seg_tri(A, B, V):   # segments (m,3),(m,3) against triangles (k,3,3) -> (m,k) bool
    e1 = V[:, 1] - V[:, 0]; e2 = V[:, 2] - V[:, 0]; d = B - A
    h = np.cross(d[:, None], e2[None]); a = (e1[None] * h).sum(-1)
    with np.errstate(divide='ignore', invalid='ignore'):
        f = 1 / a; sv = A[:, None] - V[None, :, 0]; u = f * (sv * h).sum(-1)
        q = np.cross(sv, e1[None]); v = f * (d[:, None] * q).sum(-1); t = f * (e2[None] * q).sum(-1)
    return (np.abs(a) > 1e-14) & (u >= 0) & (v >= 0) & (u + v <= 1) & (t >= 0) & (t <= 1)


Vb = P[T[boot]]; To = T[~boot]
E = np.unique(np.sort(np.vstack([To[:, [0, 1]], To[:, [1, 2]], To[:, [2, 0]]]), 1), axis=0)
hit_b = seg_tri(P[E[:, 0]], P[E[:, 1]], Vb).any(0)
Eb = np.unique(np.sort(np.vstack([T[boot][:, [0, 1]], T[boot][:, [1, 2]], T[boot][:, [2, 0]]]), 1), axis=0)
hit_e = seg_tri(P[Eb[:, 0]], P[Eb[:, 1]], P[To])
crossv = np.zeros(len(P), bool); crossv[Eb[hit_e.any(1)].ravel()] = True
x = np.zeros(n, bool); bi = np.flatnonzero(boot); x[bi[hit_b]] = True; x |= boot & crossv[T].any(1)
w = weld_ids(P); vh = np.zeros(w.max() + 1, bool); vh[w[T[x]].ravel()] = True; x |= boot & vh[w[T]].any(1)
out = np.zeros(len(s['cls']), bool); out[:n] = x; np.save(HERE / 'work' / 'bootcross.npy', out)
print('BOOTCROSS faces', int(x.sum()), 'crossed directly', int(hit_b.sum()), 'boot edges crossing', int(hit_e.any(1).sum()),
      'x side', np.sign(P[T[x]].mean(1)[:, 0]).astype(int).tolist()[:40])
