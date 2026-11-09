from pathlib import Path
import bpy,sys,math,numpy as np
from mathutils import Vector,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik,action_curves
bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_repaired.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
for name in ('Running','Death'):
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];N=int(a.frame_range[1]);frames=[]
 for i in range(N*2+1):
  f=i/2;sc.frame_set(int(f),subframe=f-int(f));frames.append({b.name:b.matrix_basis.copy() for b in rig.pose.bones})
 if name=='Death':
  qs=[x['B_R_Hand'].to_quaternion() for x in frames]
  for i in range(1,len(qs)):
   if qs[i].dot(qs[i-1])<0:qs[i]=-qs[i]
  for i in range(2,len(frames)-2):
   q=Quaternion(np.array([tuple(x) for x in qs[i-2:i+3]]).T@np.array([1,2,3,2,1])/9);q.normalize();frames[i]['B_R_Hand']=q.to_matrix().to_4x4()
 else:
  for i,x in enumerate(frames):
   rig.animation_data.action=None
   for n,m in x.items():rig.pose.bones[n].matrix_basis=m
   bpy.context.view_layer.update()
   H=armik.W(rig,'B_L_Hand');armik.solve(rig,'L',H.translation+Vector((.008,0,0)),hand_rot=H.to_3x3())
   # The opposite upper arm is thick; carry the club's striking head farther ahead during the crossing.
   H=armik.W(rig,'B_R_Hand');w=math.exp(-.5*((i/2-13)/3)**2);armik.solve(rig,'R',H.translation+Vector((-.025,-.055,.015))*w,hand_rot=H.to_3x3())
   frames[i]={b.name:b.matrix_basis.copy() for b in rig.pose.bones}
  frames[-1]=frames[0]
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 changed=['B_R_Hand'] if name=='Death' else [f'B_{s}_{n}' for s in 'LR' for n in ('UpperArm','Forearm','Hand')]
 action_curves.remove_rotations(a,changed);previous={}
 for i,x in enumerate(frames):
  for n in changed:
   q=x[n].to_quaternion()
   if n in previous and q.dot(previous[n])<0:q=-q
   previous[n]=q.copy();rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=i/2)
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/full_repaired.blend'))
