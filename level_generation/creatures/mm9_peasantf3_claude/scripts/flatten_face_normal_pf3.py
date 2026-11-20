#!/usr/bin/env python3
"""Head normal map flattened over the face (pass 5): Meshy's normal map of the fresh head paint carries strong relief in the eye sockets,
under the lower lids and between the lips that is not in the mesh, which the viewer's light drew as dark wedges under the eyes and a dark
slit between the lips. Inside the face window (|x| < 7 cm, 1.495-1.69 m over the soles, front faces; 6 mm ramps) the map is blended toward
flat by STRENGTH (eyes, nose and mouth box fully). Args: <in normal png> <out normal png> [strength 0.85]   (project folder)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ni
D = np.load('work/uv.npz'); co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
nm = np.asarray(Image.open(sys.argv[1]).convert('RGB'), np.float32); S = nm.shape[0]; K = float(sys.argv[3]) if len(sys.argv) > 3 else 0.85
Z0 = -0.9297; kh = names.index('head')
W = np.zeros((S, S), np.float32)
def ramp(v, a, b): return np.clip((v - a) / (b - a), 0, 1)
for f in np.where((mat == 1) & (comp[tri[:, 0]] == kh))[0]:
    c = co[tri[f]].mean(0); zs = c[2] - Z0; x = abs(c[0])
    if c[1] > -0.03: continue
    w = ramp(zs, 1.495, 1.501) * (1 - ramp(zs, 1.684, 1.690)) * (1 - ramp(x, 0.064, 0.070))
    core = (1 - ramp(x, 0.045, 0.050)) * ramp(zs, 1.53, 1.535) * (1 - ramp(zs, 1.635, 1.64))      # eyes, nose, mouth
    w = max(w * K, core)
    if w <= 0: continue
    q = uv[tri[f]] * [S, -S] + [0, S]
    x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int), S - 1)
    W[y0:y1 + 1, x0:x1 + 1] = np.maximum(W[y0:y1 + 1, x0:x1 + 1], w)
W = ni.gaussian_filter(W, 1.0)[..., None]
out = nm * (1 - W) + np.array([128, 128, 255.0]) * W
Image.fromarray(np.clip(out + 0.5, 0, 255).astype('u1')).save(sys.argv[2]); print('FLAT face normal texels', int((W[..., 0] > 0.5).sum()))
