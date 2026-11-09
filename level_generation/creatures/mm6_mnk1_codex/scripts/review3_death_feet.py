"""Plant the source fall's shoes with fixed-length leg IK; retain the source torso and timing."""
import bpy,math,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/animation_finish.blend'))
r=bpy.data.objects['Rig'];B=r.data.bones;sc=bpy.context.scene
a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(0)
footq={sd:r.pose.bones[f'B_{sd}_Foot'].matrix.to_quaternion().copy() for sd in ['L','R']};footz={sd:r.pose.bones[f'B_{sd}_Foot'].head.z for sd in ['L','R']}
standx={sd:r.pose.bones[f'B_{sd}_Foot'].head.x for sd in ['L','R']};meanx=sum(standx.values())/2
def aim(n,ch,target):
 pb=r.pose.bones[n];old=pb.matrix.to_quaternion();d=(r.pose.bones[ch].head-pb.head).normalized();q=d.rotation_difference((target-pb.head).normalized())@old;m=q.to_matrix().to_4x4();m.translation=pb.head;pb.matrix=m;bpy.context.view_layer.update()
a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];rows=[]
for f in np.arange(0,float(a.frame_range[1])+.01,.5):
 sc.frame_set(int(f),subframe=float(f%1));targets={};cx=sum(r.pose.bones[f'B_{sd}_Foot'].head.x for sd in ['L','R'])/2
 for sd in ['L','R']:
  un,fn,hn=[f'B_{sd}_{k}' for k in ['Thigh','Calf','Foot']];sh=r.pose.bones[un].head.copy();w=r.pose.bones[hn].head.copy();w.z=footz[sd];w.x=cx+standx[sd]-meanx;u=max(0,min(1,(f-3)/11));u=u*u*(3-2*u);w.y=max(w.y,r.pose.bones['B_Pelvis'].head.y+.50*u);pole=r.pose.bones[fn].head.copy();l1=(B[fn].head_local-B[un].head_local).length;l2=(B[hn].head_local-B[fn].head_local).length;delta=w-sh;d=min(delta.length,l1+l2-.001);e=delta.normalized();w=sh+e*d;aa=(l1*l1-l2*l2+d*d)/(2*d);v=pole-sh;v=(v-e*v.dot(e)).normalized();knee=sh+e*aa+v*math.sqrt(max(0,l1*l1-aa*aa));aim(un,fn,knee);aim(fn,hn,w);m=footq[sd].to_matrix().to_4x4();m.translation=r.pose.bones[hn].head;r.pose.bones[hn].matrix=m;bpy.context.view_layer.update()
  for n in [un,fn,hn]:targets[n]=r.pose.bones[n].rotation_quaternion.copy()
 rows.append((float(f),targets))
for f,target in rows:
 for n,q in target.items():r.pose.bones[n].rotation_quaternion=q;r.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
r.animation_data.action=bpy.data.actions['Dead'];r.animation_data.action_slot=r.animation_data.action.slots[0]
for f in [0,30]:
 for n,q in rows[-1][1].items():r.pose.bones[n].rotation_quaternion=q;r.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
for act in [a,bpy.data.actions['Dead']]:
 for layer in act.layers:
  for st in layer.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/animation_finish.blend'))
