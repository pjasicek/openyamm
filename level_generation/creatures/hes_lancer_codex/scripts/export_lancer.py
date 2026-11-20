"""Export the shared heavy body and both rigid lance configurations; materials/tier data follow in Python."""
import json
import os
from pathlib import Path
import sys

import bmesh
import bpy

P = Path(__file__).resolve().parents[1]
args = sys.argv[sys.argv.index('--') + 1:]
source = Path(args[0]).resolve()
forge = len(args) > 1 and args[1] == 'forge'


def texture_material(name):
    material = bpy.data.materials[name]
    material.use_nodes = True
    nt = material.node_tree
    bsdf = nt.nodes.get('Principled BSDF')
    for node in list(nt.nodes):
        if node.type in ('TEX_IMAGE', 'NORMAL_MAP', 'SEPARATE_COLOR'):
            nt.nodes.remove(node)
    bsdf.inputs['Metallic'].default_value = 0.0
    for suffix, color_space, socket in [('basecolor', 'sRGB', 'Base Color'),
                                        ('normal', 'Non-Color', 'Normal'),
                                        ('metal_rough', 'Non-Color', 'Roughness')]:
        node = nt.nodes.new('ShaderNodeTexImage')
        node.image = bpy.data.images.load(str(P / f'textures/{"forge_armour" if forge else "hkr_armour"}_{suffix}.png'))
        node.image.colorspace_settings.name = color_space
        if suffix == 'normal':
            converter = nt.nodes.new('ShaderNodeNormalMap')
            nt.links.new(node.outputs['Color'], converter.inputs['Color'])
            nt.links.new(converter.outputs['Normal'], bsdf.inputs[socket])
        elif suffix == 'metal_rough':
            converter = nt.nodes.new('ShaderNodeSeparateColor')
            nt.links.new(node.outputs['Color'], converter.inputs['Color'])
            nt.links.new(converter.outputs['Green'], bsdf.inputs[socket])
            if forge:
                nt.links.new(converter.outputs['Blue'], bsdf.inputs['Metallic'])
        else:
            nt.links.new(node.outputs['Color'], bsdf.inputs[socket])


