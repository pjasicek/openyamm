import bpy,sys,math,json,runpy
from pathlib import Path
from mathutils import Vector,Quaternion
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/round3_motion_before_transitions.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;sys.path.insert(0,str(p/'scripts'));import arm_solver as sol
side=sol.Side('B_L_');L=json.loads((p/'work/round2_left_grip.json').read_text());side.grip_hand=Vector(L['centre']);side.axis_hand=Vector(L['axis']);G=json.loads((p/'work/grip_pose.json').read_text());act=bpy.data.actions['Attack'];stand=bpy.data.actions['Standing']
def attach(a):rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
def smooth(t):t=max(0,min(1,t));return t*t*t*(10+t*(-15+6*t))
attach(stand);scene.frame_set(0);fingers={n:rig.pose.bones[n].rotation_quaternion.copy() for n in L['fingers']};attach(act);scene.frame_set(120);H=rig.pose.bones['B_L_Hand'].matrix.copy();R0=H.to_3x3();A0=(R0@side.axis_hand).normalized();P=rig.pose.bones['B_L_Forearm'].head-rig.pose.bones['B_L_UpperArm'].head
scene.frame_set(201);Hend=rig.pose.bones['B_L_Hand'].matrix.copy();Cend=Hend@side.grip_hand;pend=rig.pose.bones['B_Pelvis'].head.copy()
for f in [*range(78,105),*range(201,226)]:
 attach(act);scene.frame_set(f);pose={n:pb.matrix_basis.copy() for n,pb in rig.pose.bones.items()};RH=rig.pose.bones['B_R_Hand'].matrix.copy();A=(RH.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized();C=RH@Vector(G['handle_centre_hand_local'])+A*.5;Rh=A0.rotation_difference(A).to_matrix()@R0 if f<=104 else Hend.to_3x3();radial=-(Rh@side.grip_hand);radial=(radial-A*radial.dot(A)).normalized();offset=.05*(smooth((104-f)/26) if f<=104 else smooth((f-201)/24));target=C+radial*offset if f<=104 else Cend+(rig.pose.bones['B_Pelvis'].head-pend)+radial*offset
 rig.animation_data.action=None
 for n,m in pose.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update();r=side.pose_anatomical(target,Rh,P);side.apply(r);qs={n:rig.pose.bones[n].rotation_quaternion.copy() for n in ['B_L_UpperArm','B_L_Forearm','B_L_Hand']};attach(act)
 for n,q in qs.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
for f in range(301):
 attach(act);scene.frame_set(f);close=smooth((f-104)/14)*smooth((201-f)/12)
 for n,q in L['fingers'].items():rig.pose.bones[n].rotation_quaternion=fingers[n].slerp(Quaternion(q),close);rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
runpy.run_path(str(p/'scripts/normalize_keys_r2.py'));bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/round3_radial_approach.blend'))
