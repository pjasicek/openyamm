"""Bake native-style top light and local cloth occlusion for the self-lit Ghost."""
import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master_full.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=32;sc.render.bake.margin=8;sc.render.bake.use_selected_to_active=False
images=[]
for slot,label in enumerate(['body','head']):
 mat=bpy.data.materials.new('NativeShade_'+label);mat.use_nodes=True;body.data.materials[slot]=mat;nt=mat.node_tree;nt.nodes.clear();image=bpy.data.images.new('shade_'+label,1024,1024,alpha=False,float_buffer=True);image.colorspace_settings.name='Non-Color';images.append((label,image));target=nt.nodes.new('ShaderNodeTexImage');target.image=image;nt.nodes.active=target
 ao=nt.nodes.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.08;geo=nt.nodes.new('ShaderNodeNewGeometry');dot=nt.nodes.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=(0,0,1);nt.links.new(geo.outputs['Normal'],dot.inputs[0])
 def mad(socket,mul,add):
  n=nt.nodes.new('ShaderNodeMath');n.operation='MULTIPLY_ADD';nt.links.new(socket,n.inputs[0]);n.inputs[1].default_value=mul;n.inputs[2].default_value=add;return n.outputs[0]
 shade=nt.nodes.new('ShaderNodeMath');shade.operation='MULTIPLY';nt.links.new(mad(ao.outputs['AO'],.75,.25),shade.inputs[0]);nt.links.new(mad(dot.outputs['Value'],.45,.85),shade.inputs[1]);em=nt.nodes.new('ShaderNodeEmission');nt.links.new(shade.outputs[0],em.inputs['Color']);out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(em.outputs[0],out.inputs['Surface'])
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body;bpy.ops.object.bake(type='EMIT')
for label,image in images:image.filepath_raw=str(P/f'work/native_shade_{label}.exr');image.file_format='OPEN_EXR';image.save()

import runpy
runpy.run_path(str(P/'scripts/read_native_shade.py'),run_name='__main__')
