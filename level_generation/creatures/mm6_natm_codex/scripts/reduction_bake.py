"""Rebake every candidate from the unreduced textured mesh, including lost detail in tangent normals."""
import bpy,json,time
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def bake(obj,folder):
 folder.mkdir(parents=True,exist_ok=True);scene=bpy.context.scene;rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 # Keep chart layout and rebake surface appearance onto the collapsed charts; no distorted old texture is reused.
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 with bpy.data.libraries.load(str(P/'work/bake_source.blend'),link=False)as(src,dst):dst.objects=[obj.name]
 high=dst.objects[0];scene.collection.objects.link(high);high.name='Bake source';high.parent=rig
 for mod in high.modifiers:
  if mod.type=='ARMATURE':mod.object=rig
 high.hide_render=False;high.hide_set(False)
 # Separate disjoint feathers, cloth and skin during projection so a ray cannot steal another shell's paint.
 exploded=[]
 if 'piece' in obj.data.attributes and 'piece' in high.data.attributes:
  for ob in [obj,high]:
   coords=[v.co.copy()for v in ob.data.vertices];exploded.append((ob,coords))
   for v,piece in zip(ob.data.vertices,ob.data.attributes['piece'].data):v.co.x+=piece.value*4.
   ob.data.update()
 bpy.context.view_layer.update()
 for i,m in enumerate(high.data.materials):high.data.materials[i]=m.copy()
 sources=list(high.data.materials);original=[];source_tex=[]
 for i,m in enumerate(sources):
  nt=m.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');original.append(out.inputs['Surface'].links[0].from_socket)
  base=bs.inputs['Base Color'].links[0].from_node.image;mr=bs.inputs['Roughness'].links[0].from_node.inputs[0].links[0].from_node.image
  tag=('body'if i==0 else'head')if obj.name=='Body'else('spear'if obj.name=='SpearMesh'else'buckler')
  mask=bpy.data.images.load(str(P/f'textures/natm_{tag}_region_mask.png'),check_existing=False);mask.colorspace_settings.name='Non-Color';mask.alpha_mode='CHANNEL_PACKED'
  source_tex.append({'basecolor':base,'metal_rough':mr,'region_mask':mask})
 indices=[f.material_index for f in obj.data.polygons];obj.data.materials.clear();targets=[]
 for i in range(len(sources)):
  mat=bpy.data.materials.new(('Natm_B'if i==0 else'NatmHead_B')if obj.name=='Body'else('NatmSpear_B'if obj.name=='SpearMesh'else'NatmBuckler_B'));mat.use_nodes=True;target=mat.node_tree.nodes.new('ShaderNodeTexImage');mat.node_tree.nodes.active=target;obj.data.materials.append(mat);targets.append(target)
 for f,i in zip(obj.data.polygons,indices):f.material_index=i
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.035;scene.render.bake.max_ray_distance=.08;scene.render.bake.margin=8;scene.render.bake.use_clear=True;scene.render.bake.normal_space='TANGENT';scene.render.bake.normal_r='POS_X';scene.render.bake.normal_g='POS_Y';scene.render.bake.normal_b='POS_Z'
 bpy.ops.object.select_all(action='DESELECT');high.select_set(True);obj.select_set(True);bpy.context.view_layer.objects.active=obj
 maps=[{}for _ in sources];receipt={}
 for key in ['basecolor','region_mask','metal_rough','normal']:
  for i,(m,target)in enumerate(zip(sources,targets)):
   im=bpy.data.images.new(f'{folder.name}_{i}_{key}',width=1024,height=1024,alpha=False);im.colorspace_settings.name='sRGB'if key=='basecolor'else'Non-Color';target.image=im;maps[i][key]=im
   nt=m.node_tree;out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL')
   if key=='normal':nt.links.new(original[i],out.inputs['Surface'])
   else:
    em=nt.nodes.new('ShaderNodeEmission');tex=nt.nodes.new('ShaderNodeTexImage');tex.image=source_tex[i][key]
    if tex.image:nt.links.new(tex.outputs['Color'],em.inputs['Color'])
    else:em.inputs['Color'].default_value=(0,0,0,1)
    nt.links.new(em.outputs[0],out.inputs['Surface'])
  started=time.time();bpy.ops.object.bake(type='NORMAL'if key=='normal'else'EMIT');receipt[key]={'seconds':time.time()-started,'images':[]}
  for i in range(len(sources)):
   im=maps[i][key];im.filepath_raw=str(folder/f'{i}_{key}.png');im.file_format='PNG';im.save();receipt[key]['images'].append(str(Path(im.filepath_raw).relative_to(P)))
  print('REBAKE',folder.name,key,receipt[key]['seconds'],flush=True)
 for i,m in enumerate(obj.data.materials):
  nt=m.node_tree;bs=nt.nodes.get('Principled BSDF');nodes={}
  for key,im in maps[i].items():n=nt.nodes.new('ShaderNodeTexImage');n.image=im;nodes[key]=n
  nt.links.new(nodes['basecolor'].outputs['Color'],bs.inputs['Base Color']);nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(nodes['normal'].outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal']);sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(nodes['metal_rough'].outputs['Color'],sep.inputs[0]);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);nt.nodes.active=nodes['basecolor'];m['openyamm_specular_mask']=True;m['openyamm_specular']=1.
 for ob,coords in exploded:
  for v,co in zip(ob.data.vertices,coords):v.co=co
  ob.data.update()
 bpy.data.objects.remove(high,do_unlink=True);(folder/'receipt.json').write_text(json.dumps(receipt,indent=2));return maps
