"""Solve head/shoulder clearance on the actual lizard geometry and preserve smooth controls."""
import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));from g6_head_clearance import Clearance
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_grounded.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;names=[b.name for b in rig.data.bones];C=Clearance(bpy.data.objects['Body'])
def select(a):
 rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def capture():return{n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy())for n in names}
def apply(p):
 select(None)
 for n,(q,l)in p.items():pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l
 bpy.context.view_layer.update()
def turn(n,axis,degrees):
 pb=rig.pose.bones[n];M=pb.matrix.copy();t=M.translation.copy();M=Matrix.Rotation(math.radians(degrees),4,axis)@M;M.translation=t;pb.matrix=M;bpy.context.view_layer.update()
def correct(p,side,ctrl):
 apply(p);pitch,down,away=ctrl
 lat=(rig.pose.bones['B_L_UpperArm'].head-rig.pose.bones['B_R_UpperArm'].head).normalized()
 turn('B_Neck',lat,pitch*.5);turn('B_Head',lat,pitch*.5)
 axis=Vector((0,-1,0));turn('B_'+side+'_Clavicle',axis,down*(-1 if side=='L'else 1))
 turn('B_Neck',Vector((0,1,0)),away*(-1 if side=='L'else 1))
select(bpy.data.actions['Standing']);scene.frame_set(0);HOME=capture()
report={}
for an in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:
 a=bpy.data.actions[an];poses=[];N=int(a.frame_range[1])
 for f in range(N+1):
  select(a);scene.frame_set(f);p=capture();apply(p)
  if an in ('Standing','Fidget'):turn('B_R_UpperArm','X',-6)
  if an=='Hit':
   d=rig.pose.bones['B_Neck'].head-rig.pose.bones['B_Spine'].head;lean=math.atan2(-d.y,d.z);turn('B_Spine','X',-math.degrees(lean)*.55)
  if an not in ('Death','Dead'):
   for sd in 'LR':
    bn='B_'+sd+'_UpperArm';rot=rig.pose.bones[bn].matrix.to_quaternion();rig.pose.bones['B_'+sd+'_Clavicle'].rotation_quaternion=HOME['B_'+sd+'_Clavicle'][0];bpy.context.view_layer.update();M=rot.to_matrix().to_4x4();M.translation=rig.pose.bones[bn].head;rig.pose.bones[bn].matrix=M;bpy.context.view_layer.update()
   if an=='Hit':
    for sd in 'LR':
     bn='B_'+sd+'_UpperArm';pb=rig.pose.bones[bn];pb.rotation_quaternion=HOME[bn][0].slerp(pb.rotation_quaternion,.5)
    bpy.context.view_layer.update()
  poses.append(capture())
 controls=[];sides=[];before=[]
 for p in poses:
  apply(p);dep,dist,side=C.measure();side=side or'L';before.append(dep);sides.append(side);best=(dep,0,(0,0,0))
  if dep>.005:
   candidates=[(pitch,down,away)for pitch in (-30,-20,-10,0,10,20,30)for down in (0,8,16,24,32)for away in (0,8)]
   candidates.sort(key=lambda c:abs(c[0])+c[1]*.9+c[2]*1.5)
   for c in candidates:
    correct(p,side,c);depth=C.measure()[0];cost=abs(c[0])+c[1]*.9+c[2]*1.5
    if depth<best[0]:best=(depth,cost,c)
    if depth<=.005:best=(depth,cost,c);break
  controls.append(best[2])
 # Envelopes per side, widened one frame so interpolation cannot reintroduce contacts between keys.
 envelopes={sd:np.zeros((N+1,3))for sd in 'LR'}
 for f,(sd,c)in enumerate(zip(sides,controls)):
  for k in [f]:
   for j,v in enumerate(c):
    if abs(v)>abs(envelopes[sd][k,j]):envelopes[sd][k,j]=v
 outputs=[];after=[]
 for f,p in enumerate(poses):
  apply(p)
  for sd in 'LR':
   c=envelopes[sd][f]
   if np.any(c):correct(capture(),sd,c)
  outputs.append(capture());after.append(C.measure()[0])
 select(a)
 for f,p in enumerate(outputs):
  for n,(q,l)in p.items():
   pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
 report[an]={'before_max_m':max(before),'after_max_m':max(after),'controls':{sd:a.tolist()for sd,a in envelopes.items()}};print('HEADFIX',an,max(before),max(after))
select(None);(P/'review/head_corrections.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_preprops.blend'))
