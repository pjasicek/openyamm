"""Head texture set, step 1 (CLAUDE_CREATURE_TEXTURES.md, head-only retexture): mark the head faces, give them their
own UV layout filling 0..1, and export them alone as a neutral GLB for the Meshy head retexture.

Head = Body/Teeth/Hoops faces whose vertices are mostly weighted to mixamorig:Head (the cut falls on the upper neck).
Stores face attribute `head` (1 = head material) in work/final_v1.blend; export_glb.py assigns the GoblinHead
material from it. Body faces keep their UVs and body texture. Writes texturing/gob_head_upload.glb.
Run: blender --background work/final_v1.blend --python scripts/head_split.py"""
import os
import sys

import bpy
import bmesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

HEAD_PARTS = {0, 4, 5}  # Body, Teeth, Hoops (work/uv3d.npz 'parts')

mesh = bpy.data.objects['Peasant']
rig = bpy.data.objects['Peasant_Rig']
rig.animation_data.action = None
for bone in rig.pose.bones:
    bone.matrix_basis.identity()

head_group = mesh.vertex_groups['mixamorig:Head'].index
weight = [sum(g.weight for g in v.groups if g.group == head_group) for v in mesh.data.vertices]
part = mesh.data.attributes['part'].data
head = [part[p.index].value in HEAD_PARTS and sum(weight[v] for v in p.vertices) / len(p.vertices) >= 0.5
        for p in mesh.data.polygons]
if 'head' in mesh.data.attributes:
    mesh.data.attributes.remove(mesh.data.attributes['head'])
attribute = mesh.data.attributes.new('head', 'INT', 'FACE')
attribute.data.foreach_set('value', [int(flag) for flag in head])

bpy.context.view_layer.objects.active = mesh
for obj in bpy.data.objects:
    obj.select_set(obj == mesh)
bpy.ops.object.mode_set(mode='EDIT')
data = bmesh.from_edit_mesh(mesh.data)
for face in data.faces:
    face.select = head[face.index]
bmesh.update_edit_mesh(mesh.data)
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.004, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.pack_islands(margin=0.004, rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_mainfile()

# Neutral head-only copy (rest pose, no armature) for the retexture.
duplicate = mesh.copy()
duplicate.data = mesh.data.copy()
duplicate.modifiers.clear()
duplicate.parent = None
bpy.context.scene.collection.objects.link(duplicate)
data = bmesh.new()
data.from_mesh(duplicate.data)
bmesh.ops.delete(data, geom=[f for f in data.faces if not head[f.index]], context='FACES')
data.to_mesh(duplicate.data)
data.free()
for obj in bpy.data.objects:
    obj.select_set(obj == duplicate)
bpy.context.view_layer.objects.active = duplicate
os.makedirs(os.path.join(common.PROJECT, 'texturing'), exist_ok=True)
path = os.path.join(common.PROJECT, 'texturing', 'gob_head_upload.glb')
bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=False, export_animations=False, export_materials='NONE',
                          export_attributes=False)
print('HEAD_SPLIT faces', sum(head), 'of', len(head), 'exported', path)
