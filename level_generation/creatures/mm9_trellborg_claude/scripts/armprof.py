"""Radius of the arm along the forearm axis near the wrist. Args: blend"""
import bpy, sys, numpy as np, json
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
b = bpy.data.objects['Body']; rig = b.parent; me = b.data
P = np.array([v.co[:] for v in me.vertices])
W = np.array(rig.matrix_world @ rig.data.bones['Bip01 R Hand'].head_local); E = np.array(rig.matrix_world @ rig.data.bones['Bip01 R Forearm'].head_local)
d = (W - E) / np.linalg.norm(W - E); al = (P - W) @ d; r = np.linalg.norm(P - W - np.outer(al, d), axis=1)
print('PROF W', W.round(3), 'd', d.round(3))
for a in np.arange(-0.2, 0.34, 0.02):
    m = (np.abs(al - a) < 0.01) & (r < 0.3) & (P[:, 0] < 0)
    if m.sum(): print('PROF', round(a, 2), int(m.sum()), np.round(np.percentile(r[m], [50, 95]), 3))
