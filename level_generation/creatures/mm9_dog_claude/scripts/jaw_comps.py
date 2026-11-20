"""Connected parts of the snout in front of a y station: two parts mean the lips are separate there.
Args: <dump npz> [zmin]"""
import sys
import numpy as np
d = np.load(sys.argv[1])
co, tris, piece = d['co'], d['tris'], d['piece']
zmin = float(sys.argv[2]) if len(sys.argv) > 2 else 0.62
body = piece == 0
t = tris[body[tris].all(1)]
E = np.unique(np.sort(np.r_[t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]], 1), axis=0)
for y in [-0.46, -0.44, -0.43, -0.42, -0.41, -0.40, -0.39, -0.38, -0.37, -0.36]:
    mask = body & (co[:, 1] < y) & (co[:, 2] > zmin)
    par = np.arange(len(co))
    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for a, b in E[mask[E[:, 0]] & mask[E[:, 1]]]:
        ra, rb = find(a), find(b)
        if ra != rb:
            par[ra] = rb
    r = np.array([find(i) for i in np.nonzero(mask)[0]])
    print(y, sorted(np.unique(r, return_counts=True)[1].tolist(), reverse=True)[:4])
print('tris', len(tris), 'body', len(t))
