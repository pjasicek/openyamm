"""Apply the shared materials and export only the nine production actions and the creature rig."""
from pathlib import Path
import bpy
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/uv_master_v3.blend'))
mesh = bpy.data.objects['Couatl']
rig = bpy.data.objects['Couatl_Rig']
if 'Stress' in bpy.data.actions:
    bpy.data.actions.remove(bpy.data.actions['Stress'])
mat = bpy.data.materials.new('Couatl_A')
mat.use_nodes = True
mat.use_backface_culling = False
mat['openyamm_specular'] = 1.
mat['openyamm_specular_mask'] = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
def tex(name,space):
    img = bpy.data.images.load(str(P/'textures'/name))
    img.colorspace_settings.name = space
    img.pack()
    node = nt.nodes.new('ShaderNodeTexImage')
    node.image = img
    return node
nt.links.new(tex('m408_basecolor.png','sRGB').outputs['Color'],bsdf.inputs['Base Color'])
normal = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(tex('m408_normal.png','Non-Color').outputs['Color'],normal.inputs['Color'])
nt.links.new(normal.outputs['Normal'],bsdf.inputs['Normal'])
split = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(tex('m408_metal_rough.png','Non-Color').outputs['Color'],split.inputs['Color'])
nt.links.new(split.outputs['Green'],bsdf.inputs['Roughness'])
nt.links.new(split.outputs['Blue'],bsdf.inputs['Metallic'])
mesh.data.materials.clear()
mesh.data.materials.append(mat)
rig.animation_data.action = bpy.data.actions['Standing']
bpy.context.scene.frame_set(0)
for obj in bpy.context.scene.objects:
    obj.select_set(obj in (mesh,rig))
bpy.context.view_layer.objects.active = rig
(P/'export').mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/m408_textured_master.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm8_m408_lod0.glb'),use_selection=True,
    export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',
    export_frame_range=False,export_force_sampling=True,export_frame_step=1,export_skins=True,
    export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',
    export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=True)
print('EXPORTED Couatl with',len(bpy.data.actions),'actions')

import sys
sys.path.insert(0,str(P/"scripts"))
from material_contract import finish
finish(P/"export/mm8_m408_lod0.glb")
