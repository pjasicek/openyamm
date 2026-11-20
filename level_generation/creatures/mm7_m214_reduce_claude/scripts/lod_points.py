#!/usr/bin/env python3
"""Protected points for the LOD build (rest-pose Blender coordinates of unchanged LOD0 vertices, work/mesh_in.npz):
- work/top_points.json: the highest head vertex of the picked candidate (argument: its work/mesh_*.npz) and of each quiver arrow piece, so the coarse LODs keep the
  model's height (picking bounds use the coarsest LOD);
  plus eight face landmarks (nose tip, chin, mouth corners, outer eye corners, ear tips);
- work/string_points.json: the bowstring's nock ring (StringNock weight > 0.9) and the tip vertex at each bow end.
  The source LOD1-3 kept only 18 string vertices without any StringNock weight, so the distant string stayed straight
  while the right hand drew it."""
import json
import numpy as np
d = np.load('work/mesh_in.npz'); v, f = d['verts'], d['faces']; p = np.load('work/pieces.npy')
g = np.load('work/groups.npz'); W = g['W']; names = [str(x) for x in g['names']]
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(v), len(v))), directed=False)
import sys
cand = np.load(sys.argv[1])['verts']  # the picked LOD0 (hair is decimated: its crown vertex is the candidate's)
head = (np.abs(cand[:, 0]) < 0.15) & (np.abs(cand[:, 1]) < 0.15)
top = [cand[head][np.argmax(cand[head, 2])]]
for piece in (9,):
    for comp in np.unique(lab[f[p == piece][:, 0]]):
        vs = np.flatnonzero(lab == comp); top.append(v[vs[np.argmax(v[vs, 2])]])
sv = np.unique(f[p == 12]); nock = W[sv, names.index('StringNock')]
ring = sv[nock > 0.9]
ax = v[sv, 1]  # the string runs along y (bow ends at y -0.51 and +0.52)
ends = [sv[[np.argmin(ax)]], sv[[np.argmax(ax)]]]  # one tip vertex per end (an end ring cost 36 LOD3 triangles)
pts = np.concatenate([v[ring], *(v[x] for x in ends)])
# face landmarks (kept exactly at LOD0): nose tip, chin, mouth corners, outer eye corners, ear tips (the forehead lies
# under the decimated fringe);
# without them LOD2/LOD3 flattened the face into a box (worse than the source LODs)
hp = np.unique(f[p == 1]); hv = v[hp]; ax0 = hv[hv[:, 2] > 1.56, 0].mean()
front = hp[(hv[:, 1] < -0.05) & (hv[:, 2] > 1.5)]; fv = v[front]
nose = front[np.argmin(fv[:, 1])]; nz = v[nose, 2]
low = front[(fv[:, 2] > nz - 0.07) & (fv[:, 2] < nz - 0.03)]; chin = low[np.argmin(v[low, 1])] if len(low) else nose
lm = [nose, chin]
mouth = front[np.abs(fv[:, 2] - (nz - 0.03)) < 0.008]
for sgn in (1, -1):
    side = mouth[(v[mouth, 0] - ax0) * sgn > 0.012]
    if len(side): lm.append(side[np.argmin(np.abs(np.abs(v[side, 0] - ax0) - 0.022))])
    eye = np.unique(f[p == 3]); ev = v[eye][(v[eye, 0] - ax0) * sgn > 0]
    if len(ev):
        tip = ev[np.argmax((ev[:, 0] - ax0) * sgn)]; lm.append(hp[np.argmin(np.linalg.norm(hv - tip, axis=1))])
    ear = hp[((hv[:, 0] - ax0) * sgn > 0.072) & (hv[:, 2] > 1.56) & (hv[:, 2] < 1.72)]
    if len(ear): lm.append(ear[np.argmax(v[ear, 2])])
top += [v[i] for i in lm]
print('FACE LANDMARKS', len(lm), np.round(v[lm], 3).tolist())
json.dump(np.round(np.array(top), 6).tolist(), open('work/top_points.json', 'w'), indent=1)
json.dump(np.round(pts, 6).tolist(), open('work/string_points.json', 'w'), indent=1)
print('TOP POINTS', len(top), 'max z', round(float(np.array(top)[:, 2].max()), 4), '| STRING POINTS nock', len(ring),
      'ends', [len(x) for x in ends])
