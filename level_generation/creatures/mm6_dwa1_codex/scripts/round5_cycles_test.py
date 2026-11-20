"""Re-unwrap the reduced surface and bake accepted colour, regions, ORM and detailed tangent normals."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
import round4_search as S
W=P/'work/round5';R=P/'review/round5';config=json.loads((W/'config.json').read_text());step=config.get('step',6);dest=W/f'cycles{step}';dest.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(W/f'baked{step}/candidate.blend'));S.cleanup();S.reset();rig=bpy.data.objects['Rig'];rig.data.pose_position='REST'
low=[bpy.data.objects['Body'],bpy.data.objects['Axe']]
for ob in low:
 for mod in ob.modifiers:mod.show_render=False;mod.show_viewport=False
 # Sources and target materials must not share bake-target nodes.
 for slot in ob.material_slots:
  if slot.material:slot.material=slot.material.copy()
with bpy.data.libraries.load(str(P/'work/round4_before/work/export_reimport.blend'),link=False)as(src,dst):dst.objects=['Body','Axe']
high=dst.objects
for ob in high:
 bpy.context.scene.collection.objects.link(ob);ob.parent=None
 for mod in list(ob.modifiers):ob.modifiers.remove(mod)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1;scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.006;scene.render.bake.max_ray_distance=.03;scene.render.bake.margin=8;scene.render.bake.use_clear=True
images={}
for path in (W/'source').glob('*.png'):
 if path.stem.endswith(('_base','_orm','_normal','_mask')):
  im=bpy.data.images.load(str(path));im.colorspace_settings.name='sRGB'if path.stem.endswith('_base')else'Non-Color';images[path.stem]=im
# Match the accepted file's normal maps, already in glTF +Y convention, with Blender tangent space.
records={}
for target,source in zip(low,high):
 slots=list(range(len(target.data.materials)));outputs={}
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
   name=target.data.materials[slot].name.split('.')[0];im=outputs[name,mode];
   if slot in {f.material_index for f in target.data.polygons}:im.filepath_raw=str(dest/f'{name}_{mode}.png');im.file_format='PNG';im.save()
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
