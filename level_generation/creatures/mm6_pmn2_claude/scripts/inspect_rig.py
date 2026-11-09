"""Inspect a Meshy rig return: skeleton, actions, mesh match vs our export, and per-part dominant bones/weight mix."""
import bpy, sys, os, json, collections
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
src = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(src))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
print('ARM', arm.name, 'scale', tuple(round(x, 4) for x in arm.matrix_world.to_scale()), 'bones', len(arm.data.bones))
for b in arm.data.bones:
    h = arm.matrix_world @ b.head_local; t = arm.matrix_world @ b.tail_local
    print('BONE', b.name, 'parent', b.parent.name if b.parent else None, 'head', [round(x, 3) for x in h], 'tail', [round(x, 3) for x in t])
print('ACTIONS', [(a.name, tuple(round(x) for x in a.frame_range)) for a in bpy.data.actions])
for m in meshes:
    me = m.data
    print('MESH', m.name, 'verts', len(me.vertices), 'polys', len(me.polygons), 'groups', len(m.vertex_groups), 'uv', [u.name for u in me.uv_layers])
