"""Blender: turn reactor_geometry.build() into the rigged master work/model_v1.blend (plus Reactor_LOD1-3).

Two skinned mesh objects on one armature: Reactor (Reactor_Metal, Reactor_Glow) and ReactorGlass (Reactor_Glass,
Reactor_Flash; blended, its own glTF node so tools/build_actor_lods.py leaves it out). Every vertex has one bone
weight of 1.0. Faces are smooth; hard edges are vertex splits from the generator. Socket_Arc is an empty on Root.
Materials here are placeholders with image textures; export_glb.py finalises them."""
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import reactor_geometry as G  # noqa: E402

bpy.ops.wm.read_factory_settings(use_empty=True)
result = G.build()
# Authored LODs 1-3 of the opaque node (same bones, UVs and materials; author_lods.py wires them into the GLB).
lods = {f'Reactor_LOD{k}': G.build(lod=k)['meshes']['Reactor'] for k in (1, 2, 3)}
result['meshes'].update(lods)

arm_data = bpy.data.armatures.new('Reactor_Rig')
rig = bpy.data.objects.new('Reactor_Rig', arm_data)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for name, head, parent in result['bones']:
    eb = arm_data.edit_bones.new(name)
    eb.head = Vector(head)
    eb.tail = Vector(head) + Vector((0.0, 0.0, 0.08))
    eb.use_deform = True
for name, head, parent in result['bones']:
    if parent:
        arm_data.edit_bones[name].parent = arm_data.edit_bones[parent]
        arm_data.edit_bones[name].use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')

for node_name, m in result['meshes'].items():
    me = bpy.data.meshes.new(node_name)
    me.from_pydata([Vector(v) for v in m.verts], [], [list(t) for t in m.tris])
    me.update()
    uv = me.uv_layers.new(name='UVMap')
    for poly, uvs, slot in zip(me.polygons, m.uvs, m.mat):
        poly.material_index = slot
        poly.use_smooth = True
        for li, coord in zip(poly.loop_indices, uvs):
            uv.data[li].uv = coord
    for mat_name in m.materials:
        mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
        me.materials.append(mat)
    obj = bpy.data.objects.new(node_name, me)
    bpy.context.scene.collection.objects.link(obj)
    groups = {}
    for index, bone_name in enumerate(m.bone):
        groups.setdefault(bone_name, []).append(index)
    for bone_name, indices in groups.items():
        obj.vertex_groups.new(name=bone_name).add(indices, 1.0, 'REPLACE')
    obj.parent = rig
    mod = obj.modifiers.new('Armature', 'ARMATURE')
    mod.object = rig
    # Consistency: every polygon's vertices share one bone (rigid parts never straddle bones).
    for t in m.tris:
        if len({m.bone[i] for i in t}) != 1:
            raise RuntimeError(f'{node_name}: triangle across bones {[m.bone[i] for i in t]}')

bpy.context.view_layer.update()
for name, (bone_name, position) in result['sockets'].items():
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_size = 0.1
    bpy.context.scene.collection.objects.link(empty)
    empty.parent = rig
    empty.parent_type = 'BONE'
    empty.parent_bone = bone_name
    bpy.context.view_layer.update()
    empty.matrix_world = Matrix.Translation(Vector(position))

os.makedirs(os.path.join(HERE, 'work'), exist_ok=True)
out = os.path.join(HERE, 'work', 'model_v1.blend')
bpy.ops.wm.save_as_mainfile(filepath=out)
counts = {o.name: len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'}
print('SAVED', out, counts, 'bones', len(arm_data.bones))
