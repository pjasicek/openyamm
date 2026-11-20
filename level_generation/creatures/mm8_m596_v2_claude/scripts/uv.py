"""UV-unwrap the rigged body for the facet texture (Smart UV Project, padded islands) and dump triangles for
texture.py: per triangle the UVs, face normal, centroid, loop vertex ids and head_fix.py's part (1 eye gem, 2 socket) -> work/uv_tris.npz.
Usage: blender -b -P uv.py -- <rig.blend> <out.blend>"""
import os, sys, bpy, bmesh
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, a[0]))
body = bpy.data.objects['CrystalWalker']; me = body.data
while me.uv_layers:
    me.uv_layers.remove(me.uv_layers[0])
me.uv_layers.new(name='UVMap')
bpy.context.view_layer.objects.active = body
for o in bpy.context.view_layer.objects:
    o.select_set(o == body)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.006, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
bpy.ops.object.mode_set(mode='OBJECT')
uv = me.uv_layers.active.data
part_attr = me.attributes.get('part')
parts = [part_attr.data[p.index].value for p in me.polygons] if part_attr else [0] * len(me.polygons)
tri_uv, nrm, cen, vid = [], [], [], []
for p in me.polygons:
    assert len(p.loop_indices) == 3
    tri_uv.append([uv[l].uv[:] for l in p.loop_indices]); nrm.append(p.normal[:]); cen.append(p.center[:])
    vid.append([me.loops[l].vertex_index for l in p.loop_indices])
np.savez(os.path.join(P, 'work', 'uv_tris.npz'), uv=np.array(tri_uv), normal=np.array(nrm), centre=np.array(cen),
         vid=np.array(vid), part=np.array(parts))
print('UV tris', len(tri_uv))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(P, a[1]))
