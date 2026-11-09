import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Quaternion,Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;scene.render.fps=30;report={}
roles=['Standing','Walking','Running','Attack','Hit','Death','Fidget']
for name in roles:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];end=int(a.frame_range[1]);poses=[]
 for f in range(end+1):
  scene.frame_set(f);poses.append({pb.name:(pb.rotation_quaternion.copy(),pb.location.copy())for pb in rig.pose.bones})
 # Hands are unencumbered on the left: retain a relaxed 45% of the source curl.
 for f,pose in enumerate(poses):
  for n in pose:
   if n.startswith('B_L_Finger'):pose[n]=(Quaternion().slerp(pose[n][0],.45),pose[n][1])
 # Root lift from the actual soles/corpse surface over a half-frame neighbourhood.
 floors=[]
 for f in np.arange(0,end+.0001,.25):
  scene.frame_set(int(f),subframe=float(f-int(f)));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();floors.append(min((body.matrix_world@v.co).z for v in m.vertices));ev.to_mesh_clear()
 required=np.maximum(0,-np.array(floors))+.0015;lifts=np.array([float(required[max(0,f*4-2):min(len(required),f*4+3)].max())for f in range(end+1)])
 new=bpy.data.actions.new(name+'_final');new.use_fake_user=True;prev={};rig.animation_data.action=None
 for f,pose in enumerate(poses):
  rig.animation_data.action=None
  for n,(q,l)in pose.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].location=l
  bpy.context.view_layer.update();pb=rig.pose.bones['B_Pelvis'];M=pb.matrix.copy();M.translation.z+=lifts[f];pb.matrix=M;bpy.context.view_layer.update();rig.animation_data.action=new
  if len(new.slots):rig.animation_data.action_slot=new.slots[0]
  for pb in rig.pose.bones:
   q=pb.rotation_quaternion.copy()
   if pb.name in prev and q.dot(prev[pb.name])<0:q=-q
   prev[pb.name]=q;pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
   if pb.name=='B_Pelvis':pb.keyframe_insert('location',frame=f)
 new.use_frame_range=True;new.frame_start=0;new.frame_end=end;rig.animation_data.action=None;bpy.data.actions.remove(a);new.name=name
 for lay in new.layers:
  for strip in lay.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 report[name]={'root_lift_min_max_m':[float(lifts.min()),float(lifts.max())],'source_floor_min_max_m':[min(floors),max(floors)],'left_finger_curl_share':.45}
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'));(P/'review/floor_correction.json').write_text(json.dumps(report,indent=2));print('FLOOR CORRECTED',report)