exports = [('Thunder_Maul', 'hes_forgemaster')] if forge else [('Rifle', 'hes_lancer'), ('TwinLance', 'hes_lancer_twin')]
for weapon, output in exports:
    bpy.ops.wm.open_mainfile(filepath=str(source))
    rig = bpy.data.objects['Rig']
    body = bpy.data.objects['Body']
    rig.animation_data_clear()
    for bone in rig.pose.bones:
        bone.matrix_basis.identity()
    bpy.context.view_layer.update()
    texture_material('HKR_Plate')
    if not forge:
        texture_material('Lancer_Ancient')
    glow = bpy.data.materials['HKR_Glow']
    glow.use_nodes = True
    bsdf = glow.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = ((.08,.008,.001,1) if forge else (0.7,0.25,0.035,1))
    bsdf.inputs['Emission Color'].default_value = ((1,.20,.015,1) if forge else (1,0.42,0.08,1))
    bsdf.inputs['Emission Strength'].default_value = 1
    bsdf.inputs['Metallic'].default_value = 0
    glow['openyamm_bloom'] = True
    hidden = [v.value for v in body.data.attributes['shell_hidden'].data]
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.verts.ensure_lookup_table()
    dead = [f for f in bm.faces if all(hidden[v.index] for v in f.verts)]
    bmesh.ops.delete(bm, geom=dead, context='FACES_ONLY')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(body.data)
    bm.free()
    # Spend the reduction on broad skin surfaces; preserve the fingers, clawed feet, face and loose native details.
    before_reduction = sum(len(p.vertices)-2 for p in body.data.polygons)
    labels = body.data.attributes['piece']
    group_names = [g.name for g in body.vertex_groups]
    protect = body.vertex_groups.new(name='_lancer_protect')
    for vertex in body.data.vertices:
        fine = labels.data[vertex.index].value != 0 or any(e.weight > .2 and
            any(part in group_names[e.group] for part in ('Hand', 'Finger', 'Foot', 'Toe', 'B_Head'))
            for e in vertex.groups if e.group < len(group_names))
        if fine:
            protect.add([vertex.index], 1.0, 'REPLACE')
    modifier = body.modifiers.new('Broad skin reduction', 'DECIMATE')
    modifier.ratio = .70
    modifier.vertex_group = protect.name
    modifier.invert_vertex_group = True
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_move_to_index(modifier=modifier.name, index=0)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    remaining = body.vertex_groups.get('_lancer_protect')
    if remaining is not None:
        body.vertex_groups.remove(remaining)
    print('BODY_REDUCTION', before_reduction, '->', sum(len(p.vertices)-2 for p in body.data.polygons), flush=True)
    # The imported primitive uses the original body textures; variant extras are rebuilt against exported indices.
    for material in bpy.data.materials:
        for key in list(material.keys()):
            if key.startswith('openyamm_region'):
                del material[key]
    parts = [body, bpy.data.objects[weapon]] + [o for o in bpy.data.objects if o.type == 'MESH' and
              (o.name.startswith(('Arm_', 'Apron_')) or (not forge and o.name == 'Ancient_Graft'))]
    for obj in bpy.data.objects:
        obj.select_set(obj in parts)
    for obj in parts:
        obj.modifiers.clear()
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    body = bpy.context.view_layer.objects.active
    body.name = body.data.name = 'Lancer'
    # This master contains only level zero; source mesh indices no longer describe its geometry.
    for key in ('openyamm_lods','openyamm_shadow_lods'):
        if key in body.data:
            del body.data[key]
    for name in ('piece', 'garment', 'thin_co', 'shell_hidden'):
        if name in body.data.attributes:
            body.data.attributes.remove(body.data.attributes[name])
    body.parent = rig
    body.modifiers.new('Armature', 'ARMATURE').object = rig
    keep = lambda a: a.name.startswith(('Carbine_', 'Demon_', 'Lancer_', 'Forge_')) and not '.00' in a.name
    for action in list(bpy.data.actions):
        if not keep(action):
            bpy.data.actions.remove(action)
    rig.animation_data_create()
    rig.animation_data.action = bpy.data.actions['Carbine_Standing']
    if rig.animation_data.action.slots:
        rig.animation_data.action_slot = rig.animation_data.action.slots[0]
    for obj in bpy.data.objects:
        obj.select_set(obj in (body, rig))
    bpy.context.view_layer.objects.active = rig
    bpy.context.scene.render.fps = 60 if forge else 30
    if forge:
        # Preserve the half-frame arm fit when the glTF exporter samples whole frames.
        for action in bpy.data.actions:
            before = tuple(action.frame_range)
            for layer in action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for curve in bag.fcurves:
                            for key in curve.keyframe_points:
                                key.co.x *= 2
                                key.handle_left.x *= 2
                                key.handle_right.x *= 2
                            curve.update()
            if action.use_frame_range:
                action.frame_end=before[1]*2
                action.frame_start=before[0]*2
            assert all(abs(actual-2*old)<1e-4 for actual,old in zip(action.frame_range,before)), (action.name,before,tuple(action.frame_range))
    bpy.ops.export_scene.gltf(filepath=str(P / f'export/{output}_lod0.glb'), use_selection=True,
        export_format='GLB', export_yup=True, export_animations=True, export_animation_mode='ACTIONS',
        export_force_sampling=True, export_frame_step=1, export_skins=True, export_all_influences=False,
        export_attributes=False, export_morph=False, export_extras=True, export_reset_pose_bones=True,
        export_anim_slide_to_zero=True)
    triangles = sum(len(p.vertices)-2 for p in body.data.polygons)
    assert triangles < 15000, (output, triangles)
    print('EXPORT', output, triangles, 'triangles', len(dead), 'hidden skin faces removed')
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(P / f'export/{output}.blend'))

sys.stdout.flush();os._exit(0)
