"""Drop Meshy's two mouth-insert shells (raw comps 11/12 = seg 21/22: teeth/tongue pieces 3-8 mm behind the modelled lips) from the uv npz,
faces only (the brief: delete loose lip pieces; every other UV stays). Args: <seg npz> <uv npz in> <uv npz out>"""
import sys
import numpy as np
from scipy.spatial import cKDTree
R = np.load(sys.argv[1]); rc, rcomp = R['co'], R['comp']
lips = rc[np.isin(rcomp, [int(x) for x in __import__('os').environ.get('DROP', '21,22').split(',')])] + [0.008, 0, -0.9297]; lips = np.vstack([lips, lips * [-1, 1, 1]])
D = dict(np.load(sys.argv[2])); co, tri, comp = D['co'], D['tri'], D['comp']; names = [str(x) for x in D['names']]
d, _ = cKDTree(lips).query(co); lv = (comp == names.index('head')) & (d < 1e-4); bad = lv[tri].all(1)
for k in ('tri', 'mat', 'inner'): D[k] = D[k][~bad]
np.savez(sys.argv[3], **D); print('PIECES dropped', int(bad.sum()), 'faces')
