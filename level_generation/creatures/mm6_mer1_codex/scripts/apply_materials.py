import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/prop_audited.blend'));body=bpy.data.objects['Body'];prop=bpy.data.objects['ClubMesh'];r=bpy.data.objects['Rig'];s=bpy.context.scene;T=P/'textures'
def material(name,prefix):
 m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
 def tex(kind,color):
  n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(T/f'mer1_{prefix}_{kind}{"_1k"if prefix!="club"else""}.png'));n.image.colorspace_settings.name=color;return n
 b=tex('basecolor','sRGB');nt.links.new(b.outputs['Color'],bs.inputs['Base Color']);nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal','Non-Color').outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal']);sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('metal_rough','Non-Color').outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);nt.nodes.active=b;m['openyamm_specular_mask']=True;m['openyamm_specular']=1.;return m
body.data.materials.clear();body.data.materials.append(material('Merchant_A','body'));body.data.materials.append(material('MerchantHead_A','head'));hd=[x.value for x in body.data.attributes['head'].data];buv=body.data.uv_layers['UVMap'].data;huv=body.data.uv_layers['HeadUV'].data
for f in body.data.polygons:
 f.material_index=hd[f.index]
 if hd[f.index]:
  for li in f.loop_indices:buv[li].uv=huv[li].uv
body.data.uv_layers.remove(body.data.uv_layers['HeadUV']);body.data.uv_layers.active=body.data.uv_layers['UVMap'];body.data.uv_layers['UVMap'].active_render=True
prop.data.materials.clear();prop.data.materials.append(material('MerchantClub','club'))
for v in prop.data.uv_layers.active.data:
 u,w=v.uv;v.uv=((u*1536-32)/1472,1-((1-w)*1024-80)/378)
heights=[];a=bpy.data.actions['Walking'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
for f in np.arange(0,24.01,.625):
 s.frame_set(int(f),subframe=float(f%1));lo,hi=common.world_bounds([body]);heights.append(hi.z-lo.z)
(P/'work/runtime_scale.json').write_text(json.dumps({'native_height':253*.699997,'walk_height_m':max(heights),'scale':253*.699997/max(heights),'yaw_offset':-1.570796327,'stride_length':.84},indent=2))
a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];s.frame_set(0);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'));common.workbench_clay(s,True)
for tier in ['a','b','c']:
 mat=body.data.materials[0];bs=mat.node_tree.nodes.get('Principled BSDF');node=bs.inputs['Base Color'].links[0].from_node;node.image=bpy.data.images.load(str(T/f'mer1_{tier}_preview.png'));mat.node_tree.nodes.active=node
 common.render_views(str(P/'review'/f'tier_{tier}'),.86,1.92,views=('front','left','back','right','three_quarter'),resolution=(600,800))
