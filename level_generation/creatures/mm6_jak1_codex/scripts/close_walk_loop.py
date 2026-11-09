"""Make the free-arm elbow pole periodic without changing the library hand or leg paths."""
import bpy,sys,json,math,numpy as np,shutil
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));master=P/'work/runtime_master.blend';backup=P/'work/round2/pre_loop_runtime_master.blend'
if not backup.exists():shutil.copy2(master,backup)
bpy.ops.wm.open_mainfile(filepath=str(backup));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;action=bpy.data.actions['Walking'];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];last=int(round(action.frame_range[1]));poses=[];poles=[];hands=[]
for frame in range(last+1):
 sc.frame_set(frame);poses.append({pb.name:pb.matrix_basis.copy()for pb in rig.pose.bones});hand=rig.matrix_world@rig.pose.bones['B_L_Hand'].matrix;shoulder=(rig.matrix_world@rig.pose.bones['B_L_UpperArm'].matrix).translation;elbow=(rig.matrix_world@rig.pose.bones['B_L_Forearm'].matrix).translation;axis=(hand.translation-shoulder).normalized();pole=elbow-shoulder;pole-=axis*pole.dot(axis);poles.append(list(pole.normalized()));hands.append(hand.copy())
poles=np.array(poles[:-1]);x=np.arange(-36,37);kernel=np.exp(-.5*(x/12)**2);kernel/=kernel.sum();smooth=np.stack([np.convolve(np.pad(poles[:,j],(36,36),mode='wrap'),kernel,mode='valid')for j in range(3)],1);smooth=np.vstack([smooth,smooth[0]])
from staff_ik import Side
solver=Side('L');new=[]
for frame in range(last+1):
 sc.frame_set(frame)
 for name,m in poses[frame].items():rig.pose.bones[name].matrix_basis=m
 bpy.context.view_layer.update();hm=hands[frame];result=solver.pose_anatomical(hm@solver.grip_hand,hm.to_3x3(),Vector(smooth[frame]));solver.apply(result);new.append({name:rig.pose.bones[name].matrix_basis.copy()for name in ['B_L_UpperArm','B_L_Forearm','B_L_Hand']})
for frame,row in enumerate(new):
 for name,m in row.items():
  pb=rig.pose.bones[name];pb.matrix_basis=m;pb.keyframe_insert('location',frame=frame);pb.keyframe_insert('rotation_quaternion',frame=frame);pb.keyframe_insert('scale',frame=frame)
from bake_twist import bake_twist
bake_twist(action);rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
# Preserve the unchanged staff-side helper channels byte-for-pose.
for frame,row in enumerate(poses):
 for name in ['B_R_UpperArmTwist','B_R_ForearmTwist']:
  pb=rig.pose.bones[name];pb.matrix_basis=row[name];pb.keyframe_insert('rotation_quaternion',frame=frame)
for layer in action.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for curve in bag.fcurves:
    for key in curve.keyframe_points:key.interpolation='LINEAR'
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
selected=json.loads((P/'review/round2/reduction/selection.json').read_text());bpy.ops.wm.save_as_mainfile(filepath=str(P/selected['blend']));bpy.ops.wm.save_as_mainfile(filepath=str(master));print('PERIODIC WALK POLE',last,flush=True)
