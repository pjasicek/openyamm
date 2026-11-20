#!/usr/bin/env python3
"""Compare two wing_gap.py reports on the anchors both share (same rest position): the attached ones (installed largest
signed distance outside the posed body skin under LIM m over the nine role clips), worst and count over 1 cm.
Usage: wing_gap_compare.py <installed.json> <candidate.json> [LIM]"""
import json, sys
import numpy as np
from scipy.spatial import cKDTree
a, b = (json.load(open(p)) for p in sys.argv[1:3]); LIM = float(sys.argv[3]) if len(sys.argv) > 3 else 0.1
A = np.array(a['per_anchor']); B = np.array(b['per_anchor'])
d, j = cKDTree(B[:, :3]).query(A[:, :3]); m = d < 1e-5
ia, ib = A[m, 3], B[j[m], 3]; att = ia < LIM
print(f'anchors installed {len(A)}, candidate {len(B)}, shared {int(m.sum())}, attached (installed max < {LIM} m) {int(att.sum())}')
print(f'attached: installed max {ia[att].max() * 100:.2f} cm, candidate {ib[att].max() * 100:.2f} cm; over 1 cm {int((ia[att] > .01).sum())} -> '
      f'{int((ib[att] > .01).sum())}; largest change {np.abs(ib[att] - ia[att]).max() * 100:.2f} cm')
