#!/usr/bin/env python3
"""Axe LOD0 (work/mm7_m286_axe_source_pre_reduce.glb, node Sword, glTF axe space: +Y along the haft, origin at the grip
centre) -> work/axe_dec/mesh_in.npz for decimate_tex.py: vertices welded by position + UV (the GLB splits them only by
normal: the axe is mostly flat-shaded), wedge UVs, no protection. Grip band: haft faces (radius <= 7 cm) with every
vertex within AXE_GRIP (default 0.11 m) of y = 0.01, the centre of the right finger joints in axe space (-0.05..0.07 at
bind; the solved fist is rigid on the hand) -> work/axe_dec/grip.npy (kept exactly)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import axe_glb
doc, b, base = axe_glb.read('work/mm7_m286_axe_source_pre_reduce.glb')
P, N, UV, F = axe_glb.prim(doc, b, base, 0)
key = np.round(np.hstack([P * 1e5, UV * 1e5])).astype(np.int64)
_, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
inv = inv.ravel(); V = P[first]; f = inv[F]
f = f[(f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])]
os.makedirs('work/axe_dec', exist_ok=True)
wuv = UV[F].reshape(-1, 2)
np.savez('work/axe_dec/mesh_in.npz', verts=V, faces=f.astype(np.int32), wuv=wuv, protect=np.zeros(len(f)))
G = float(os.environ.get('AXE_GRIP', '0.11'))
v = V[f]; rad = np.hypot(v[..., 0], v[..., 2])
grip = ((np.abs(v[..., 1] - 0.01) < G) & (rad <= 0.07)).all(1)
np.save('work/axe_dec/grip.npy', grip)
e = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), 1); _, c = np.unique(e, axis=0, return_counts=True)
print('AXEDUMP glb verts', len(P), 'welded', len(V), 'tris', len(f), 'open edges', int((c == 1).sum()), 'grip faces', int(grip.sum()),
      'grip y', np.round(V[np.unique(f[grip])][:, 1].min(), 3), np.round(V[np.unique(f[grip])][:, 1].max(), 3))
