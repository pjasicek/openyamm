import bpy,math,json,sys,runpy,numpy as np
from mathutils import Quaternion,Vector
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));bpy.ops.wm.open_mainfile(filepath=str(P/'work/pre_motion.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
from arm_ik import Side,swing_twist_deg
sides={s:Side(s)for s in 'LR'};roles=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget'];names=[n for n in rig.pose.bones.keys() if n in ['B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']or any(n==f'B_{s}_{k}'for s in 'LR'for k in ['Clavicle','UpperArm','Forearm','Hand'])]
def average(seq,i,sigma=4):
 weights=np.exp(-np.arange(-12,13,dtype=float)**2/(2*sigma*sigma));v=np.zeros(4);ref=seq[i]
 for off,w in zip(range(-12,13),weights):
  q=seq[(i+off)%(len(seq)-1)if role in ['Walking','Running']else max(0,min(len(seq)-1,i+off))];v+=np.array(q)*(w if q.dot(ref)>=0 else-w)
 return Quaternion(v/np.linalg.norm(v))
for role in roles:
 if role in ['Standing','Dead','Fidget']:continue
 act=bpy.data.actions[role];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];end=int(act.frame_range[1]);qs={n:[]for n in names};hands=[]
 for f in range(end+1):
  sc.frame_set(f)
  for n in names:qs[n].append(rig.pose.bones[n].rotation_quaternion.copy())
  hands.append(rig.pose.bones['B_L_Hand'].matrix.to_quaternion())
 frames=[]
 for f in range(end+1):
  sc.frame_set(f)
  for n in names:rig.pose.bones[n].rotation_quaternion=average(qs[n],f)
  bpy.context.view_layer.update()
  for sd in 'LR':
   obj=sides[sd];U,F,H=[rig.pose.bones[f'B_{sd}_{n}']for n in ['UpperArm','Forearm','Hand']];A=U.matrix.to_3x3();old=F.matrix.to_3x3();d=(old@obj.uF).normalized();normal=(A@Vector((0,0,-1))).normalized();d=(d-normal*d.dot(normal)).normalized();base=A@obj.rel['ForeArm'];base=(base@obj.uF).rotation_difference(d).to_matrix()@base;tw=swing_twist_deg((base.inverted()@old).to_quaternion(),obj.uF)[1];new=Quaternion(d,math.radians(max(-85,min(85,tw)))).to_matrix()@base;M=new.to_4x4();M.translation=F.head;F.matrix=M;bpy.context.view_layer.update()
  # Keep the shield palm and board orientation continuous in world space after smoothing its carrying arm.
  H=rig.pose.bones['B_L_Hand'];M=average(hands,f).to_matrix().to_4x4();M.translation=H.head;H.matrix=M;bpy.context.view_layer.update();frames.append({n:rig.pose.bones[n].rotation_quaternion.copy()for n in names})
 previous={}
 for f,row in enumerate(frames):
  for n,q in row.items():
   if n in previous and q.dot(previous[n])<0:q.negate()
   previous[n]=q.copy();pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
ns=runpy.run_path(str(P/'scripts/bake_twist.py'));[ns['bake_twist'](bpy.data.actions[n])for n in roles]
# Dead is a held final Death pose, including the smoothed arms and helpers.
a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(int(a.frame_range[1]));last={pb.name:pb.rotation_quaternion.copy()for pb in rig.pose.bones};a=bpy.data.actions['Dead'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
for f in range(int(a.frame_range[1])+1):
 for n,q in last.items():pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/accepted_master.blend'))
runpy.run_path(str(P/'scripts/motion_probe.py'),run_name='__main__')
