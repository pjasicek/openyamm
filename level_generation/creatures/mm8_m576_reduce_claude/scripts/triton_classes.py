"""Per-face labels of the Triton rest mesh (work/mesh_in.npz, work/groups.npz): connected piece, dominant region
(left gripping hand + fingers, right hand + fingers, head, feet, pauldrons, rest), head texture set (u > 0.5 of the
padded 4096x2048 atlas: 2K body | 1K gutter | 1K head) and the sole band -> work/classes.npz; prints counts."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); g = np.load('work/groups.npz'); W = g['W']; names = [str(n) for n in g['names']]
f, v = d['faces'], d['verts']; uv = d['wuv'].reshape(-1, 3, 2)
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
piece = lab[f[:, 0]]; psize = np.bincount(piece)[piece]
sel = lambda pred: W[:, [i for i, nm in enumerate(names) if pred(nm)]].sum(1)
fm = lambda a: a[f].mean(1)
lhand = fm(sel(lambda s: s == 'B_L_Hand' or s.startswith('B_L_Finger')))
rhand = fm(sel(lambda s: s == 'B_R_Hand' or s.startswith('B_R_Finger')))
head = fm(sel(lambda s: s == 'B_Head')); foot = fm(sel(lambda s: 'Foot' in s or 'Toe' in s))
paul = fm(sel(lambda s: s.startswith('Pauldron'))); trident = fm(sel(lambda s: s == 'Trident'))
region = np.full(len(f), 'rest', object)
region[foot > .5] = 'foot'; region[paul > .5] = 'pauldron'; region[head > .5] = 'head'
region[rhand > .5] = 'rhand'; region[lhand > .5] = 'lhand'
headtex = uv[:, :, 0].mean(1) > .5
c = v[f].mean(1); zmin = v[:, 2].min(); sole = (region == 'foot') & (v[f][:, :, 2].max(1) < zmin + .06)
np.savez('work/classes.npz', piece=piece, psize=psize, region=region.astype(str), headtex=headtex, sole=sole, centroid=c,
         trident=trident)
for r in np.unique(region):
    m = region == r; print(f'{r:9s} {m.sum():5d} headtex {int((m & headtex).sum()):5d}')
print('headtex total', int(headtex.sum()), 'sole', int(sole.sum()), 'trident-weighted', int((trident > .5).sum()))
for p in np.unique(piece):
    m = piece == p
    print('piece', p, m.sum(), 'regions', dict(zip(*np.unique(region[m], return_counts=True))), 'headtex', int(headtex[m].sum()),
          'centre', np.round(c[m].mean(0), 3), 'size', np.round(np.ptp(v[f[m]].reshape(-1, 3), 0), 3))
