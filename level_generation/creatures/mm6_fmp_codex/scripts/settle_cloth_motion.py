"""Use stable fall poses for the covered legs and skirt; remove the simulator's one-frame roll reversals."""
import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
r=bpy.data.objects['Rig'];s=bpy.context.scene;a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
names=[b.name for b in r.pose.bones if b.name.startswith('Skirt_') or b.name.startswith(('B_L_Thigh','B_R_Thigh','B_L_Calf','B_R_Calf','B_L_Foot','B_R_Foot','B_L_Toe','B_R_Toe'))]
frames=[0,24,48,72,96,120];poses=[]
for f in frames:
 s.frame_set(f);poses.append({n:(r.pose.bones[n].rotation_quaternion.copy().normalized(),r.pose.bones[n].location.copy()) for n in names})
for i in range(1,len(poses)):
 for n in names:
  if poses[i][n][0].dot(poses[i-1][n][0])<0:poses[i][n][0].negate()
for f in range(121):
 i=min(f//24,len(frames)-2);t=(f-frames[i])/24
 for n in names:
  b=r.pose.bones[n];b.rotation_quaternion=poses[i][n][0].slerp(poses[i+1][n][0],t);b.location=poses[i][n][1].lerp(poses[i+1][n][1],t);b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
for l in a.layers:
 for st in l.strips:
  for bag in st.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
(P/'work/death_motion_cleanup.json').write_text(json.dumps({'anchors_frames':frames,'bones':names,'reason':'Remove unstable roll reversals in cloth simulation and covered legs, retaining fall and floor silhouette'},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_uv.blend'))
