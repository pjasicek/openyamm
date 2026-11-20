"""Apply verified texture maps to the retained animated master and export."""
import bpy,json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];T=P/'textures'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated.blend'))
m=bpy.data.objects['CrystalDragon'];rig=bpy.data.objects['CrystalDragonRig']
mat=bpy.data.materials.new('CrystalDragon');mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF')
mat['openyamm_specular']=.45;mat['openyamm_specular_mask']=True;mat['openyamm_edge_darkening']=.35
mat.use_backface_culling=True
bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.39
for name,cs in [('basecolor','sRGB'),('normal','Non-Color'),('orm','Non-Color')]:
 node=nt.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(T/f'crystal_{name}.png'));node.image.colorspace_settings.name=cs
 if name=='basecolor':nt.links.new(node.outputs['Color'],bs.inputs['Base Color'])
 elif name=='normal':
  bump=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(node.outputs['Color'],bump.inputs['Color']);nt.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
 else:
  sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(node.outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
m.data.materials.clear();m.data.materials.append(mat)
for f in m.data.polygons:f.material_index=0
rig.animation_data.action=bpy.data.actions['Standing'];bpy.context.scene.frame_set(1)
for img in bpy.data.images:
 if img.source=='FILE':img.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm8_m548.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in [m,rig,bpy.data.objects['Socket_Mouth']]:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm8_m548_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=True)
print('EXPORTED',flush=True)
