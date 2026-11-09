#!/usr/bin/env python3
"""MM9's own skin projected onto our body UVs: every body texel's rest position (rasterised barycentrics of work/uv.npz) takes the colour of
the nearest point on MM9's bind mesh (dense barycentric samples of every MM9 triangle with its skin UV). Used for the tier-A bodice
embroidery (gold vines on black), which no ramp can draw: its gold texels become the fourth region channel. Faces outside --parts are left 0.
Args: <skin png> <out png> [size] [parts,comma]  (project folder)"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb
skin_p, out_p = sys.argv[1:3]; S = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
parts = sys.argv[4].split(',') if len(sys.argv) > 4 else ['dress']
D = np.load('work/uv.npz'); co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
sel = np.where((mat == 0) & np.isin(comp[tri[:, 0]], [names.index(p) for p in parts]))[0]
# MM9 surface samples
g = Glb('source/mm9/pf2a.glb'); doc = g.json; SP = []; SU = []
for node in doc['nodes']:
    if 'mesh' not in node: continue
    pr = doc['meshes'][node['mesh']]['primitives'][0]; A = pr['attributes']
    pos = g.accessor(A['POSITION']).astype(float); P = np.c_[pos[:, 0], -pos[:, 2], pos[:, 1]]
    t = g.accessor(pr['indices']).astype(int).reshape(-1, 3); U = g.accessor(A['TEXCOORD_0']).astype(float)
    n = 24; bb = [(i / n, j / n) for i in range(n + 1) for j in range(n + 1 - i)]
    for a, b in bb:
        c = 1 - a - b
        SP.append(P[t[:, 0]] * a + P[t[:, 1]] * b + P[t[:, 2]] * c); SU.append(U[t[:, 0]] * a + U[t[:, 1]] * b + U[t[:, 2]] * c)
SP = np.vstack(SP); SU = np.vstack(SU); kd = cKDTree(SP)
import os
UP = int(os.environ.get('UP', '4'))      # the 256 skin enlarged (Lanczos) and sampled bilinearly, not nearest texels
skin = Image.open(skin_p).convert('RGB'); skin = np.asarray(skin.resize((skin.width * UP, skin.height * UP), Image.LANCZOS), np.float32); H, W_ = skin.shape[:2]
def bil(px, py):
    x0 = np.clip(np.floor(px).astype(int), 0, W_ - 2); y0 = np.clip(np.floor(py).astype(int), 0, H - 2); fx = np.clip(px - x0, 0, 1)[:, None]; fy = np.clip(py - y0, 0, 1)[:, None]
    return (skin[y0, x0] * (1 - fx) * (1 - fy) + skin[y0, x0 + 1] * fx * (1 - fy) + skin[y0 + 1, x0] * (1 - fx) * fy + skin[y0 + 1, x0 + 1] * fx * fy)
out = np.zeros((S, S, 3), np.float32); cov = np.zeros((S, S), bool)
for f in sel:
    q = uv[tri[f]] * [S, -S] + [0, S]; x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1 + 1, S)), np.arange(max(y0, 0), min(y1 + 1, S)))
    pts = np.c_[xs.ravel() + 0.5, ys.ravel() + 0.5]
    T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
    if abs(np.linalg.det(T_)) < 1e-9: continue
    l = np.linalg.solve(T_, (pts - q[2]).T).T; l3 = np.c_[l, 1 - l.sum(1)]
    ok = (l3 > -0.02).all(1)
    if not ok.any(): continue
    p3 = l3[ok] @ co[tri[f]]
    _, nn = kd.query(p3); u_ = SU[nn]
    out[pts[ok, 1].astype(int), pts[ok, 0].astype(int)] = bil(u_[:, 0] * W_ - 0.5, u_[:, 1] * H - 0.5); cov[pts[ok, 1].astype(int), pts[ok, 0].astype(int)] = True
Image.fromarray(out.astype('u1')).save(out_p); np.save(str(Path(out_p).with_suffix('.cov.npy')), cov)
print('PROJECTED', out_p, int(cov.sum()), 'texels')
