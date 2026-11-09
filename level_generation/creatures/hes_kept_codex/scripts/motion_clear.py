"""Body-proportion clearance over the selected mocap, preserving the source hand orientation."""
import bpy,sys,os,math,json
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_natm_claude/scripts'));import armik
src,out=sys.argv[sys.argv.index('--')+1:];kind=os.environ['KEPT_BODY']
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
for a in sorted(bpy.data.actions,key=lambda a:a.name):
 if not a.name.startswith('Kept_'):continue
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];poses=[];n=int(a.frame_range[1]);correction=0.;clamps=0
 for f in range(n+1):
  sc.frame_set(f);snap={pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones};rig.animation_data.action=None
  for pb in rig.pose.bones:pb.matrix_basis=snap[pb.name]
  bpy.context.view_layer.update()
  offset={'Kept_Attack':(-.12,-.04,.08),'Kept_MaceAttack':(-.035,-.025,0)}.get(a.name)
  if offset:
   weight=min(1,f/5,(n-f)/5) if a.name!='Kept_ArmedDeath' else min(1,f/5)
   weight=max(weight,0);weight=weight*weight*(3-2*weight)
   # Pelvis yaw carries the offset; falling pitch does not fold the clearance back into the garment.
   M=armik.W(rig,'B_Pelvis');b=rig.data.bones['B_Pelvis'];rot=M.to_3x3()@b.matrix_local.to_3x3().inverted()
   forward=rot@Vector((0,-1,0));yaw=math.atan2(forward.x,-forward.y)
   delta=Matrix.Rotation(yaw,3,'Z')@Vector(offset)*weight;H=armik.W(rig,'B_R_Hand')
   armik.solve(rig,'R',H.translation+delta,hand_rot=H.to_3x3().normalized());correction=max(correction,delta.length)
  for sd in 'LR':
   pb=rig.pose.bones[f'B_{sd}_Hand'];swing,tw=armik.split_swing_twist(pb.rotation_quaternion,Vector((0,1,0)))
   angle=min(swing.angle,2*math.pi-swing.angle)
   if angle>math.radians(58):
    if swing.w<0:swing=-swing
    pb.rotation_quaternion=Quaternion().slerp(swing,math.radians(58)/angle)@Quaternion((0,1,0),tw);clamps+=1
  bpy.context.view_layer.update();poses.append({pb.name:(pb.rotation_quaternion.copy(),pb.location.copy()) for pb in rig.pose.bones})
  rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 prev={}
 for f,p in enumerate(poses):
  for name,(q,l) in p.items():
   if name in prev and q.dot(prev[name])<0:q=-q
   prev[name]=q.copy();pb=rig.pose.bones[name];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
 rig.animation_data.action=None
 print('CLEAR',a.name,'wrist offset max m',correction,'swing keys limited',clamps,flush=True)
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

sys.stdout.flush();sys.stderr.flush();os._exit(0)
