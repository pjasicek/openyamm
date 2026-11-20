"""Dump Body (verts, faces, part) and the MM9 rig to npz for analysis. Args: blend, mm9 glb, out npz"""
import bpy, sys, json
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
BL, MM9, OUT = argv
bpy.ops.wm.open_mainfile(filepath=BL)
b = bpy.data.objects['Body']; me = b.data
v = np.array([b.matrix_world @ x.co for x in me.vertices]); f = np.array([list(p.vertices) for p in me.polygons])
part = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', part)
ex = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MM9)
new = [x for x in bpy.data.objects if x not in ex]
m = next(x for x in new if x.type == 'MESH' and 'd_lich' in x.name)
a = next(x for x in new if x.type == 'ARMATURE')
if a.animation_data:
    a.animation_data.action = None
for p in a.pose.bones:
    p.matrix_basis.identity()
bpy.context.view_layer.update()
mv = np.array([m.matrix_world @ x.co for x in m.data.vertices]); mf = np.array([list(p.vertices) for p in m.data.polygons])
lab = []
for x in m.data.vertices:
    g = max(x.groups, key=lambda g: g.weight); lab.append(m.vertex_groups[g.group].name)
bn = [x.name for x in a.data.bones]; bp = [x.parent.name if x.parent else '' for x in a.data.bones]
J = np.array([a.matrix_world @ x.head_local for x in a.data.bones])
Tl = np.array([a.matrix_world @ x.tail_local for x in a.data.bones])
np.savez(OUT, v=v, f=f, part=part, mv=mv, mf=mf, lab=np.array(lab), bn=np.array(bn), bp=np.array(bp), J=J, Tl=Tl)
