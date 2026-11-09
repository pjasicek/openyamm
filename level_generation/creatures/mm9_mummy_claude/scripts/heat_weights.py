"""Automatic (heat) weights on the master-pose body. Args: <blend> <rig json> <out npz>"""
import bpy, sys, json, os
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rig_bones import bone_table
BL, RIG, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=BL)
ob = bpy.data.objects['Body']; me = ob.data
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
names = [g.name for g in ob.vertex_groups]
W = np.zeros((len(me.vertices), len(names)), np.float32)
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
print('HEAT', W.shape, 'unweighted', int((W.sum(1) < 1e-4).sum()))
np.savez(OUT, W=W, names=np.array(names))
