"""Retexture of a runtime GLB as it is (user: "use the model for head/body I said ok and just retexture that"): its LOD0
mesh with its own UVs becomes work/uv.blend (Body, Rig; one material slot) and work/body_upload.glb (geometry and UVs
only, one neutral material, no skin) for a Meshy retexture with enable_original_uv.
Usage: blender -b -P orig_uv_prep.py -- <runtime glb> [mesh node, default KnightPlate]"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
glb, node = os.path.abspath(a[0]), (a[1] if len(a) > 1 else 'KnightPlate')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
body = bpy.data.objects[node]; body.name = 'Body'
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); rig.name = 'Rig'
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o is not body]:
    bpy.data.objects.remove(o, do_unlink=True)
while len(body.data.materials) > 1:
    body.data.materials.pop()
print('BODY tris', sum(len(p.vertices) - 2 for p in body.data.polygons), 'uv layers', [u.name for u in body.data.uv_layers])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'uv.blend'))
# upload: an unskinned copy at the rest pose with one neutral material
up = body.copy(); up.data = body.data.copy(); up.name = 'Upload'; bpy.context.scene.collection.objects.link(up)
for m in list(up.modifiers):
    up.modifiers.remove(m)
up.parent = None; up.matrix_world = body.matrix_world.copy(); up.vertex_groups.clear()
mat = bpy.data.materials.new('Neutral'); up.data.materials.clear(); up.data.materials.append(mat)
for o in bpy.data.objects:
    o.select_set(o is up)
bpy.context.view_layer.objects.active = up
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work', 'body_upload.glb'), use_selection=True, export_format='GLB',
                          export_animations=False, export_skins=False)
print('UPLOAD', len(up.data.polygons), 'faces -> work/body_upload.glb')
