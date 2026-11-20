#!/usr/bin/env python3
"""Connected pieces of decimated template npz files: faces, group, closed/open, signed volume (cm^3), size (cm).
A closed piece with negative volume is inside out (check_winding.py would flag it). Usage: piece_report.py <npz>..."""
import sys
import numpy as np
import scipy.sparse as sp
import scipy.sparse.csgraph as cg
bad = 0
for n in sys.argv[1:]:
    d = np.load(n); V, F, grp = d['verts'], d['faces'], d['group']
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    nc, lab = cg.connected_components(sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(V),) * 2), directed=False)
    out = []
    for k in range(nc):
        s = lab[F[:, 0]] == k; f = F[s]
        if not s.any():
            continue
        fe = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), 1); _, cc = np.unique(fe, axis=0, return_counts=True)
        closed = bool((cc == 2).all()); vol = (np.cross(V[f[:, 0]], V[f[:, 1]]) * V[f[:, 2]]).sum() / 6
        bad += closed and vol < 0
        out.append(f"{int(s.sum())}t g{int(np.unique(grp[s])[0])} {'closed' if closed else 'open'} {vol * 1e6:+.1f}cm3 {np.ptp(V[np.unique(f)], 0).max() * 100:.1f}cm")
    print(n, len(F), '|', ', '.join(out))
print('INSIDE-OUT CLOSED PIECES', bad)
