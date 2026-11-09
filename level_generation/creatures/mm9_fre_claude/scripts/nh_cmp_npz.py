"""Pass 7: comparison npz for clay renders: a new-head npz (co, tri, comp) beside r72's head pieces and body top (uv_tex2.npz),
optionally offset in x. Args: <new npz> <out npz> [dx for the old head (0 = overlap)] [old parts: head,hair2,dress,scarf]"""
import sys
import numpy as np
new, out = sys.argv[1:3]; dx = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
parts = (sys.argv[4] if len(sys.argv) > 4 else 'head,hair2,dress').split(',')
N = np.load(new); D = np.load('work/uv_tex2.npz'); names = [str(x) for x in D['names']]
co, tri, comp = [N['co']], [N['tri']], [N['comp']]; off = len(N['co']); base = int(N['comp'].max()) + 1
for k, p in enumerate(parts):
    ft = D['tri'][(D['comp'][D['tri']] == names.index(p)).all(1)]
    if p == 'dress': ft = ft[(D['co'][ft][:, :, 2].min(1) > 0.40)]
    u, i = np.unique(ft, return_inverse=True)
    c = D['co'][u].copy(); c[:, 0] += dx
    co.append(c); tri.append(i.reshape(-1, 3) + off); comp.append(np.full(len(u), base + k)); off += len(u)
np.savez(out, co=np.vstack(co), tri=np.vstack(tri), comp=np.concatenate(comp))
