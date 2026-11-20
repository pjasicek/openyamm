"""Export the demon master (body + head skin materials, all clips, palm/eye sockets) to export/mm6_wdm_lod0.glb.
Tiers are added afterwards as tinted material copies (add_variants.py)."""
import bpy, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
mesh = bpy.data.objects['Demon']; rig = bpy.data.objects['Demon_Rig']


def material(name, prefix, basecolor):
    """Skin material: base colour (sRGB), normal map, MR texture (R tint mask, G roughness, B metallic)."""
    mat = bpy.data.materials.new(name); mat.use_nodes = True; mat.use_backface_culling = False; nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(file, cs):
        img = bpy.data.images.load(os.path.join(T, file)); img.colorspace_settings.name = cs
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n

    bc = tex(basecolor, 'sRGB'); nt.links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
    nm = tex(f'{prefix}_normal_1k.png', 'Non-Color'); nmap = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(nm.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    mr = tex(f'{prefix}_metal_rough_1k.png', 'Non-Color'); sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(mr.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat


# slot 0 body, slot 1 the grafted head (graft_head.py) when present
mats = [material('Demon', 'wdm', 'wdm_basecolor_graded_1k.png')]
if len(mesh.data.materials) > 1:
    mats.append(material('DemonHead', 'wdm_head', 'wdm_head_basecolor.png'))
for i, m in enumerate(mats):          # assign in place: clearing the slots would reset every face to slot 0
    if i < len(mesh.data.materials):
        mesh.data.materials[i] = m
    else:
        mesh.data.materials.append(m)
rig.animation_data_create(); rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
sockets = []
for side in ('Left', 'Right'):
    for name, bone, at in ((f'Socket_Palm_{side}', f'mixamorig:{side}Hand', 0.5),):
        e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e)
        b = rig.data.bones[bone]
        e.matrix_world = rig.matrix_world @ __import__('mathutils').Matrix.Translation(b.head_local.lerp(b.tail_local, at))
        mw = e.matrix_world.copy(); e.parent = rig; e.parent_type = 'BONE'; e.parent_bone = bone; e.matrix_world = mw
        sockets.append(e)
rig.animation_data.action = bpy.data.actions['Flight']; bpy.context.scene.frame_set(0)
for o in bpy.data.objects:
    o.select_set(o in [mesh, rig] + sockets)
bpy.context.view_layer.objects.active = rig
out = os.path.join(HERE, 'export', 'mm6_wdm_lod0.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
print('EXPORTED', out)
