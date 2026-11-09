"""Apply verified PBR maps to the retained master; never ingest Meshy's normalized static body."""
import bpy,json
from pathlib import Path
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006');ROOT=OUT.parent;maps=ROOT/'meshy/body_texture_v1'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'work/native_uv_v1.blend'));body=bpy.data.objects['Goblin_Body']
images={}
for semantic in ['base_color','roughness','metallic','normal']:
 image=bpy.data.images.load(str(maps/f'texture_urls_0_{semantic}.png'),check_existing=False);image.name='Goblin Meshy 4K '+semantic;image.colorspace_settings.name='sRGB' if semantic=='base_color' else 'Non-Color';image.pack();images[semantic]=image
for mat in body.data.materials:
 name=mat.name;mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');bsdf=nodes.new('ShaderNodeBsdfPrincipled');mat.node_tree.links.new(bsdf.outputs['BSDF'],out.inputs['Surface'])
 for semantic,target in [('base_color','Base Color'),('roughness','Roughness'),('metallic','Metallic')]:
  tex=nodes.new('ShaderNodeTexImage');tex.name=semantic;tex.image=images[semantic]
  if semantic=='metallic' and any(k in name.lower() for k in ['skin','leather','tooth','mouth']):bsdf.inputs['Metallic'].default_value=0
  else:mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs[target])
 tex=nodes.new('ShaderNodeTexImage');tex.name='normal';tex.image=images['normal'];normal=nodes.new('ShaderNodeNormalMap');normal.space='TANGENT';normal.inputs['Strength'].default_value=.65;normal.uv_map='Goblin_Atlas_4K';mat.node_tree.links.new(tex.outputs['Color'],normal.inputs['Color']);mat.node_tree.links.new(normal.outputs['Normal'],bsdf.inputs['Normal'])
 mat['source']='Meshy body_texture_v1 4K PBR';mat['material_role']=name
bpy.context.scene.view_layers[0].material_override=None
arm=bpy.data.objects['Goblin_Rig'];a=bpy.data.actions['Standing'];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'work/native_textured_v1.blend'));print('Applied maps to original UV master, retained rig and all native actions.',flush=True)
