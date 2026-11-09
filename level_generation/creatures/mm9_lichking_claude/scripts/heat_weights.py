"""Automatic (heat) weights on the skin parts in the master pose. Args: <asm npz> <rig json> <out npz>"""
import bpy, sys, json, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rig_bones import bone_table
NPZ, RIG, OUT = sys.argv[sys.argv.index('--') + 1:]
D = np.load(NPZ); co, tri, comp = D['co'], D['tri'], D['comp']; names = [str(x) for x in D['names']]
SK = [names.index(n) for n in ('torso', 'pants', 'hands', 'boots', 'uarms')]
keep = np.isin(comp, SK); rem = -np.ones(len(co), int); rem[keep] = np.arange(keep.sum())
tt = rem[tri[keep[tri[:, 0]]]]
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('b'); me.from_pydata(co[keep].tolist(), [], tt.tolist()); me.update()
ob = bpy.data.objects.new('Body', me); bpy.context.collection.objects.link(ob)
R = json.load(open(RIG)); T = bone_table(R['joints'], R['fingers'])
ad = bpy.data.armatures.new('rig'); arm = bpy.data.objects.new('rig', ad); bpy.context.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm; arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for n, (p, h, t) in T.items():
    b = ad.edit_bones.new(n); b.head = h; b.tail = t
for n, (p, h, t) in T.items():
    if p: ad.edit_bones[n].parent = ad.edit_bones[p]
bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.context.selected_objects: o.select_set(False)
ob.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
gn = [g.name for g in ob.vertex_groups]
W = np.zeros((len(co), len(gn)), np.float32); idx = np.where(keep)[0]
for v in me.vertices:
    for g in v.groups: W[idx[v.index], g.group] = g.weight
print('HEAT', W.shape, 'unweighted skin', int((W[keep].sum(1) < 1e-4).sum()))
np.savez(OUT, W=W, names=np.array(gn))
