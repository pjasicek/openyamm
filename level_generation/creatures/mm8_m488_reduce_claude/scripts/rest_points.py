"""Posed probe points -> rest-pose positions of the nearest source vertices (to build keep patches around them).
Usage: REA_POINTS='Running:15:0.12,-0.19,0.80;...' blender -b -P rest_points.py"""
import os, bpy, bmesh
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
for item in os.environ['REA_POINTS'].split(';'):
    clip, f, xyz = item.split(':'); p = Vector([float(x) for x in xyz.split(',')])
    rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(int(f))
    b = bmesh.new(); b.from_object(src, bpy.context.evaluated_depsgraph_get()); b.transform(src.matrix_world)
    b.verts.ensure_lookup_table()
    i = min(range(len(b.verts)), key=lambda k: (b.verts[k].co - p).length)
    print('REST', item, i, tuple(round(c, 4) for c in src.data.vertices[i].co)); b.free()
