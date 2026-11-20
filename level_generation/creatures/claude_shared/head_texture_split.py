"""Head texture set, step 1 (CLAUDE_CREATURE_TEXTURES.md "Head-only retexture"), shared by Claude projects.

Marks the head faces with face attribute `head`, gives them their own UV layout filling 0..1 (body faces keep their
UVs), saves the master, and exports the head faces alone (rest pose, no armature) as a neutral GLB for the Meshy head
retexture. The project's export then assigns a head material from `head`.

Head = faces whose vertices are mostly weighted to the head groups, restricted to --parts when given, plus every face
of --whole-parts (e.g. a braid that hangs below the head). Part ids come from the mesh's FACE attribute `part`.
Run: blender --background <master.blend> --python head_texture_split.py -- --mesh Peasant --rig Peasant_Rig \
       --out texturing/<x>_head_upload.glb [--groups mixamorig:Head] [--parts 0 3] [--whole-parts 9]"""
import argparse
import os
import sys

import bmesh
import bpy

args = argparse.ArgumentParser()
args.add_argument('--mesh', required=True)
args.add_argument('--rig', required=True)
args.add_argument('--out', required=True)
args.add_argument('--groups', nargs='+', default=['mixamorig:Head'])
args.add_argument('--parts', nargs='*', type=int, default=None)
args.add_argument('--whole-parts', nargs='*', type=int, default=[])
options = args.parse_args(sys.argv[sys.argv.index('--') + 1:])

mesh = bpy.data.objects[options.mesh]
rig = bpy.data.objects[options.rig]
if rig.animation_data:
    rig.animation_data.action = None
for bone in rig.pose.bones:
    bone.matrix_basis.identity()

groups = {mesh.vertex_groups[name].index for name in options.groups if name in mesh.vertex_groups}
weight = [sum(g.weight for g in v.groups if g.group in groups) for v in mesh.data.vertices]
part = mesh.data.attributes['part'].data if 'part' in mesh.data.attributes else None


def is_head(polygon):
    part_id = part[polygon.index].value if part is not None else 0
    if part_id in options.whole_parts:
        return True
    if options.parts is not None and part_id not in options.parts:
        return False
    return sum(weight[v] for v in polygon.vertices) / len(polygon.vertices) >= 0.5


head = [is_head(p) for p in mesh.data.polygons]
if 'head' in mesh.data.attributes:
    mesh.data.attributes.remove(mesh.data.attributes['head'])
mesh.data.attributes.new('head', 'INT', 'FACE').data.foreach_set('value', [int(flag) for flag in head])

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
out = os.path.abspath(options.out)
os.makedirs(os.path.dirname(out), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=False, export_animations=False, export_materials='NONE',
                          export_attributes=False)
print('HEAD_SPLIT faces', sum(head), 'of', len(head), 'exported', out)
