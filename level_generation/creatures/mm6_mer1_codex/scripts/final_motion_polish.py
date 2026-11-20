"""Smooth the retargeted action transitions while preserving planted legs and grip frames."""
import bpy,sys,math,json,shutil,numpy as np
from pathlib import Path
from mathutils import Quaternion,Matrix
P=Path(__file__).resolve().parents[1];backup=P/'work/pre_final_polish.blend'
if not backup.exists():shutil.copyfile(P/'work/reduction_master.blend',backup)
bpy.ops.wm.open_mainfile(filepath=str(backup));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
r=rig.animation_data;r.action=bpy.data.actions['Standing'];r.action_slot=r.action.slots[0];sc.frame_set(0)
neutral={n:rig.pose.bones[n].rotation_quaternion.copy()for n in ['B_Neck','B_Head']};changes={}
for role in ['Attack','Hit','Death']:
 a=bpy.data.actions[role];r.action=a;r.action_slot=a.slots[0];frames=np.arange(0,float(a.frame_range[1])+.001,.25)
 names=['B_Neck','B_Head']+([f'B_{sd}_{part}'for sd in 'LR'for part in ['Clavicle','UpperArm','UpperArmTwist','Forearm','ForearmTwist','Hand']]if role!='Hit'else[])
 names=[n for n in names if n in rig.pose.bones];values={n:[]for n in names};oldH=[];oldClub=[]
 for f in frames:
  sc.frame_set(int(f),subframe=float(f%1));oldH.append(rig.pose.bones['B_R_Hand'].matrix.copy());oldClub.append(rig.pose.bones['Club'].matrix.copy())
  for n in names:
   q=rig.pose.bones[n].rotation_quaternion.copy()
   if n in neutral:
    d=neutral[n].rotation_difference(q)
    if d.w<0:d=-d
    q=neutral[n].slerp(q,min(1,math.radians(20)/max(d.angle,1e-8)))
   if values[n] and q.dot(Quaternion(values[n][-1]))<0:q=-q
   values[n].append(list(q))
 for n,vs in values.items():
  arr=np.array(vs);smooth=[]
  for i,f in enumerate(frames):
   weights=np.exp(-.5*((frames-f)/1.65)**2);weights[abs(frames-f)>4.95]=0;q=(arr*weights[:,None]).sum(0);q/=np.linalg.norm(q);smooth.append(Quaternion(q))
  for f,q in zip(frames,smooth):rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=float(f))
 if role=='Attack':
  prev=None
  for i,f in enumerate(frames):
   sc.frame_set(int(f),subframe=float(f%1));H=rig.pose.bones['B_R_Hand'].matrix;target=H@oldH[i].inverted()@oldClub[i];w=min(1,float(f)/6,(float(a.frame_range[1])-f)/7.5);w=w*w*(3-2*w)
   M=oldClub[i].to_quaternion().slerp(target.to_quaternion(),w).to_matrix().to_4x4();M.translation=oldClub[i].translation.lerp(target.translation,w);pb=rig.pose.bones['Club'];pb.matrix=M;q=pb.rotation_quaternion.copy()
   if prev and q.dot(prev)<0:q=-q
   prev=q;pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=float(f));pb.keyframe_insert('location',frame=float(f))
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 changes[role]={'smoothed_bones':names,'sigma_seconds':.055,'head_neck_max_local_delta_deg':20}
r.action=bpy.data.actions['Death'];r.action_slot=r.action.slots[0];sc.frame_set(int(r.action.frame_range[1]));terminal={b.name:(b.location.copy(),b.rotation_quaternion.copy(),b.scale.copy())for b in rig.pose.bones}
r.action=bpy.data.actions['Dead'];r.action_slot=r.action.slots[0]
for b in rig.pose.bones:
 for f in [0,30]:
  b.location,b.rotation_quaternion,b.scale=terminal[b.name]
  for field in ['location','rotation_quaternion','scale']:b.keyframe_insert(field,frame=f)
changes['Dead']={'source':'Held polished terminal Death pose'}
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/reduction_master.blend'))
# The distance candidates use the same skeleton; replace their action data without touching geometry or UVs.
selection=json.loads((P/'review/reduction/selection.json').read_text())
for entry in selection['body']:
 bpy.ops.wm.open_mainfile(filepath=str(P/entry['blend']));r=bpy.data.objects['Rig'].animation_data;r.action=None
 for role in changes:
  if role in bpy.data.actions:bpy.data.actions.remove(bpy.data.actions[role])
 with bpy.data.libraries.load(str(P/'work/reduction_master.blend'),link=False)as(src,dst):dst.actions=list(changes)
 for a in dst.actions:a.use_fake_user=True
 bpy.ops.wm.save_as_mainfile(filepath=str(P/entry['blend']))
(P/'review/final_motion_polish.json').write_text(json.dumps(changes,indent=2));print('Final motion polish saved')
