"""Export the measured meshes with the same fitted skeleton and eight clips."""
import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROLES=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
selection=json.loads((P/'review/reduction_soft/selection.json').read_text());reports={}
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/selection[str(level)]['blend']));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];knife=bpy.data.objects['KnifeAsset'];scene=bpy.context.scene;scene.render.fps=30;scene.render.fps_base=1
 for ob in list(bpy.data.objects):
  if ob not in [rig,body,knife]:bpy.data.objects.remove(ob,do_unlink=True)
 for act in list(bpy.data.actions):
  if act.name not in ROLES:bpy.data.actions.remove(act)
  else:act.use_fake_user=True
 assert {a.name for a in bpy.data.actions}==set(ROLES)
 suffix=''if level==0 else f'_LOD{level}'
 for ob,prefixes in [(body,['PeasantF3','PeasantF3Head']),(knife,['Knife'])]:
  group=ob.vertex_groups.get('_reduction_protect')
  if group:ob.vertex_groups.remove(group)
  for mi,prefix in enumerate(prefixes):
   mat=ob.data.materials[mi];target=prefix+suffix+'_A';old=bpy.data.materials.get(target)
   if old is not None and old!=mat:old.name='Unused_'+target
   mat.name=target;assert mat.name==target
   # Saved Blender checkpoints may contain packed images; the selected canonical maps are authoritative.
   stem='knife'if ob==knife else ['mfp','mfp_head'][mi]
   for node in mat.node_tree.nodes:
    if node.type!='TEX_IMAGE'or not node.image:continue
    image_name=node.image.name.lower();kind='normal'if 'normal'in image_name else'metal_rough'if 'metal_rough'in image_name else'basecolor';node.image=bpy.data.images.load(str(Path(selection[str(level)]['textures'])/f'{stem}_{kind}.png'),check_existing=False);node.image.colorspace_settings.name='sRGB'if kind=='basecolor'else'Non-Color'
   bs=mat.node_tree.nodes.get('Principled BSDF')
   for key,value in [('IOR',1.5),('Specular IOR Level',.5),('Coat Weight',0),('Sheen Weight',0),('Transmission Weight',0)]:
    if key in bs.inputs and not bs.inputs[key].is_linked:bs.inputs[key].default_value=value
  for layer in list(ob.data.uv_layers):
   if layer.name!='UVMap':ob.data.uv_layers.remove(layer)
  ob.data.uv_layers.active=ob.data.uv_layers['UVMap']
 rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];scene.frame_set(0)
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([v.co[:]for v in me.vertices]);ev.to_mesh_clear()
 info={'standing_bounds_m':[co.min(0).tolist(),co.max(0).tolist()],'standing_height_m':float(np.ptp(co[:,2])),'body_triangles':sum(len(f.vertices)-2 for f in body.data.polygons),'knife_triangles':sum(len(f.vertices)-2 for f in knife.data.polygons),'joints':len(rig.data.bones),'durations':{a.name:float(a.frame_range[1]-a.frame_range[0])/30 for a in bpy.data.actions}}
 if level==0:
  bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_mfp.blend'))
 # 240 Hz keeps the fitted 48 Hz cloth bends through the forced glTF sampler.
 for act in bpy.data.actions:
  end=act.frame_range[1]*8;start=act.frame_range[0]*8
  for layer in act.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for key in fc.keyframe_points:
       for coord in [key.co,key.handle_left,key.handle_right]:coord.x*=8
  act.frame_start=start;act.frame_end=end
 scene.render.fps=240
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');body.select_set(True);knife.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name=body.data.name='PeasantF3'
 for attr in list(body.data.attributes):
  if attr.name in ['piece','head','finger','orig_co']:body.data.attributes.remove(attr)
 bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.gltf(filepath=str(P/f'export/mm6_mfp_level{level}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=level==0,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_tangents=True,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
 reports[str(level)]=info;print('EXPORT_LEVEL',level,info,flush=True)
(P/'export/export_info.json').write_text(json.dumps(reports,indent=2))
