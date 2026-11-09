"""Portable animated master and runtime-source GLB with two shared stone texture sets."""
import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];T=P/'textures'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated.blend'))
rig=bpy.data.objects['JuggernautRig']
for part in ['body','head']:
 name='Juggernaut'+part.title();mat=bpy.data.materials.get(name);mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear();bs=nt.nodes.new('ShaderNodeBsdfPrincipled');out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
 mat['openyamm_specular']=1.;mat['openyamm_specular_mask']=True;mat['openyamm_edge_darkening']=.65;mat.use_backface_culling=True
 for key,cs in [('basecolor','sRGB'),('normal','Non-Color'),('orm','Non-Color')]:
  node=nt.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(T/f'{part}_{key}.png'));node.image.colorspace_settings.name=cs
  if key=='basecolor':nt.links.new(node.outputs['Color'],bs.inputs['Base Color'])
  elif key=='normal':
   normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(node.outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
  else:
   sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(node.outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
 o=bpy.data.objects[part.title()];o.data.materials.clear();o.data.materials.append(mat)
 for f in o.data.polygons:f.material_index=0
for name,color,alpha in [('Eyes',(1,.91,.32,1),1),('Flash',(1,.80,.14,1),.75)]:
 o=bpy.data.objects[name];mat=bpy.data.materials.new(name);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=color;bs.inputs['Emission Color'].default_value=color;bs.inputs['Emission Strength'].default_value=1;bs.inputs['Alpha'].default_value=alpha;bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=1
 mat['openyamm_edge_darkening']=0.;mat['openyamm_specular']=0.;mat.use_backface_culling=name=='Eyes'
 if alpha<1:mat.surface_render_method='BLENDED'
 o.data.materials.clear();o.data.materials.append(mat)
body=bpy.data.objects['Body'];head=bpy.data.objects['Head'];bpy.ops.object.select_all(action='DESELECT');body.select_set(True);head.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name='Juggernaut'
rig.animation_data.action=bpy.data.actions['Standing'];bpy.context.scene.frame_set(1)
for im in bpy.data.images:
 if im.source=='FILE':im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm8_m608.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
 if o.type in ['MESH','ARMATURE'] or o.name.startswith('Socket_'):o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm8_m608_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=True)
print('EXPORTED_JUGGERNAUT',flush=True)
