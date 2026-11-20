"""Export the animation of work/gait2.blend (Walking for the parity check, Walk2, Run2) the way export_runtime.py
does (keys doubled to 60 fps, forced sampling) to work/gait2/anim.glb, for gait2_graft.py."""
import bpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/gait2.blend'))
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene
keep=['Walking','Walk2','Run2']
for a in list(bpy.data.actions):
 if a.name not in keep:bpy.data.actions.remove(a)
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
for a in bpy.data.actions:
 start,end=map(float,a.frame_range)
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for key in fc.keyframe_points:key.co.x*=2;key.handle_left.x*=2;key.handle_right.x*=2
     fc.update()
 a.frame_start=start*2;a.frame_end=end*2
sc.render.fps=60;sc.render.fps_base=1
r.animation_data.action=bpy.data.actions['Walking'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0)
for obj in bpy.data.objects:obj.select_set(obj in [r,b])
bpy.context.view_layer.objects.active=r
bpy.ops.export_scene.gltf(filepath=str(p/'work/gait2/anim.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_materials='NONE',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
print('GAIT2_EXPORTED')
