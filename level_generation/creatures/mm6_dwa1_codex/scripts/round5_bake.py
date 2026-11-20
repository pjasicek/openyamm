"""Re-unwrap the reduced surface and bake accepted colour, regions, ORM and detailed tangent normals."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
import round4_search as S
W=P/'work/round5';R=P/'review/round5';config=json.loads((W/'config.json').read_text());step=config.get('step',6);dest=W/f'baked{step}';dest.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(W/f'step{step}.blend'));S.cleanup();S.reset();rig=bpy.data.objects['Rig'];rig.data.pose_position='REST'
low=[bpy.data.objects['Body'],bpy.data.objects['Axe']]
for ob in low:
 for mod in ob.modifiers:mod.show_render=False;mod.show_viewport=False
 # New UVs remove collapsed-chart distortion; material sets retain separate 1K allocations.
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 for slot in sorted(set(f.material_index for f in ob.data.polygons)):
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
  for f in ob.data.polygons:f.select=f.material_index==slot
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.008,area_weight=.2,correct_aspect=True,scale_to_bounds=True);bpy.ops.object.mode_set(mode='OBJECT')
 # Sources and target materials must not share bake-target nodes.
 for slot in ob.material_slots:
  if slot.material:slot.material=slot.material.copy()
with bpy.data.libraries.load(str(P/'work/round4_before/work/export_reimport.blend'),link=False)as(src,dst):dst.objects=['Body','Axe']
high=dst.objects
for ob in high:
 bpy.context.scene.collection.objects.link(ob);ob.parent=None
 for mod in list(ob.modifiers):ob.modifiers.remove(mod)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1;scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.018;scene.render.bake.max_ray_distance=.04;scene.render.bake.margin=8;scene.render.bake.use_clear=True
maps=np.load(W/'source_maps.npz');images={}
for key,arr in maps.items():
 im=bpy.data.images.new(key,width=arr.shape[1],height=arr.shape[0],alpha=True,float_buffer=False);im.colorspace_settings.name='sRGB'if key.endswith('_base')else'Non-Color'
 rgba=np.ones((*arr.shape[:2],4),np.float32);rgba[:,:,:arr.shape[-1]]=arr;im.pixels.foreach_set(rgba[::-1].ravel());im.update();images[key]=im
# Match the accepted file's normal maps, already in glTF +Y convention, with Blender tangent space.
records={}
for target,source in zip(low,high):
 slots=sorted(set(f.material_index for f in target.data.polygons));outputs={}
 for mode in ['base','mask','orm','normal']:
  for mat in source.data.materials:
   if not mat:continue
   name=mat.name.split('.')[0];nodes=mat.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');tex=nodes.new('ShaderNodeTexImage');tex.image=images[name+'_'+('normal'if mode=='normal'else mode)]
   if mode=='normal':
    bs=nodes.new('ShaderNodeBsdfPrincipled');nm=nodes.new('ShaderNodeNormalMap');mat.node_tree.links.new(tex.outputs['Color'],nm.inputs['Color']);mat.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal']);mat.node_tree.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
   else:
    em=nodes.new('ShaderNodeEmission');mat.node_tree.links.new(tex.outputs['Color'],em.inputs['Color']);mat.node_tree.links.new(em.outputs['Emission'],out.inputs['Surface'])
  for slot in slots:
   mat=target.data.materials[slot];name=mat.name.split('.')[0];im=bpy.data.images.new(f'{name}_{mode}_rebake',width=1024,height=1024,alpha=False);im.colorspace_settings.name='sRGB'if mode=='base'else'Non-Color';node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;mat.node_tree.nodes.active=node;outputs[name,mode]=im
  bpy.ops.object.select_all(action='DESELECT');target.select_set(True);source.select_set(True);bpy.context.view_layer.objects.active=target
  bpy.ops.object.bake(type='NORMAL'if mode=='normal'else'EMIT',normal_space='TANGENT')
  for slot in slots:
   name=target.data.materials[slot].name.split('.')[0];im=outputs[name,mode];im.filepath_raw=str(dest/f'{name}_{mode}.png');im.file_format='PNG';im.save()
  print('REBAKED',step,target.name,mode,flush=True)
 for slot in slots:
  mat=target.data.materials[slot];name=mat.name.split('.')[0];nodes=mat.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');bs=nodes.new('ShaderNodeBsdfPrincipled');bs.inputs['Metallic'].default_value=0;mat.node_tree.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
  for mode in ['base','orm','normal']:
   tex=nodes.new('ShaderNodeTexImage');tex.image=outputs[name,mode]
   if mode=='base':mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);nodes.active=tex
   elif mode=='orm':
    sep=nodes.new('ShaderNodeSeparateColor');mat.node_tree.links.new(tex.outputs['Color'],sep.inputs['Color']);mat.node_tree.links.new(sep.outputs['Green'],bs.inputs['Roughness'])
   else:
    nm=nodes.new('ShaderNodeNormalMap');mat.node_tree.links.new(tex.outputs['Color'],nm.inputs['Color']);mat.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
 for mod in target.modifiers:mod.show_render=True;mod.show_viewport=True
 records[target.name]={'triangles':S.triangles(target),'sets':[target.data.materials[s].name.split('.')[0]for s in slots]}
for ob in high:bpy.data.objects.remove(ob,do_unlink=True)
for ob in list(bpy.data.objects):
 if ob.type=='ARMATURE'and ob!=rig:bpy.data.objects.remove(ob,do_unlink=True)
rig.data.pose_position='POSE';S.reset();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(dest/'candidate.blend'));(dest/'receipt.json').write_text(json.dumps({'source':'work/round4_before/work/export_reimport.blend','target_step':step,'sets_1k':True,'maps':['base','mask','orm','normal'],'method':'Cycles selected-to-active, new per-material Smart UV layouts; high-surface normal plus existing glTF tangent detail','objects':records},indent=2)+'\n')
