import bpy,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction_master.blend'));C.cleanup();C.reset();r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];c=bpy.data.objects['ClubMesh']
for o in bpy.data.objects:o.select_set(o in [b,c])
bpy.context.view_layer.objects.active=b;bpy.ops.object.join();b.name='Merchant'
for a in bpy.data.actions:
 for lay in a.layers:
  for st in lay.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.co.x*=4;k.handle_left.x*=4;k.handle_right.x*=4
     fc.update()
 if a.use_frame_range:
  start,end=a.frame_start,a.frame_end;a.frame_end=end*4;a.frame_start=start*4
bpy.context.scene.render.fps=120
r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];bpy.context.scene.frame_set(0)
for o in bpy.data.objects:o.select_set(o in [r,b])
bpy.context.view_layer.objects.active=r
bpy.ops.export_scene.gltf(filepath=str(P/'work/master_trace.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_extras=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
runpy.run_path(str(P/'scripts/trace_sources.py'),run_name='__main__')
