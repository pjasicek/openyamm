"""Rebake selected far geometry, retain per-LOD maps, and export the shared source-frame rig."""
import bpy,sys,json,shutil,subprocess,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
import reduction_common as C,reduction_bake as B
OUT=P/'export';OUT.mkdir(exist_ok=True)
selected=json.loads((P/'review/reduction/selected.json').read_text());info={'lods':[],'clips':{}}
def bindmaps(o,folder):
 for i,m in enumerate(o.data.materials):
  for n in m.node_tree.nodes:
   if n.type!='TEX_IMAGE' or not n.image:continue
   key=next((k for k in ['basecolor','normal','metal_rough','region_mask']if n.image.name.endswith(k) or k in n.image.filepath),None)
   if key:
    path=folder/f'{i}_{key}.png'
    if path.exists():
     n.image=bpy.data.images.load(str(path),check_existing=False);n.image.colorspace_settings.name='sRGB'if key=='basecolor'else'Non-Color'
def ao(o,folder):
 r=bpy.data.objects['Rig'];C.reset()
 with bpy.data.libraries.load(str(P/'work/bake_source.blend'),link=False)as(src,dst):dst.objects=[o.name]
 high=dst.objects[0];bpy.context.collection.objects.link(high);high.parent=r
 for mod in high.modifiers:
  if mod.type=='ARMATURE':mod.object=r
 for i,m in enumerate(high.data.materials):
  m=m.copy();high.data.materials[i]=m;nt=m.node_tree;out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');a=nt.nodes.new('ShaderNodeAmbientOcclusion');a.inputs['Distance'].default_value=.04;a.samples=16;em=nt.nodes.new('ShaderNodeEmission');nt.links.new(a.outputs['AO'],em.inputs['Color']);nt.links.new(em.outputs[0],out.inputs['Surface'])
 images=[]
 for i,m in enumerate(o.data.materials):
  im=bpy.data.images.new(f'LOD AO {i}',width=1024,height=1024,alpha=False);im.colorspace_settings.name='Non-Color';n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=im;m.node_tree.nodes.active=n;images.append(im)
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=16;sc.render.threads=4;sc.render.threads_mode='FIXED';sc.render.bake.use_selected_to_active=True;sc.render.bake.cage_extrusion=.035;sc.render.bake.max_ray_distance=.08;sc.render.bake.margin=8
 bpy.ops.object.select_all(action='DESELECT');high.select_set(True);o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.bake(type='EMIT')
 for i,im in enumerate(images):im.filepath_raw=str(folder/f'{i}_ao.png');im.file_format='PNG';im.save()
 bpy.data.objects.remove(high,do_unlink=True)
