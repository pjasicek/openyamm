"""Apply the shared bat material (double-sided membrane) and export the rig, mesh and clips of work/uv_r1.blend
to export/mm7_m158_lod0.glb; saves work/m158_textured_master.blend (packed images)."""
from pathlib import Path
import bpy
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/uv_r1.blend'))  # reduce_lod0.py 0.5 0.75 of uv_master
mesh = bpy.data.objects['Bat']; rig = bpy.data.objects['Bat_Rig']
mat = bpy.data.materials.new('Bat_A'); mat.use_nodes = True; mat.use_backface_culling = False
mat['openyamm_specular'] = 1.0; mat['openyamm_specular_mask'] = True
nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
def tex(name, space):
    img = bpy.data.images.load(str(P / 'textures' / name)); img.colorspace_settings.name = space; img.pack()
    node = nt.nodes.new('ShaderNodeTexImage'); node.image = img; return node
nt.links.new(tex('bat_basecolor.png', 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
nm = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(tex('bat_normal.png', 'Non-Color').outputs['Color'], nm.inputs['Color'])
nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
sep = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(tex('bat_metal_rough.png', 'Non-Color').outputs['Color'], sep.inputs['Color'])
nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
mesh.data.materials.clear(); mesh.data.materials.append(mat)
rig.animation_data.action = bpy.data.actions['Fly']; bpy.context.scene.frame_set(1)
for o in bpy.context.scene.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
(P / 'export').mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/m158_textured_master.blend'))
bpy.ops.export_scene.gltf(filepath=str(P / 'export/mm7_m158_lod0.glb'), use_selection=True, export_format='GLB',
    export_yup=True, export_animations=True, export_animation_mode='ACTIONS', export_frame_range=False,
    export_force_sampling=True, export_frame_step=1, export_skins=True, export_all_influences=False,
    export_attributes=False, export_morph=False, export_image_format='AUTO', export_reset_pose_bones=True,
    export_anim_slide_to_zero=True, export_extras=True)
print('EXPORTED', sorted(a.name for a in bpy.data.actions))
