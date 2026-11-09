"""Export the cobra master (shared skin material 'Cobra', all clips) to export/mm6_cob_lod0.glb.
Tiers are added afterwards by claude_shared/region_variants.py (region mask + ramps)."""
import bpy, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
mesh = bpy.data.objects['Cobra']; rig = bpy.data.objects['Cobra_Rig']
mat = bpy.data.materials.new('Cobra'); mat.use_nodes = True; mat.use_backface_culling = False; nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')


def tex(file, cs):
    img = bpy.data.images.load(os.path.join(T, file)); img.colorspace_settings.name = cs
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n


nt.links.new(tex('cob_basecolor_graded.png', 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
nm = tex('cob_normal_1k.png', 'Non-Color'); nmap = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(nm.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
mr = tex('cob_metal_rough_1k.png', 'Non-Color'); sep = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(mr.outputs['Color'], sep.inputs['Color'])
nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
mesh.data.materials.clear(); mesh.data.materials.append(mat)
rig.animation_data_create(); rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
rig.animation_data.action = bpy.data.actions['Standing']; bpy.context.scene.frame_set(0)
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
out = os.path.join(HERE, 'export', 'mm6_cob_lod0.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
print('EXPORTED', out)
