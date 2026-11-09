"""Export the cockatrice master (skin A material, all clips, Socket_Head) to export/mm6_ckt_lod0.glb.
Faces with the `head` attribute (claude_shared/head_texture_split.py) use CockatriceHead_A: the separate 1K head set
from compose_head_set.py, one material for every tier (only the wing membranes change between palettes).
The body base colour is 1K since the head has its own set (CLAUDE_CREATURE_TEXTURES.md)."""
import bpy, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
mesh = bpy.data.objects['Cockatrice']; rig = bpy.data.objects['Ckt_Rig']
mat = bpy.data.materials.new('Cockatrice_A'); mat.use_nodes = True; nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
def tex(name, cs):
    img = bpy.data.images.load(os.path.join(T, name)); img.colorspace_settings.name = cs
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n
bc = tex('ckt_a_basecolor_graded_1k.png', 'sRGB'); nt.links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
nm = tex('ckt_normal_1k.png', 'Non-Color'); nmap = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(nm.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
mr = tex('ckt_metal_rough_1k.png', 'Non-Color'); sep = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(mr.outputs['Color'], sep.inputs['Color'])
nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
mat.use_backface_culling = False                             # thin wing membranes: visible from both sides
head = bpy.data.materials.new('CockatriceHead_A'); head.use_nodes = True; nt = head.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
nt.links.new(tex('ckt_head_basecolor_graded.png', 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
nmap = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(tex('ckt_head_normal_1k.png', 'Non-Color').outputs['Color'], nmap.inputs['Color'])
nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
sep = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(tex('ckt_head_metal_rough_1k.png', 'Non-Color').outputs['Color'], sep.inputs['Color'])
nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
mesh.data.materials.clear(); mesh.data.materials.append(mat); mesh.data.materials.append(head)
flags = [0] * len(mesh.data.polygons); mesh.data.attributes['head'].data.foreach_get('value', flags)
mesh.data.polygons.foreach_set('material_index', flags)
rig.animation_data.action = bpy.data.actions['Standing']; bpy.context.scene.frame_set(1)
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig) or o.name.startswith('Socket_'))
bpy.context.view_layer.objects.active = rig
out = os.path.join(HERE, 'export', 'mm6_ckt_lod0.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
print('EXPORTED', out)
