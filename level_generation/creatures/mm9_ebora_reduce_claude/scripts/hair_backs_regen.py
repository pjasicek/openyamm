"""Rebuild the hair shell's back copies on a reduced mesh (Ebora's hair_backs.py made them on the full shell: a reversed copy
0.5 mm inward wherever the inside of the shell is ever in view). Every reduced shell face (decimate group 1) whose nearest
original shell face (by centroid) had a copy gets one: same UVs, reversed winding, vertices moved 0.5 mm against the
shell's vertex normal; copy_of records the front vertex so interp_weights.py gives the copy its exact weights.
Usage: hair_backs_regen.py <tag,...>  (rewrites work/mesh_<tag>.npz in place)"""
import sys
import numpy as np
from scipy.spatial import cKDTree
B = np.load('work/backs_src.npz'); tree = cKDTree(B['cen'])
for tag in sys.argv[1].split(','):
    d = dict(np.load(f'work/mesh_{tag}.npz')); v, f, w, g = d['verts'], d['faces'], d['wuv'].reshape(-1, 3, 2), d['group']
    sel = np.flatnonzero(g == 1)
    _, nn = tree.query(v[f[sel]].mean(1), 1); need = sel[B['had'][nn]]
    fn = np.cross(v[f[sel, 1]] - v[f[sel, 0]], v[f[sel, 2]] - v[f[sel, 0]])
    vn = np.zeros_like(v)
    for k in range(3):
        np.add.at(vn, f[sel, k], fn)
    vn /= np.linalg.norm(vn, axis=1, keepdims=True) + 1e-12
    used = np.unique(f[need]); remap = -np.ones(len(v), int); remap[used] = len(v) + np.arange(len(used))
    newv = v[used] - 0.0005 * vn[used]
    newf = remap[f[need]][:, ::-1]; neww = w[need][:, ::-1]
    copy_of = np.r_[-np.ones(len(v), int), used] if 'copy_of' not in d else None
    d.update(verts=np.vstack([v, newv]), faces=np.vstack([f, newf]), wuv=np.vstack([w, neww]).reshape(-1, 2),
             group=np.r_[g, np.full(len(newf), 4)], src_index=np.r_[d['src_index'], -np.ones(len(used), int)], copy_of=copy_of)
    np.savez(f'work/mesh_{tag}.npz', **d)
    print('BACKS', tag, 'shell faces', len(sel), 'copied', len(need), 'faces total', len(d['faces']))
