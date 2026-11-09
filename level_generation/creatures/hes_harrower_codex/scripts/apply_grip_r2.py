"""Apply solved finger channels and align the existing blade plane to the new hand-local grip frame."""
from pathlib import Path
import bpy,json,sys,numpy as np
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/review_v1/final.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
correction={};report={}
for side in 'LR':
 old=json.loads((P/f'work/review_v1/grip_pose_{side}.json').read_text());new=json.loads((P/f'work/grip_pose_r2_{side}.json').read_text())
 z=Vector(old['handle_axis_hand_local']);x=Vector(old['blade_out_hand_local']);O=Matrix((x,z.cross(x),z)).transposed()
 z=Vector(new['handle_axis_hand_local']);x=(x-z*x.dot(z)).normalized();N=Matrix((x,z.cross(x),z)).transposed();Q=O@N.transposed();correction[side]=Q.to_quaternion()
 new['blade_out_hand_local']=list(x);new['blade_front_hand_local']=list(z.cross(x));(P/f'work/grip_pose_r2_{side}.json').write_text(json.dumps(new,indent=2)+'\n')
 report[side]={'rotation_degrees':float(np.degrees(Q.to_quaternion().angle))}
for action in [a for a in bpy.data.actions if a.name.startswith('Harrower_')]:
 rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];keys={};stats={s:{'swing':0,'twist':0} for s in 'LR'}
 for frame in range(int(action.frame_range[1])+1):
  sc.frame_set(frame)
  for side in 'LR':
   hand=rig.pose.bones[f'B_{side}_Hand'];q=hand.rotation_quaternion@correction[side];keys[frame,side]=q.copy();hand.rotation_quaternion=q
   bpy.context.view_layer.update();swing,twist=armik.wrist_cost(rig,side,hand.matrix.to_3x3());stats[side]['swing']=max(stats[side]['swing'],swing);stats[side]['twist']=max(stats[side]['twist'],abs(twist))
 for (frame,side),q in keys.items():
  hand=rig.pose.bones[f'B_{side}_Hand'];hand.rotation_quaternion=q;hand.keyframe_insert('rotation_quaternion',frame=frame)
  new=json.loads((P/f'work/grip_pose_r2_{side}.json').read_text())
  for name,quat in new['finger_local'].items():
   pb=rig.pose.bones[name];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion(quat);pb.keyframe_insert('rotation_quaternion',frame=frame)
 report[action.name]=stats;print('WRIST_R2',action.name,stats,flush=True)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/gripped_r2.blend'));(P/'review/r2/wrists.json').write_text(json.dumps(report,indent=2)+'\n')