for level in range(4):
 entry=selected[str(level)];bpy.ops.wm.open_mainfile(filepath=str(P/entry['blend']));C.cleanup();C.reset();r=bpy.data.objects['Rig'];sc=bpy.context.scene
 if level:
  for a in list(bpy.data.actions):bpy.data.actions.remove(a)
  with bpy.data.libraries.load(str(P/'work/final_lod0.blend'),link=False)as(src,dst):dst.actions=list(src.actions)
 for a in bpy.data.actions:a.use_fake_user=True
 tex=OUT/f'textures_lod{level}';shutil.copytree(P/entry['textures'],tex,dirs_exist_ok=True)
 meshes=[('Body','body'),('SpearMesh','spear'),('BucklerMesh','buckler')]
 for name,kind in meshes:
  o=bpy.data.objects[name];C.reset()
  if level>=2 and kind=='body':
   if level==3 and 'piece'in o.data.attributes:o.data.attributes['piece'].name='semantic_piece'
   B.bake(o,tex/kind)
   if 'semantic_piece'in o.data.attributes:o.data.attributes['semantic_piece'].name='piece'
  else:bindmaps(o,tex/kind)
  ao(o,tex/kind)
  for g in list(o.vertex_groups):
   if g.name not in r.data.bones:o.vertex_groups.remove(g)
  for v in o.data.vertices:
   w=sorted([(g.group,g.weight)for g in v.groups if g.weight>0],key=lambda x:-x[1])[:8];total=sum(x[1]for x in w);assert total>0
   for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
   for gi,weight in w:o.vertex_groups[gi].add([v.index],weight/total,'REPLACE')
  for m in o.data.materials:
   bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['IOR'].default_value=1.5;bs.inputs['Specular IOR Level'].default_value=.5;bs.inputs['Specular Tint'].default_value=(1,1,1,1)
  if kind=='body':
   (OUT/f'lod{level}_semantics.json').write_text(json.dumps({'positions':[v.co[:]for v in o.data.vertices],'pieces':[x.value for x in o.data.attributes['piece'].data]}))
 # Downsample each map independently, normalize tangent normals, and preserve a conventional AO/roughness/metal receipt.
 subprocess.run(['/usr/bin/python3','-B',str(P/'scripts/finish_lod_maps.py'),str(tex),str([1024,512,256,512][level])],check=True)
 for name,kind in meshes:bindmaps(bpy.data.objects[name],tex/kind)
 if level==3:
  for m in bpy.data.objects['Body'].data.materials:
   nt=m.node_tree;bs=nt.nodes.get('Principled BSDF');base=bs.inputs['Base Color'].links[0].from_node;cut=nt.nodes.new('ShaderNodeMath');cut.operation='GREATER_THAN';cut.inputs[1].default_value=.5;nt.links.new(base.outputs['Alpha'],cut.inputs[0]);nt.links.new(cut.outputs[0],bs.inputs['Alpha']);m.surface_render_method='DITHERED'

 subprocess.run(['/usr/bin/python3','-B',str(P/'scripts/tier_previews.py'),str(tex)],check=True)
 C.reset();sc.render.fps=48;sc.render.fps_base=1
 for im in bpy.data.images:
  if im.source=='FILE'and im.has_data:im.pack()
 dest=P/f'work/runtime_lod{level}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest))
 row={'level':level,'blend':str(dest.relative_to(P)),'textures':str(tex.relative_to(P)),'triangles':{name:C.triangles(bpy.data.objects[name])for name,_ in meshes}};info['lods'].append(row)
 if level==0:
  bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'mm6_natm.blend'));cal=json.loads((P/'review/calibration.json').read_text())
  for a in bpy.data.actions:
   r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];end=float(a.frame_range[1]);lo=np.full(3,1e6);hi=-lo.copy();samples=[]
   for f in range(round(end)+1):
    sc.frame_set(f);coords=[]
    for name,_ in meshes:
     ob=bpy.data.objects[name];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();coords.extend(v.co[:]for v in mm.vertices);ev.to_mesh_clear()
    vv=np.array(coords);lo=np.minimum(lo,vv.min(0));hi=np.maximum(hi,vv.max(0))
    M=r.pose.bones['Spear'].matrix;tip=M@Vector((0,0,cal['spear_tip_m']));palm=r.pose.bones['Socket_LeftPalm'].matrix.translation;samples.append({'time':f/48,'tip':tip[:],'grip':M.translation[:],'palm':palm[:]})
   info['clips'][a.name]={'duration':end/48,'mode':'loop'if a.name in ['Standing','Walking','Running','Dead']else'once','bounds':lo.tolist()+hi.tolist()}
   if a.name in ['Attack','Cast']:(P/f'review/{a.name.lower()}_final_samples.json').write_text(json.dumps(samples,indent=2))
  info['bones']=len(r.data.bones);C.reset()
 # Keep the source editable with separate pieces; the raw export is one skinned mesh for the existing splitter.
 bpy.ops.object.select_all(action='DESELECT')
 for name,_ in meshes:bpy.data.objects[name].select_set(True)
 body=bpy.data.objects['Body'];bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name=body.data.name='Natm'
 for o in bpy.data.objects:o.select_set(o in [r,body])
 bpy.context.view_layer.objects.active=r;C.reset()
 bpy.ops.export_scene.gltf(filepath=str(OUT/f'mm6_natm_raw_lod{level}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=level==0,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=False)
 print('EXPORTED',row,flush=True)
(OUT/'export_info.json').write_text(json.dumps(info,indent=2))
