"""Rebake each reduced material from the unreduced rig in its neutral pose."""
import bpy,bmesh,json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
def material_part(ob,index,name):
 part=ob.copy();part.data=ob.data.copy();part.name=name;bpy.context.collection.objects.link(part)
 bm=bmesh.new();bm.from_mesh(part.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=index],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(part.data);bm.free()
 old=ob.data.materials[index];part.data.materials.clear();part.data.materials.append(old.copy())
 for f in part.data.polygons:f.material_index=0
 return part
def bake(path,tag,level):
 bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update();low=bpy.data.objects['Body'];high=bpy.data.objects['BakeSource'];high.hide_viewport=False
 sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.render.threads_mode='FIXED';sc.render.threads=4
 sc.render.bake.use_selected_to_active=True;sc.render.bake.cage_extrusion=.001;sc.render.bake.max_ray_distance=.004;sc.render.bake.margin=16;sc.render.bake.margin_type='EXTEND';sc.render.bake.use_clear=True
 sc.render.bake.normal_space='TANGENT';sc.render.bake.use_pass_direct=False;sc.render.bake.use_pass_indirect=False;sc.render.bake.use_pass_color=True
 sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
 for o in bpy.data.objects:
  if o.type=='MESH':o.hide_render=True
 config=json.loads((P/'textures/lzd_ramps.json').read_text());report={};parts=[]
 for idx in sorted({f.material_index for f in low.data.polygons}):
  mat=low.data.materials[idx]
  key=mat.name.split('.')[0];group={'Lizard_A':'body','LizardHead_A':'head','LizardBow_A':'bow'}[key]
  lo=material_part(low,idx,'Low_'+group);hi=material_part(high,idx,'High_'+group)
  for m in list(hi.modifiers):hi.modifiers.remove(m)
  # Both objects are in the same neutral pose; modifiers remain on the runtime mesh.
  for m in lo.modifiers:m.show_render=False
  lo.hide_viewport=False;hi.hide_viewport=False;lo.hide_render=False;hi.hide_render=False
  bpy.ops.object.select_all(action='DESELECT');lo.select_set(True);bpy.context.view_layer.objects.active=lo
  if group=='head':
   bm=bmesh.new();bm.from_mesh(lo.data)
   for e in bm.edges:e.seam=len(e.link_faces)==2 and (e.link_faces[0].calc_center_median().x<0)!=(e.link_faces[1].calc_center_median().x<0)
   bm.to_mesh(lo.data);bm.free()
   bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.unwrap(method='ANGLE_BASED',margin=0);bpy.ops.object.mode_set(mode='OBJECT')
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.select_all(action='SELECT');bpy.ops.uv.pack_islands(udim_source='ACTIVE_UDIM',rotate=False,scale=True,margin_method='FRACTION',margin=16/(2048 if group=='body'else 1024));bpy.ops.object.mode_set(mode='OBJECT')
  assert all(-1e-5<=c<=1.00001 for uv in lo.data.uv_layers.active.data for c in uv.uv),group
  # Separate overlapping armour/skin shells for rays, without changing their normals or UVs.
  for ob in [lo,hi]:
   pieces=[v.value for v in ob.data.attributes['piece'].data]
   for v in ob.data.vertices:v.co.x+=pieces[v.index]*3 if level<2 else 0
   ob.data.update()
  sm=hi.data.materials[0];nt=sm.node_tree;bs=nt.nodes.get('Principled BSDF');out=nt.nodes.get('Material Output')
  for n in nt.nodes:
   if n.type=='TEX_IMAGE' and n.image and 'normal'in n.image.name:n.image=bpy.data.images.load(str(P/json.loads((P/'review/rebake/final0_bake.json').read_text())[group]['paths']['normal']),check_existing=True);n.image.colorspace_settings.name='Non-Color'
  images={n.image.name:n.image for n in nt.nodes if n.type=='TEX_IMAGE' and n.image}
  base=bs.inputs['Base Color'].links[0].from_node.image
  normal=next(n.image for n in nt.nodes if n.type=='TEX_IMAGE' and n.image and 'normal' in n.image.name)
  mr=next(n.image for n in nt.nodes if n.type=='TEX_IMAGE' and n.image and 'metal_rough' in n.image.name)
  entry=next(e for e in config['materials']if e['base']==key)
  mask=bpy.data.images.load(str(P/json.loads((P/'review/rebake/final0_bake.json').read_text())[group]['paths']['regions']),check_existing=True);mask.colorspace_settings.name='Non-Color'
  lm=bpy.data.materials.new(key+(''if level==0 else f'_LOD{level}'));lm.use_nodes=True;lo.data.materials.clear();lo.data.materials.append(lm);ln=lm.node_tree
  target=ln.nodes.new('ShaderNodeTexImage');ln.nodes.active=target;size=([2048,1024,512,256]if group=='body'else[1024,512,256,128])[level];dest=P/f'textures/rebake/{tag}/{group}';dest.mkdir(parents=True,exist_ok=True);baked={}
  tex=nt.nodes.new('ShaderNodeTexImage');em=nt.nodes.new('ShaderNodeEmission');nt.links.new(tex.outputs['Color'],em.inputs['Color'])
  for channel,kind,img in [('basecolor','EMIT',base),('normal','NORMAL',normal),('metal_rough','EMIT',mr),('regions','EMIT',mask)]:
   if kind=='EMIT':tex.image=img;nt.links.new(em.outputs[0],out.inputs['Surface'])
   else:nt.links.new(bs.outputs[0],out.inputs['Surface'])
   image=bpy.data.images.new(f'{tag}_{group}_{channel}',width=size,height=size,alpha=False);image.colorspace_settings.name='sRGB'if channel=='basecolor'else'Non-Color';target.image=image;ln.nodes.active=target
   bpy.ops.object.select_all(action='DESELECT');hi.select_set(True);lo.select_set(True);bpy.context.view_layer.objects.active=lo
   bpy.ops.object.bake(type=kind)
   image.filepath_raw=str(dest/f'{channel}.png');image.file_format='PNG';image.save();baked[channel]=image
  nt.links.new(bs.outputs[0],out.inputs['Surface']);ln.nodes.remove(target);lbs=ln.nodes.get('Principled BSDF');lbs.inputs['Specular IOR Level'].default_value=.5;lbs.inputs['Specular Tint'].default_value=(1,1,1,1);lbs.inputs['IOR'].default_value=1.5
  for channel in ['basecolor','normal','metal_rough']:
   node=ln.nodes.new('ShaderNodeTexImage');node.image=baked[channel]
   if channel=='basecolor':ln.links.new(node.outputs['Color'],lbs.inputs['Base Color'])
   elif channel=='normal':
    n=ln.nodes.new('ShaderNodeNormalMap');ln.links.new(node.outputs['Color'],n.inputs['Color']);ln.links.new(n.outputs['Normal'],lbs.inputs['Normal'])
   else:
    n=ln.nodes.new('ShaderNodeSeparateColor');ln.links.new(node.outputs['Color'],n.inputs['Color']);ln.links.new(n.outputs['Green'],lbs.inputs['Roughness']);ln.links.new(n.outputs['Blue'],lbs.inputs['Metallic'])
  pieces=[v.value for v in lo.data.attributes['piece'].data]
  for v in lo.data.vertices:v.co.x-=pieces[v.index]*3 if level<2 else 0
  lo.data.update()
  for m in lo.modifiers:m.show_render=True
  lo.hide_render=False;parts.append(lo);bpy.data.objects.remove(hi,do_unlink=True)
  report[group]={'material':lm.name,'base_material':key,'size':size,'paths':{c:str(dest.relative_to(P)/f'{c}.png')for c in baked},'triangles':sum(len(f.vertices)-2 for f in lo.data.polygons)}
 bpy.data.objects.remove(low,do_unlink=True);high.hide_viewport=True;high.hide_render=True;bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();lo=parts[0];lo.name='Body'
 path=P/f'work/round4/{tag}_baked.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));(P/f'review/rebake/{tag}_bake.json').write_text(json.dumps(report,indent=2));print('BAKED',tag,report,flush=True);return path

bpy.ops.wm.open_mainfile(filepath=str(P/'work/round4/repaired.blend'))
r=bpy.data.objects['Rig'];r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
for old in list(bpy.data.objects):
 if old.name.startswith('BakeSource'):bpy.data.objects.remove(old,do_unlink=True)
ob=bpy.data.objects['Body'];high=ob.copy();high.data=ob.data.copy();high.name='BakeSource';bpy.context.collection.objects.link(high);high.hide_render=True
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
m=ob.modifiers.new('Coplanar cleanup','DECIMATE');m.decimate_type='DISSOLVE';m.angle_limit=.0035;m.delimit={'MATERIAL','UV','SEAM'};bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round4/near_unbaked.blend'))
bake(P/'work/round4/near_unbaked.blend','round4_shared',0)
