"""Put the right elbow bend in its anatomical hinge plane without moving hand or elbow targets."""
import bpy,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/master.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene
changed=['B_R_UpperArm','B_R_Forearm','B_R_Hand','B_R_UpperArmTwist','B_R_ForearmTwist'];report={}
def align(name,axis,normal):
 pb=rig.pose.bones[name];old=-pb.matrix.to_3x3().col[2].normalized();old=(old-axis*old.dot(axis)).normalized();angle=math.atan2(axis.dot(old.cross(normal)),old.dot(normal));q=Quaternion(axis,angle);m=q.to_matrix().to_4x4()@pb.matrix;m.translation=pb.head;pb.matrix=m;bpy.context.view_layer.update();return math.degrees(angle)
for act in list(bpy.data.actions):
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];samples=[];changes=[];hand_error=0
 for f in range(int(act.frame_range[1])+1):
  scene.frame_set(f);samples.append({b.name:(b.rotation_quaternion.copy(),b.location.copy(),b.scale.copy()) for b in rig.pose.bones})
 poses=[];angles=[];rig.animation_data.action=None
 for sample in samples:
  for name,(q,l,s) in sample.items():pb=rig.pose.bones[name];pb.rotation_quaternion=q;pb.location=l;pb.scale=s
  bpy.context.view_layer.update();ua,fa,ha=[rig.pose.bones['B_R_'+n] for n in ['UpperArm','Forearm','Hand']];H=ua.head.copy();E=fa.head.copy();W=ha.head.copy();F=fa.matrix.copy();hand=ha.matrix.copy();u=(E-H).normalized();v=(W-E).normalized();normal=u.cross(v).normalized();a=align(ua.name,u,normal);fa.matrix=F;bpy.context.view_layer.update();b=align(fa.name,v,normal);ha.matrix=hand;bpy.context.view_layer.update();hand_error=max(hand_error,(ha.head-W).length);changes.append([a,b])
  rb=rig.data.bones;axes=[(rb[fa.name].matrix_local.inverted()@rb[ha.name].head_local).normalized(),(rb[ua.name].matrix_local.inverted()@rb[fa.name].head_local).normalized()];rel=(fa.matrix.inverted()@ha.matrix).to_quaternion();rest=(rb[fa.name].matrix_local.inverted()@rb[ha.name].matrix_local).to_quaternion();qs=[rel@rest.inverted(),ua.matrix_basis.to_quaternion()];angles.append([2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w) for q,axis in zip(qs,axes)]);poses.append({name:(rig.pose.bones[name].rotation_quaternion.copy(),rig.pose.bones[name].location.copy()) for name in changed})
 for pose,values in zip(poses,np.unwrap(np.array(angles),axis=0)):
  for name,axis,value,factor in zip(['B_R_ForearmTwist','B_R_UpperArmTwist'],axes,values,[.5,-.5]):
   angle=float(value*factor)
   if name=='B_R_ForearmTwist':angle=float(np.clip(angle,-math.pi/2,math.pi/2))
   pose[name]=(Quaternion(axis,angle),pose[name][1])
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 for f,pose in enumerate(poses):
  for name,(q,l) in pose.items():pb=rig.pose.bones[name];pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
 report[act.name]={'hand_target_preservation_max_m':hand_error,'upper_arm_roll_correction_max_deg':float(np.max(np.abs(np.array(changes)[:,0]))),'forearm_roll_correction_max_deg':float(np.max(np.abs(np.array(changes)[:,1])))}
 assert hand_error<1e-5
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master.blend'));(P/'review/elbow_frame_repair.json').write_text(json.dumps(report,indent=2));print('ELBOW_FRAME_REPAIR',report)
