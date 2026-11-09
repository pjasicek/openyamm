"""Surface probe: for rays along y from the front (-y) and back at given (x, z), the first/last surface y of comp 0. Args: <npz> x,z ..."""
import sys, numpy as np
D = np.load(sys.argv[1]); co, comp = D['co'], D['comp']
for a in sys.argv[2:]:
    x, z = map(float, a.split(','))
    q = co[(np.abs(co[:, 0] - x) < 0.008) & (np.abs(co[:, 2] - z) < 0.008)]
    for c in sorted(set(comp[(np.abs(co[:, 0] - x) < 0.008) & (np.abs(co[:, 2] - z) < 0.008)].tolist())):
        qq = co[(np.abs(co[:, 0] - x) < 0.008) & (np.abs(co[:, 2] - z) < 0.008) & (comp == c)]
        print(a, 'comp', c, 'y', np.round(np.sort(qq[:, 1]), 3).tolist()[:14])
