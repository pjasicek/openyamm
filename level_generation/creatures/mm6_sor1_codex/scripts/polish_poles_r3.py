"""Continuous anatomical elbow solution preserving the authored hand path and fixed grip frames."""
import bpy,sys,math,json,runpy,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/round3_motion.blend'));sys.path.insert(0,str(p/'scripts'));import arm_solver as sol
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;side=sol.Side('B_L_');L=json.loads((p/'work/round2_left_grip.json').read_text());side.grip_hand=Vector(L['centre']);side.axis_hand=Vector(L['axis']);act=bpy.data.actions['Attack'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
from sleeve_fit_r2 import Sleeve
sleeve=Sleeve(rig,bpy.data.objects['Body'],'B_L_');frames=[]
for f in range(301):
 scene.frame_set(f);frames.append({n:b.matrix_basis.copy() for n,b in rig.pose.bones.items()})
def restore(f):
 rig.animation_data.action=None;scene.frame_set(f)
 for n,m in frames[f].items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
angles=[];diagnostics=[]
for f in range(301):
 restore(f);H=rig.pose.bones['B_L_Hand'].matrix.copy();Rh=H.to_3x3();C=H@side.grip_hand;A=(Rh@side.axis_hand).normalized();S=rig.pose.bones['B_L_UpperArm'].head;axis=(H.translation-S).normalized();sleeve.begin();candidates=[]
 for k in range(144):
  a=k*2*math.pi/144;r=side.pose_anatomical(C,Rh,Quaternion(axis,a)@Vector((0,0,-1)));sleeve.cost(r,C,A,{})
  cost=r['sw']**2+r['tw']**2+1e6*max(0,r['sw']-60)**2+1e6*max(0,abs(r['tw'])-35)**2+1e6*max(0,abs(r['tw0'])-120)**2+2e5*max(0,sleeve.stretch-1.85)**2
  if angles:cost+=30000*((a-angles[-1]+math.pi)%(2*math.pi)-math.pi)**2
  candidates.append((cost,a,r['sw'],r['tw']))
 best=min(candidates);angles.append(best[1]);diagnostics.append([f,*best])
a=np.unwrap(angles);rad=10;w=np.exp(-np.arange(-rad,rad+1)**2/(2*3.5**2));w/=w.sum();a=np.convolve(np.pad(a,(rad,rad),mode='edge'),w,mode='valid')
for f,angle in enumerate(a):
 restore(f);H=rig.pose.bones['B_L_Hand'].matrix.copy();S=rig.pose.bones['B_L_UpperArm'].head;axis=(H.translation-S).normalized();r=side.pose_anatomical(H@side.grip_hand,H.to_3x3(),Quaternion(axis,float(angle))@Vector((0,0,-1)));side.apply(r)
 for kind in ['UpperArm','Forearm']:
  b=rig.data.bones['B_L_'+kind];child=rig.data.bones['B_L_'+('Forearm' if kind=='UpperArm' else 'Hand')];axis=(b.matrix_local.inverted()@child.head_local).normalized();q=rig.pose.bones[b.name].matrix_basis.to_quaternion() if kind=='UpperArm' else (rig.pose.bones[b.name].matrix.inverted()@rig.pose.bones[child.name].matrix).to_quaternion()@(b.matrix_local.inverted()@child.matrix_local).to_quaternion().inverted();tw=(2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w)+math.pi)%(2*math.pi)-math.pi;pb=rig.pose.bones[b.name+'Twist'];pb.rotation_quaternion=Quaternion(axis,tw*(-.5 if kind=='UpperArm' else .5));
 poses={n:rig.pose.bones[n].rotation_quaternion.copy() for n in ['B_L_UpperArm','B_L_Forearm','B_L_Hand','B_L_UpperArmTwist','B_L_ForearmTwist']};rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 for n,q in poses.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
runpy.run_path(str(p/'scripts/normalize_keys_r2.py'));(p/'work/pole_polish_r3.json').write_text(json.dumps({'samples':diagnostics,'max_unsmoothed_wrist_swing':max(r[3] for r in diagnostics),'max_unsmoothed_wrist_roll':max(abs(r[4]) for r in diagnostics)},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/round3_motion.blend'))
