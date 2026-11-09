#!/usr/bin/env python3
"""Ladder ratio r that leaves the free part (label 0, the body) a given share of its unkept faces, for decimate_tex.py's
budget rule (free target = N*r - kept - sum(group faces * group ratio)). Usage: ratio_for.py <keep.npy> <groups.npy>
<group ratios 1:0.5,...> <body ratio,...>  -> prints the r values (3 decimals, rounded up)."""
import math, sys
import numpy as np
keep, g = np.load(sys.argv[1]), np.load(sys.argv[2]); N = len(g)
gr = {int(k): float(v) for k, v in (kv.split(':') for kv in sys.argv[3].split(','))}
gb = sum(int(((g == k) & ~keep).sum() * r) for k, r in gr.items())
free = int(((g == 0) & ~keep).sum())
print(','.join(f'{math.ceil((keep.sum() + gb + free * float(b)) / N * 1000) / 1000:.3f}' for b in sys.argv[4].split(',')))
