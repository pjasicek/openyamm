#!/usr/bin/env python3
"""For an axis-aligned cut through a box of air, the number of connected air components in each candidate slice:
tools/slice_scan.py <axis x|z> <from> <to> <xmin> <xmax|zmin..> ... -> slices with one component are clean cuts.
Usage: slice_scan.py z -2560 -2100 -4620 -3740 -340 -170   (axis, range, other-axis range, y range; LT)"""
import pickle, sys
from pathlib import Path
import numpy as np
from scipy import ndimage
PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
grid, air, door = pickle.loads((PROJECT / "work/cutlab.pkl").read_bytes())
axis, a0, a1, o0, o1, y0, y1 = sys.argv[1], *map(float, sys.argv[2:])
ax = {"x": 0, "z": 2}[axis]
other = 2 - ax
def idx(v, k):
    p = np.zeros(3); p[k] = v
    return int(grid.index(p[None])[0][k])
lo, hi = sorted((idx(a0, ax), idx(a1, ax)))
olo, ohi = sorted((idx(o0, other), idx(o1, other)))
ylo, yhi = sorted((idx(y0, 1), idx(y1, 1)))
for c in range(lo, hi + 1):
    sl = np.take(air, c, axis=ax)            # 2D: (other0, other1)
    sub = sl[olo:ohi + 1, ylo:yhi + 1] if ax == 2 else sl[ylo:yhi + 1, olo:ohi + 1]
    labels, n = ndimage.label(sub)
    plane = grid.origin[ax] + (c + 0.5) * grid.size
    print(round(plane), n, int(sub.sum()))
