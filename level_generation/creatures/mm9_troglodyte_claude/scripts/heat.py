"""Bone heat weights in Blender. Args: <mesh npz> <out npz>. Mesh in glTF frame; bones from rig_bones.table()."""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
A = sys.argv[sys.argv.index('--') + 1:]
D = np.load(A[0]); co, tri = D['co'], D['tri']
T = dict(np.load(A[0].replace('.npz', '_bones.npz'), allow_pickle=True)['table'].item())
bpy.ops.wm.read_factory_settings(use_empty=True)
b = lambda p: (float(p[0]), float(-p[2]), float(p[1]))
me = bpy.data.meshes.new('Body'); ob = bpy.data.objects.new('Body', me); bpy.context.collection.objects.link(ob)
me.from_pydata([b(p) for p in co], [], tri.tolist()); me.update()
ad = bpy.data.armatures.new('rig'); arm = bpy.data.objects.new('rig', ad); bpy.context.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm; arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for n, (p, h, t) in T.items():
    e = ad.edit_bones.new(n); e.head = b(h); e.tail = b(t)
for n, (p, h, t) in T.items():
    if p: ad.edit_bones[n].parent = ad.edit_bones[p]
bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.context.selected_objects: o.select_set(False)
ob.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
names = [g.name for g in ob.vertex_groups]
W = np.zeros((len(me.vertices), len(names)), np.float32)
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
print('HEAT', W.shape, 'unweighted', int((W.sum(1) < 1e-4).sum()))
np.savez(A[1], W=W, names=np.array(names))
