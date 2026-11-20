"""Selected-to-active reproject base, region weights, packed material map and tangent normals."""
import bpy,json
from project_maps import project
from pathlib import Path
P=Path(__file__).resolve().parents[1]
TAGS={'Natf_A':'natf_body','NatfHead_A':'natf_head','ForearmBlade_A':'blade','LeafShield_A':'natf_shield'}
def bake(target,source,folder,tag,size=1024):
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=1;sc.render.threads_mode='FIXED';sc.render.threads=4
 sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
 source.hide_render=False;source.hide_set(False);source.modifiers.clear();sc.tool_settings.mesh_select_mode=(False,False,True)
 originals=list(target.data.materials);ti=[f.material_index for f in target.data.polygons];si=[f.material_index for f in source.data.polygons]
 source.data.materials.clear();target.data.materials.clear();rows=[]
 for i,original in enumerate(originals):
  high=original.copy();high.name=original.name+'_High';source.data.materials.append(high)
  low=original.copy();low.name=original.name+'_Rebaked';low['source_material']=original.name;target.data.materials.append(low)
  
  if TAGS[original.name]in ['natf_body','natf_head']:
   bs=high.node_tree.nodes.get('Principled BSDF');nm=bs.inputs['Normal'].links[0].from_node;tex=nm.inputs['Color'].links[0].from_node;tex.image=bpy.data.images.load(str(P/f"textures/{TAGS[original.name]}_normal_gl.png"),check_existing=True);tex.image.colorspace_settings.name='Non-Color'
  row={'high':high,'low':low,'tag':TAGS[original.name],'name':original.name,'maps':{}}
  rows.append(row)
 for f,i in zip(target.data.polygons,ti):f.material_index=i
 for f,i in zip(source.data.polygons,si):f.material_index=i
 bpy.ops.object.select_all(action='DESELECT');target.select_set(True);bpy.context.view_layer.objects.active=target
 # Retain chart boundaries, then rebake their texels from the reduced surface positions.
 # This repairs the collapse's UV distortion without repacking and resampling unaffected face charts.
 if target.name!='Body':
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.002);bpy.ops.object.mode_set(mode='OBJECT')
 source.select_set(True)
 projected=project(target,source,[r['tag']for r in rows],size)
 for channel in ['basecolor','metal_rough','region_mask','normal']:
  outputs=[]
  for i,row in enumerate(rows):
   high,low=row['high'],row['low'];nt=high.node_tree;bs=nt.nodes.get('Principled BSDF');out=nt.nodes.get('Material Output')
   if channel=='normal':nt.links.new(bs.outputs[0],out.inputs['Surface'])
   else:
    em=nt.nodes.new('ShaderNodeEmission')
    if channel=='basecolor':nt.links.new(bs.inputs['Base Color'].links[0].from_socket,em.inputs['Color'])
    else:
     name=f"{row['tag']}_{channel}{'_1k'if channel=='metal_rough'else''}.png";path=P/'textures'/name
     if path.exists():
      tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path),check_existing=True);tex.image.colorspace_settings.name='Non-Color';tex.image.alpha_mode='CHANNEL_PACKED';nt.links.new(tex.outputs['Color'],em.inputs['Color'])
     else:em.inputs['Color'].default_value=(0,0,0,1)
    nt.links.new(em.outputs[0],out.inputs['Surface'])
   image=bpy.data.images.new(f'{tag}_{i}_{channel}',width=size,height=size,alpha=False);image.colorspace_settings.name='sRGB'if channel=='basecolor'else'Non-Color'
   tex=low.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;low.node_tree.nodes.active=tex;outputs.append((row,image,tex))
  if channel=='normal':bpy.ops.object.bake(type='NORMAL',normal_space='TANGENT',use_selected_to_active=True,use_cage=False,cage_extrusion=.003,max_ray_distance=.012,margin=8,use_clear=True)
  else:
   for i,(_,image,_)in enumerate(outputs):image.pixels.foreach_set(projected[i][channel].ravel())
  for row,image,tex in outputs:
   path=folder/f"{tag}_{row['tag']}_{channel}.png";image.filepath_raw=str(path);image.file_format='PNG';image.save();image.pack();row['maps'][channel]=str(path.relative_to(P));nt=row['low'].node_tree;bs=nt.nodes.get('Principled BSDF')
   if channel=='basecolor':nt.links.new(tex.outputs['Color'],bs.inputs['Base Color']);nt.nodes.active=tex
   elif channel=='metal_rough':
    sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex.outputs['Color'],sep.inputs[0]);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
   elif channel=='normal':
    nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
  print('REBAKE',tag,channel,flush=True)
 # Workbench takes the active image node. Keep the base colour selected after the normal bake.
 for row in rows:
  mat=row['low'];bs=mat.node_tree.nodes.get('Principled BSDF');mat.node_tree.nodes.active=bs.inputs['Base Color'].links[0].from_node
 source.hide_render=True
 return [{'name':r['name'],'tag':r['tag'],'maps':r['maps']}for r in rows]
