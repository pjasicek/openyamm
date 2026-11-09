"""Octahedra at rig joints and finger points -> npz for view_npz.py. Args: <rig json> <out npz> [r]"""
import sys, json, numpy as np
R = json.load(open(sys.argv[1])); r = float(sys.argv[3]) if len(sys.argv) > 3 else 0.012
pts = list(R['joints'].values())
for f, ps in R['fingers'].items():
    pts += ps + [[-p[0], p[1], p[2]] for p in ps]
pts += R.get('extra', [])
O = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]], float) * r
F = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
co = []; tri = []
for p in pts:
    b = len(co); co += list(np.array(p) + O); tri += [(b + a, b + c, b + d) for a, c, d in F]
np.savez(sys.argv[2], co=np.array(co), tri=np.array(tri), part=np.ones(len(co), int))
