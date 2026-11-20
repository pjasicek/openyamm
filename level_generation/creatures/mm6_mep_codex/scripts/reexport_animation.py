import bpy,subprocess,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'export/mm6_mep.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Mep'];sc=bpy.context.scene
for a in bpy.data.actions:
 start,end=map(float,a.frame_range)
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for key in fc.keyframe_points:key.co.x*=8;key.handle_left.x*=8;key.handle_right.x*=8
     fc.update()
 a.frame_start=start*8;a.frame_end=end*8
sc.render.fps=240;r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();b.data.uv_layers.active=b.data.uv_layers['MergedUV'];b.data.uv_layers['MergedUV'].active_render=True
for uv in list(b.data.uv_layers):
 if uv.name!='MergedUV':b.data.uv_layers.remove(uv)
b.data.uv_layers.active.name='UVMap'
for o in bpy.data.objects:o.select_set(o in [r,b])
bpy.context.view_layer.objects.active=r
bpy.ops.export_scene.gltf(filepath=str(p/'export/mm6_mep_raw_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
subprocess.run(['/usr/bin/python3',str(p.parents[2]/'tools/prepare_actor_glb.py'),str(p/'export/mm6_mep_raw_lod0.glb'),str(p/'export/mm6_mep_runtime_lod0.glb')],check=True)
runpy.run_path(str(p/'scripts/export_trace_final.py'),run_name='__main__')
