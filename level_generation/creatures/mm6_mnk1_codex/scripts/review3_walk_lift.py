"""Raise the source swing feet to an 8 cm clearance, retaining its planted contacts and stride."""
import bpy,math,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/animation_finish.blend'))
r=bpy.data.objects['Rig'];B=r.data.bones;b=bpy.data.objects['Body'];sc=bpy.context.scene;pv=np.array([v.value for v in b.data.attributes['piece'].data]);ids={sd:np.where((pv==pi)&(np.array([v.co.z for v in b.data.vertices])<.02))[0] for sd,pi in [('L',8),('R',7)]}
def aim(n,ch,target):
 pb=r.pose.bones[n];q=(r.pose.bones[ch].head-pb.head).rotation_difference(target-pb.head)@pb.matrix.to_quaternion();m=q.to_matrix().to_4x4();m.translation=pb.head;pb.matrix=m;bpy.context.view_layer.update()
for name in ['Walking','Running']:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];rows=[]
 for f in np.arange(0,float(a.frame_range[1])+.01,.5):
  sc.frame_set(int(f),subframe=float(f%1));ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low={sd:min(me.vertices[int(i)].co.z for i in indices) for sd,indices in ids.items()};ev.to_mesh_clear();lift={sd:max(0,min(1,(z-.006)/.029)) for sd,z in low.items()};lift={sd:u*u*(3-2*u) for sd,u in lift.items()};targets={sd:r.pose.bones[f'B_{sd}_Foot'].head.copy()+Vector((0,0,.05*lift[sd])) for sd in ['L','R']};qs={sd:r.pose.bones[f'B_{sd}_Foot'].matrix.to_quaternion().copy() for sd in ['L','R']};poles={sd:r.pose.bones[f'B_{sd}_Calf'].head.copy() for sd in ['L','R']}
  root=r.pose.bones['B_Pelvis'];m=root.matrix.copy();m.translation.z+=.008*max(lift.values());root.matrix=m;bpy.context.view_layer.update();pose={}
  for sd in ['L','R']:
   un,fn,hn=[f'B_{sd}_{k}' for k in ['Thigh','Calf','Foot']];sh=r.pose.bones[un].head.copy();w=targets[sd];l1=(B[fn].head_local-B[un].head_local).length;l2=(B[hn].head_local-B[fn].head_local).length;delta=w-sh;d=min(delta.length,l1+l2-.001);e=delta.normalized();aa=(l1*l1-l2*l2+d*d)/(2*d);v=poles[sd]-sh;v=(v-e*v.dot(e)).normalized();knee=sh+e*aa+v*math.sqrt(max(0,l1*l1-aa*aa));aim(un,fn,knee);aim(fn,hn,sh+e*d);m=qs[sd].to_matrix().to_4x4();m.translation=r.pose.bones[hn].head;r.pose.bones[hn].matrix=m;bpy.context.view_layer.update()
   for n in [un,fn,hn]:pose[n]=r.pose.bones[n].rotation_quaternion.copy()
  rows.append((float(f),pose,root.location.copy()))
 for f,pose,l in rows:
  root.location=l;root.keyframe_insert('location',frame=f)
  for n,q in pose.items():r.pose.bones[n].rotation_quaternion=q;r.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
 for layer in a.layers:
  for st in layer.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/animation_finish.blend'))
