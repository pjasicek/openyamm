import bpy,json
from pathlib import Path
from mathutils import Quaternion
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;names=[b.name for b in r.pose.bones if b.name.startswith('B_R_Finger')]
def action(n):a=bpy.data.actions[n];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
action('Standing');sc.frame_set(0);relax={n:Quaternion().slerp(r.pose.bones[n].rotation_quaternion,.25)for n in names}
action('Attack');sc.frame_set(30);hook={n:Quaternion().slerp(r.pose.bones[n].rotation_quaternion,.65)for n in names}
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
for a in bpy.data.actions:
 action(a.name)
 for f in range(int(a.frame_range[1])+1):
  w=smooth((f-5)/19)*smooth((49-f)/13)if a.name=='Attack'else 0.
  for n in names:
   b=r.pose.bones[n];b.rotation_quaternion=relax[n].slerp(hook[n],w);b.keyframe_insert('rotation_quaternion',frame=f)
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
(P/'work/finger_motion.json').write_text(json.dumps({'right_relaxed_fraction':.25,'right_draw_hook_fraction':.65,'draw_blend_frames':[5,24],'release_blend_frames':[36,49],'left_grip_unchanged':True},indent=2))
