#!/usr/bin/env python3
"""Rest-pose source->candidate error per region group (work/errmap_<cand>.npz from err_where.py).
Usage: err_groups.py <set> <Cand_NN> ..."""
import sys
import numpy as np
d = np.load('work/mesh_in.npz'); f = d['faces']
g = np.load(f'work/groups_{sys.argv[1]}.npy'); k = np.load(f'work/keep_{sys.argv[1]}.npy')
vg = np.full(len(d['verts']), -1); vg[f[~k].ravel()] = np.repeat(g[~k], 3)
for c in sys.argv[2:]:
    s = np.load(f'work/errmap_{c}.npz')['src']
    print(c, ' '.join(f'g{x}: n{int((vg == x).sum())} p99 {np.percentile(s[vg == x], 99) * 1000:.0f} max {s[vg == x].max() * 1000:.0f} >28mm {int(((vg == x) & (s > .028)).sum())}'
                       for x in range(-1, 6) if (vg == x).any()))
