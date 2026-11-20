"""Horizontal skin sections per height: connected components with length-weighted centroid, bbox and perimeter.
Args: <npz> <zmin> <zmax> <step> [xmin xmax]"""
import sys
import numpy as np
sys.path.insert(0, 'scripts')
from limb_trace import section, loops
a = sys.argv[1:]
z0, z1, dz = map(float, a[1:4])
xr = (float(a[4]), float(a[5])) if len(a) > 5 else (-9, 9)
for z in np.arange(z0, z1 + 1e-9, dz):
    segs = section(np.array([0, 0, z]), np.array([0, 0, 1.0]))
    out = []
    for lp in loops(segs):
        mid = lp.mean(1); L = np.linalg.norm(lp[:, 1] - lp[:, 0], axis=1)
        c = (mid * L[:, None]).sum(0) / L.sum()
        if L.sum() < 0.04 or not (xr[0] <= c[0] <= xr[1]):
            continue
        lo, hi = lp.reshape(-1, 3).min(0), lp.reshape(-1, 3).max(0)
        out.append(f'({c[0]:+.3f},{c[1]:+.3f}) x[{lo[0]:+.2f},{hi[0]:+.2f}] y[{lo[1]:+.2f},{hi[1]:+.2f}] P{L.sum():.2f}')
    print(f'z{z:.2f}: ' + ' | '.join(out))
