"""Per-face labels for the beholder ladder (work/mesh_in.npz), from connected pieces and dominant bones.
- keep (work/keep_eyes.npy): the painted eyes, kept exactly (an eye texture tears under collapse, mm6_bh_reduce_claude):
  head faces within 7.5 cm of the painted iris (../mm7_m166_claude/work/iris.json), the split StalkEye piece and the
  eyeball end of the other stalks (faces within 6.5 cm of the stalk tip; the eyeballs are about 6 cm across);
- groups (work/groups.npy): 0 head flesh and drool, 1 tentacles, 2 stalk shafts, 3 teeth (19 small pieces), 4 tongue."""
import json
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']; bones = d['bones']; vb = d['vbone']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl); cen = v[f].mean(1)
fb = np.array([bones[vb[t]][np.argmax([np.sum(vb[t] == x) for x in vb[t]])] for t in f])
head = sizes[fl] == sizes.max()
iris = np.array(json.load(open('../mm7_m166_claude/work/iris.json'))['iris_centre'])
keep = head & (np.linalg.norm(cen - iris, axis=1) < 0.075)
groups = np.zeros(len(f), int)
for p in np.unique(fl):
    m = fl == p; names = set(fb[m])
    if any(b.startswith('Tentacle') for b in names):
        groups[m] = 1
    elif names == {'StalkEye'}:
        keep |= m
    elif any(b.startswith('Stalk') for b in names):
        pv = v[np.unique(f[m])]; root = pv[np.argmin(np.linalg.norm(pv - v[f[head]].reshape(-1, 3).mean(0), axis=1))]
        tip = pv[np.argmax(np.linalg.norm(pv - root, axis=1))]
        ball = m & (np.linalg.norm(cen - tip, axis=1) < 0.065)
        keep |= ball; groups[m & ~ball] = 2
    elif names == {'Tongue'}:
        groups[m] = 4
    elif not head[m][0]:
        groups[m] = 3
np.save('work/keep_eyes.npy', keep); np.save('work/groups.npy', groups)
print('FACES', len(f), 'keep', int(keep.sum()), 'head eye', int((keep & head).sum()),
      {g: int(((groups == g) & ~keep).sum()) for g in range(5)})
