"""Teeth budget (modelling guidelines: no micro triangles): the 36 teeth and the gum (pieces 1-36, 3,975 tris of the
15.4k LOD0, each tooth ~4 cm with ~100 tris) are collapse-decimated to RATIO in place on work/anim_v2u.blend; UVs
and their rigid Head/Jaw weights survive (collapse interpolates both). Args: -- <blend> [ratio]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
blend = a[0]; RATIO = float(a[1]) if len(a) > 1 else 0.3
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
ob = bpy.data.objects['Body']; me = ob.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
before = sum(len(p.vertices) - 2 for p in me.polygons)
for o in bpy.data.objects:
    o.select_set(o == ob)
bpy.context.view_layer.objects.active = ob
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
for p in me.polygons:
    p.select = bool(pv[p.vertices[0]] > 0)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.decimate(ratio=RATIO, use_vertex_group=False)
bpy.ops.object.mode_set(mode='OBJECT')
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
teeth = sum(len(p.vertices) - 2 for p in me.polygons if pv[p.vertices[0]] > 0)
print('TEETH', before, '->', sum(len(p.vertices) - 2 for p in me.polygons), 'tris; teeth now', teeth)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(blend))
