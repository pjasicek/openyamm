"""Relaxed keep set for prio-1 monsters (brief section "Prio-1 monsters: relaxed keep set") on Ebora's rest mesh:
-> work/keep_r.npy (exact: head skin piece incl. face, eyes, mouth, horns, fringe and side locks with their copies, neck ring,
soles, small pieces, wing spars and the pleat-heavy membrane faces), work/drop_r.npy (the hair shell's 541 reversed back
copies: rebuilt from the reduced shell), work/groups_r.npy (1 hair shell, 2 hands/fingers, 3 light membrane faces),
work/backs_src.npz (shell faces that had a back copy). Env: PLEAT_HEAVY (default 0.5), MEMBRANE=1 to cut membranes."""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); v, f, mat, W, wuv, hw = d['verts'], d['faces'], d['mat'], d['W'], d['wuv'].reshape(-1, 3, 2), d['handw']
names = d['names'].tolist(); n = len(v)
e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sz = np.bincount(fl); c = v[f].mean(1)
fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
head = mat == 1
# back copies: UV-identical pairs in the head set; the copy sits 0.5 mm behind its original along the original's normal
key = {}
for i in np.flatnonzero(head):
    key.setdefault(tuple(sorted(map(tuple, np.round(wuv[i], 6)))), []).append(i)
copy = np.zeros(len(f), bool); orig_of = {}
for fs in key.values():
    if len(fs) == 2:
        a, b = fs
        if np.dot(c[b] - c[a], fn[a]) < 0: copy[b] = True; orig_of[b] = a
        else: copy[a] = True; orig_of[a] = b
hp = [p for p in np.unique(fl[head]) if (head & (fl == p)).sum() == sz[p]]  # pieces made only of head faces
shell_piece = max(hp, key=lambda p: sz[p])
shell = head & (fl == shell_piece) & ~copy
shell_copy = copy & np.isin(np.array([orig_of.get(i, -1) for i in range(len(f))]), np.flatnonzero(shell))
print('shell piece', shell_piece, 'faces', int(shell.sum()), 'shell back copies', int(shell_copy.sum()), 'all copies', int(copy.sum()))
had = np.zeros(len(f), bool); had[[orig_of[i] for i in np.flatnonzero(shell_copy)]] = True
np.savez('work/backs_src.npz', cen=c[shell], had=had[shell])
keep = np.zeros(len(f), bool)
keep |= head & ~shell & ~shell_copy                     # face skin piece, eyes, mouth, horns, fringe + locks and their copies
hv = np.unique(f[head]); near = cKDTree(v[hv]).query(v)[0] < 0.02
keep |= (~head) & (mat != 3) & near[f].any(1)           # neck ring
leg = mat == 2; zmin = v[f[leg]][..., 2].min(); keep |= leg & (c[:, 2] < zmin + 0.06)
small = sz[fl] <= 80; keep |= small & ~shell_copy
hands = (mat == 0) & (hw[f] > 0.2).any(1) & ~small
mem = (mat == 3) & (sz[fl] == 732)
pl = [i for i, x in enumerate(names) if 'Pleat' in x]; pw = W[:, pl].sum(1)
heavy = (pw[f] > float(os.environ.get('PLEAT_HEAVY', '0.5'))).any(1)
cutmem = mem & ~heavy if os.environ.get('MEMBRANE', '0') == '1' else np.zeros(len(f), bool)
keep |= (mat == 3) & ~cutmem
groups = np.zeros(len(f), int); groups[shell] = 1; groups[hands & ~keep] = 2; groups[cutmem] = 3
keep &= ~shell
np.save('work/keep_r.npy', keep); np.save('work/drop_r.npy', shell_copy); np.save('work/groups_r.npy', groups)
free = ~keep & ~shell_copy & (groups == 0)
print('KEEP', int(keep.sum()), 'DROP', int(shell_copy.sum()), 'hair', int((groups == 1).sum()), 'hands', int((groups == 2).sum()),
      'membrane', int((groups == 3).sum()), 'free', int(free.sum()), 'by material', np.bincount(mat[free], minlength=4))
