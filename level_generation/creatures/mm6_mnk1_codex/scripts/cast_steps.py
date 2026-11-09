"""20% of measured source foot travel, in two planted IK steps (out and back)."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/anim_pilot.blend'));r=bpy.data.objects['Rig'];B=r.data.bones;steps=json.loads((p/'work/source_steps.json').read_text())
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def setact(a):r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
def aim(n,child,target):
 pb=r.pose.bones[n];rest=B[child].head_local-B[n].head_local;carry=pb.parent.matrix.to_3x3()@B[n].parent.matrix_local.to_3x3().inverted();q=(carry@rest).rotation_difference(target-pb.head)@(carry@B[n].matrix_local.to_3x3()).to_quaternion();m=q.to_matrix().to_4x4();m.translation=pb.head;pb.matrix=m;bpy.context.view_layer.update()
for role,st in steps.items():
 a=bpy.data.actions[role];setact(a);bpy.context.scene.frame_set(0);sd=st['side'];u,f,h=[f'B_{sd}_{n}' for n in ['Thigh','Calf','Foot']];base=r.pose.bones[h].head.copy();footq=r.pose.bones[h].matrix.to_quaternion().copy();legnames=[n for n in B.keys() if n.startswith(f'B_{sd}_') and any(k in n for k in ['Thigh','Calf','Foot','Toe'])];keys=[];lead=8 if role=='Attack' else 0;N=int(a.frame_range[1])-lead;peak=st['source_peak_frame'];start=max(0,peak-5);end=N
 for fr in range(int(a.frame_range[1])+1):
  bpy.context.scene.frame_set(fr);i=fr-lead;outward=smooth((i-start)/5);back=smooth((i-(N-6))/6);progress=outward*(1-back)
  old={n:r.pose.bones[n].rotation_quaternion.copy() for n in legnames}
  if progress<=0:keys.append((fr,old));continue
  target=base+Vector(st['step_delta_m'])*progress;lift=math.sin(math.pi*((i-start)/5)) if start<i<peak else math.sin(math.pi*((i-(N-6))/6)) if N-6<i<N else 0;target.z+=max(0,lift)*abs(st['source_delta_m'][2])*.2
  sh=r.pose.bones[u].head.copy();L1=(B[f].head_local-B[u].head_local).length;L2=(B[h].head_local-B[f].head_local).length;dv=target-sh;D=min(dv.length,L1+L2-.001);d=dv.normalized();target=sh+d*D
  aa=(L1*L1-L2*L2+D*D)/(2*D);bb=math.sqrt(max(0,L1*L1-aa*aa));v=Vector((0,-1,0));v=(v-d*v.dot(d)).normalized();aim(u,f,sh+d*aa+v*bb);aim(f,h,target)
  pb=r.pose.bones[h];m=footq.to_matrix().to_4x4();m.translation=pb.head;pb.matrix=m;bpy.context.view_layer.update()
  keys.append((fr,{n:old[n].slerp(r.pose.bones[n].rotation_quaternion,progress) for n in legnames}))
 for fr,pose in keys:
  for n,q in pose.items():r.pose.bones[n].rotation_quaternion=q;r.pose.bones[n].keyframe_insert('rotation_quaternion',frame=fr)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/anim_pilot.blend'))
