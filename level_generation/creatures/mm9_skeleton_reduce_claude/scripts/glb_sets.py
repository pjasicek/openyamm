#!/usr/bin/env python3
"""Fix pass: per-face sets of the installed LOD0 (before/mm9_skeleton.glb, primitives Skel_A, SkelHead_A, Dagger in order,
the Skel linings included) from the mesh_in plan (work/groups.npy over the lining-free import, same face order): group per GLB
face (0 = kept exactly; linings and every sheet but the back panel kept), checked by centroid against mesh_in. Also the connected piece of every
GLB face (work/comps.npz) for the joint-gap test. Writes work/fix/glb_sets.npz (group, comp, prim, lining)."""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
m = Model(Glb(str(HERE / 'before' / 'mm9_skeleton.glb')))
d = np.load(HERE / 'work' / 'mesh_in.npz'); G = np.load(HERE / 'work' / 'groups.npy'); lin = np.load(HERE / 'work' / 'lining.npy')
sheet = np.load(HERE / 'work' / 'sheet_faces.npy')
# the back panel (the one sheet of 192 outer faces) stays a group: mp_plan.py re-emits its lining from the lining twins
import json  # noqa: E402
BACK = next(int(k) for k, v in json.load(open(HERE / 'work' / 'group_plan.json')).items() if v[1] == 'sheet' and v[2] == 192)
print('back panel group', BACK)
cen, grp, prim, lining = [], [], [], []
k = 0
for pi, p in enumerate(m.primitives):
    T = p['triangles']; c = p['positions'][T].mean(1)
    l = lin if pi == 0 else np.zeros(len(T), bool)
    n = int((~l).sum())
    g = np.zeros(len(T), int); g[~l] = np.where(sheet[k:k + n] & (G[k:k + n] != BACK), 0, G[k:k + n])
    mc = d['verts'][d['faces'][k:k + n]].mean(1)
    gb = np.c_[c[~l][:, 0], -c[~l][:, 2], c[~l][:, 1] - 1.10451340675354]
    err = np.abs(gb - mc).max()
    print('prim', pi, 'faces', len(T), 'lining', int(l.sum()), 'centroid match max', err)
    assert err < 1e-4
    k += n; grp.append(g); prim.append(np.full(len(T), pi)); lining.append(l)
assert k == len(G)
c = np.load(HERE / 'work' / 'comps.npz')
np.savez(HERE / 'work' / 'fix' / 'glb_sets.npz', group=np.concatenate(grp), comp=c['comp'], prim=np.concatenate(prim),
         lining=np.concatenate(lining))
g = np.concatenate(grp); print('groups', len(np.unique(g[g > 0])), 'kept faces', int((g == 0).sum()), 'of', len(g))
