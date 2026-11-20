"""Pass 7 (new head): the part of r72's head shell (F1's, component 'head') that stays: the lower neck and the skin down to the dress
neckline, below a slanted cut plane. It keeps r72's final positions (work/uv_tex2.npz, after geo_chain_fre.sh) and therefore its weld to
the dress (shared positions) and its weights (work/weights.npz: Neck / XhalfHead / Head). Vertices are welded by position (the UV seams
go; the new head set gets new UVs). Faces are kept when all three corners lie below the plane z = Z0 + SLOPE * (y - Y0) (asm frame: z up,
front -y).
Args: <out npz>   env: NH_Z0 (0.556), NH_Y0 (-0.05), NH_SLOPE (0.16)"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]
Z0 = float(os.environ.get('NH_Z0', '0.556')); Y0 = float(os.environ.get('NH_Y0', '-0.05')); SL = float(os.environ.get('NH_SLOPE', '0.16'))
D = np.load(f'{HERE}/work/uv_tex2.npz'); W = np.load(f'{HERE}/work/weights.npz')
co, tri, comp, orig = D['co'], D['tri'], D['comp'], D['orig']; names = [str(x) for x in D['names']]
h = names.index('head')
key = np.round(co, 6); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
P = np.zeros((inv.max() + 1, 3)); P[inv] = co
src = np.zeros(inv.max() + 1, int); src[inv] = np.arange(len(co))          # one uv_tex2 vertex per welded position
below = P[:, 2] < Z0 + SL * (P[:, 1] - Y0)
ft = tri[(comp[tri] == h).all(1)]; ft = inv[ft]
ft = ft[below[ft].all(1)]
# keep the largest connected piece (drops stray eye/ear bits that happen to lie below the plane)
used = np.unique(ft); par = {int(v): int(v) for v in used}
def f(a):
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
for t in ft:
    r = f(int(t[0])); par[f(int(t[1]))] = r; par[f(int(t[2]))] = r
roots = np.array([f(int(t[0])) for t in ft]); big = np.bincount(roots).argmax(); ft = ft[roots == big]
used, newi = np.unique(ft, return_inverse=True); ftn = newi.reshape(-1, 3)
pos = P[used]; s = src[used]
wj, ww = W['wj'][orig[s]], W['ww'][orig[s]]
# boundary loops: the bottom one is welded to the dress (shared positions), the top one is the cut
e = np.sort(np.vstack([ftn[:, [0, 1]], ftn[:, [1, 2]], ftn[:, [2, 0]]]), 1); u, c = np.unique(e, axis=0, return_counts=True); be = u[c == 1]
from scipy.spatial import cKDTree
dd, _ = cKDTree(np.delete(co, np.where(comp == h)[0], 0)).query(pos)
welded = dd < 2e-5
bv = np.unique(be)
top = np.setdiff1d(bv, np.where(welded)[0])
print('OLDNECK verts', len(pos), 'faces', len(ftn), 'boundary', len(bv), 'welded to body', int(welded.sum()), 'cut ring', len(top),
      'z', pos[:, 2].min().round(4), pos[:, 2].max().round(4))
np.savez(out, co=pos, tri=ftn, wj=wj, ww=ww, wnames=W['wnames'], welded=welded, cut=top, cutedges=be[np.isin(be, top).all(1)],
         z0=Z0, y0=Y0, slope=SL)
