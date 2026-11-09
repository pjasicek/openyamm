"""Export work/master.blend (all clips) to export/mm6_bld_lod0.glb with two materials: Bld_A (the installed body texture
set from ../mm6_bld_claude/textures; base colour downsized to 1K by compose_head.py) and BldHead_A (the head set from textures/, compose_head.py), chosen
per face by the `head` attribute."""
import os

import bpy

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BODY = os.path.join(os.path.dirname(HERE), 'mm6_bld_claude', 'textures')
BODY_BASE = os.path.join(HERE, 'textures', 'bld_a_basecolor_graded_1k.png')   # 1K body with a head set (merge needs equal sizes)
HEAD = os.path.join(HERE, 'textures')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'master.blend'))
mesh = bpy.data.objects['Bld']
rig = bpy.data.objects['Bld_Rig']


def material(name, folder, base, normal, metal_rough):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = False
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(file, colorspace):
        img = bpy.data.images.load(os.path.join(folder, file))
        img.colorspace_settings.name = colorspace
        node = nt.nodes.new('ShaderNodeTexImage')
        node.image = img
        return node
    nt.links.new(tex(base, 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])  # base: path relative to folder or absolute
    nmap = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(tex(normal, 'Non-Color').outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(tex(metal_rough, 'Non-Color').outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat


mesh.data.materials.clear()
mesh.data.materials.append(material('Bld_A', BODY, BODY_BASE, 'bld_normal_1k.png',
                                    'bld_metal_rough_1k.png'))
mesh.data.materials.append(material('BldHead_A', HEAD, 'bld_head_basecolor_graded.png', 'bld_head_normal_1k.png',
                                    'bld_head_metal_rough_1k.png'))
head = mesh.data.attributes['head'].data
for p in mesh.data.polygons:
    p.material_index = head[p.index].value
rig.animation_data.action = bpy.data.actions['Fly']
bpy.context.scene.frame_set(1)
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
out = os.path.join(HERE, 'export', 'mm6_bld_lod0.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
print('EXPORTED', out)
