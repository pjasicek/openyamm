"""Keep elbow flexion in its anatomical plane after world-space IK; smooth source-to-fit transitions."""
from pathlib import Path
import bpy,sys,math
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik,action_curves
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilot_fitted.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
for a in [a for a in bpy.data.actions if a.use_fake_user]:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];N=int(a.frame_range[1]);raw=[]
 for f in range(N+1):
  sc.frame_set(f);raw.append({b.name:b.matrix_basis.copy() for b in rig.pose.bones})
 frames=[]
 for f,x in enumerate(raw):
  rig.animation_data.action=None
  for n,m in x.items():rig.pose.bones[n].matrix_basis=m
  if a.name=='Attack' and 0<f<N:
   for sd in 'LR':
    for bn in ('UpperArm','Forearm','Hand'):
     n=f'B_{sd}_{bn}';q=raw[f-1][n].to_quaternion().slerp(raw[f+1][n].to_quaternion(),.5);rig.pose.bones[n].rotation_quaternion=x[n].to_quaternion().slerp(q,.65)
  bpy.context.view_layer.update()
  for sd in 'LR':
   un,fn,hn=[f'B_{sd}_{n}' for n in ('UpperArm','Forearm','Hand')];U,F,H=[armik.W(rig,n).copy() for n in (un,fn,hn)];u=(F.translation-U.translation).normalized();v=(H.translation-F.translation).normalized();normal=u.cross(v)
   if normal.length>.01:
    normal.normalize();h=U.to_3x3()@Vector((0,0,-1));h-=u*h.dot(u);h.normalize();theta=math.atan2(u.dot(h.cross(normal)),h.dot(normal));R=Quaternion(u,theta).to_matrix()@U.to_3x3();armik.set_world(rig,un,armik.rot_world(U,R));armik.set_world(rig,fn,F);armik.set_world(rig,hn,H)
  if a.name=='Attack':
   F=armik.W(rig,'B_L_Forearm').to_3x3();neutral=F@rig.data.bones['B_L_Forearm'].matrix_local.to_3x3().inverted()@rig.data.bones['B_L_Hand'].matrix_local.to_3x3();H=armik.W(rig,'B_L_Hand');R=H.to_quaternion().slerp(neutral.to_quaternion(),.30).to_matrix();armik.set_world(rig,'B_L_Hand',armik.rot_world(H,R))
  frames.append({b.name:b.matrix_basis.copy() for b in rig.pose.bones})
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for f,x in enumerate(frames):
  for sd in 'LR':
   for bn in ('UpperArm','Forearm','Hand'):
    n=f'B_{sd}_{bn}';b=rig.pose.bones[n];b.rotation_quaternion=x[n].to_quaternion();b.keyframe_insert('rotation_quaternion',frame=f)
 action_curves.continuous(a)
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/pilot_fitted.blend'))
