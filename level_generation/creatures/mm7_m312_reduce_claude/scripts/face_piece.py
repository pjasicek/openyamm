"""Per-face Smart Topology piece of the reduce source (work/face_piece.npy, dump_mesh.py face order): the production
master ../mm7_m312_claude/work/rig_v6.blend carries the 'piece' point attribute; each source face takes the majority
piece of the nearest master vertices to its three corners (rest pose; max distance printed). Usage: blender -b -P"""
import os, bpy, numpy as np
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); v, f = d['verts'], d['faces']
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm7_m312_claude', 'work', 'rig_v6.blend'))
b = bpy.data.objects['Body']; me = b.data
co = np.array([tuple(b.matrix_world @ x.co) for x in me.vertices]); pv = np.zeros(len(co), np.int32)
me.attributes['piece'].data.foreach_get('value', pv)
kd = KDTree(len(co))
for i, p in enumerate(co):
    kd.insert(p, i)
kd.balance()
near = [kd.find(tuple(p)) for p in v]
vp = np.array([pv[n[1]] for n in near]); dist = np.array([n[2] for n in near])
fp = np.array([np.bincount(vp[t]).argmax() for t in f])
np.save(os.path.join(HERE, 'work', 'face_piece.npy'), fp)
print('FACEPIECE faces', len(f), 'max dist mm', round(float(dist.max()) * 1000, 3), 'per piece', {int(k): int((fp == k).sum()) for k in np.unique(fp)})
