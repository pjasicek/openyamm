"""Per-face labels of the Mercenary rest mesh (work/mesh_in.npz, work/groups.npz, work/basecolor.png): head atlas side
(u > 1056/2080), finger / hand weights, connected piece and size, sampled base colour (mean of 9 interior samples) and
HSV -> work/face_info.npz; prints a summary."""
import colorsys
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); g = np.load('work/groups.npz'); W = g['W']; names = [str(n) for n in g['names']]
f, v = d['faces'], d['verts']; uv = d['wuv'].reshape(-1, 3, 2)
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255; H, Wd = img.shape[:2]
B = np.random.default_rng(1).dirichlet((2, 2, 2), 9)
u = np.einsum('sk,fkc->fsc', B, uv)
x = np.clip((u[..., 0] % 1) * Wd, 0, Wd - 1).astype(int); y = np.clip((1 - u[..., 1] % 1) * H, 0, H - 1).astype(int)
col = img[y, x].mean(1)
hsv = np.array([colorsys.rgb_to_hsv(*c) for c in col])
head_atlas = uv[:, :, 0].mean(1) > 1056 / 2080
idx = lambda pred: [i for i, n in enumerate(names) if pred(n)]
finger = W[:, idx(lambda n: 'Finger' in n)].sum(1)
hand = W[:, idx(lambda n: n.endswith('_Hand') or 'Finger' in n)].sum(1)
rhand = W[:, idx(lambda n: n.startswith('B_R_') and (n.endswith('_Hand') or 'Finger' in n))].sum(1)
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
piece = lab[f[:, 0]]; psize = np.bincount(piece)[piece]
fm = lambda a: a[f].mean(1)
np.savez('work/face_info.npz', head_atlas=head_atlas, finger=fm(finger), hand=fm(hand), rhand=fm(rhand),
         piece=piece, psize=psize, col=col, hsv=hsv, centroid=v[f].mean(1))
print('faces', len(f), 'head atlas', head_atlas.sum(), 'finger>.5', (fm(finger) > .5).sum(), 'hand>.5', (fm(hand) > .5).sum(),
      'small<=80', (psize <= 80).sum())
