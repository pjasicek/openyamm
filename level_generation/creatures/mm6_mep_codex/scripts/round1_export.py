import bpy,json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];info=json.loads((P/'export/export_info.json').read_text())
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/final_lod{level}.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];b.name=b.data.name='Mep';sc=bpy.context.scene
 if level==0:
  for a in bpy.data.actions:
   start,end=map(float,a.frame_range);info['clips'][a.name]['duration']=(end-start)/30
   for layer in a.layers:
    for strip in layer.strips:
     for bag in strip.channelbags:
      for fc in bag.fcurves:
       for key in fc.keyframe_points:key.co.x*=8;key.handle_left.x*=8;key.handle_right.x*=8
       fc.update()
   a.frame_start=start*8;a.frame_end=end*8
  sc.render.fps=240
 r.animation_data.action=None
 for pb in r.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();b.data.uv_layers.active=b.data.uv_layers['MergedUV'];b.data.uv_layers['MergedUV'].active_render=True
 for uv in list(b.data.uv_layers):
  if uv.name!='MergedUV':b.data.uv_layers.remove(uv)
 b.data.uv_layers.active.name='UVMap'
 for o in bpy.data.objects:o.select_set(o in [r,b])
 bpy.context.view_layer.objects.active=r
 bpy.ops.export_scene.gltf(filepath=str(P/f'export/mm6_mep_raw_lod{level}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=level==0,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
info['clips']['Attack']['impact']=.84375;info['clips']['Cast']['impact']=info['clips']['Attack']['impact']
info['review_revision']='mm6_mep_codex_review_round2';info['measurement_source']='review/gates/gates.json'
(P/'export/export_info.json').write_text(json.dumps(info,indent=2))
