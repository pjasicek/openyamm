import bpy,sys,json,math,numpy as np,runpy
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction_master.blend'))
r=bpy.data.objects['Rig'];s=bpy.context.scene;a=bpy.data.actions['Running'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
frames=[];ratio=.84*1.55/1.18
for f in np.arange(0,24.0001,.25):
 s.frame_set(int(f),subframe=float(f%1));frames.append((float(f),{b.name:b.matrix_basis.copy()for b in r.pose.bones},{sd:r.pose.bones[f'B_{sd}_Foot'].matrix.copy()for sd in 'LR'}))
r.animation_data.action=None
lens={sd:[(r.data.bones[f'B_{sd}_{b}'].head_local-r.data.bones[f'B_{sd}_{c}'].head_local).length for b,c in [('Thigh','Calf'),('Calf','Foot')]]for sd in 'LR'}
def aim(n,ch,v):
 b=r.pose.bones[n];M=b.matrix.copy();delta=(r.pose.bones[ch].head-b.head).normalized().rotation_difference(v.normalized()).to_matrix().to_4x4();T=M.translation.copy();M=delta@M;M.translation=T;b.matrix=M;bpy.context.view_layer.update()
poses=[];drops=[]
for f,pose,feet in frames:
 for n,M in pose.items():r.pose.bones[n].matrix_basis=M
 bpy.context.view_layer.update();pel=r.pose.bones['B_Pelvis'].matrix.copy();oldz=pel.translation.z
 for sd,M in feet.items():
  M.translation.y*=ratio;H=r.pose.bones[f'B_{sd}_Thigh'].head;reach=sum(lens[sd])-.003;xy=(M.translation.x-H.x)**2+(M.translation.y-H.y)**2;pel.translation.z=min(pel.translation.z,M.translation.z+math.sqrt(reach**2-xy)+oldz-H.z)
 r.pose.bones['B_Pelvis'].matrix=pel;bpy.context.view_layer.update();drops.append(oldz-pel.translation.z)
 for sd,M in feet.items():
  th,ca,ft=[f'B_{sd}_{n}'for n in ['Thigh','Calf','Foot']];H=r.pose.bones[th].head.copy();T=M.translation;A,B=lens[sd];d=(T-H).length;assert abs(A-B)<d<A+B
  u=(T-H).normalized();v=Vector((0,-1,0));v=(v-u*v.dot(u)).normalized();c=(A*A+d*d-B*B)/(2*A*d);K=H+A*(u*c+v*math.sqrt(max(0,1-c*c)));aim(th,ca,K-H);aim(ca,ft,T-K);r.pose.bones[ft].matrix=M;bpy.context.view_layer.update()
 poses.append((f,{n:r.pose.bones[n].matrix_basis.copy()for n in ['B_Pelvis']+[f'B_{sd}_{n}'for sd in 'LR'for n in ['Thigh','Calf','Foot']]}))
r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];prev={}
for f,pose in poses:
 for n,M in pose.items():
  b=r.pose.bones[n];b.matrix_basis=M;q=b.rotation_quaternion.copy()
  if n in prev and q.dot(prev[n])<0:q=-q
  b.rotation_quaternion=q;prev[n]=q;b.keyframe_insert('location',frame=f);b.keyframe_insert('rotation_quaternion',frame=f)
for l in a.layers:
 for st in l.strips:
  for cb in st.channelbags:
   for fc in cb.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
s.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/reduction_master.blend'))
(P/'review/running_stride.json').write_text(json.dumps({'walking_stride_m':.84,'runtime_run_multiplier':1.55,'running_stride_before_m':1.18,'running_stride_m':.84*1.55,'max_pelvis_lowering_mm':max(drops)*1000,'bake_hz':120},indent=2))
sys.argv=['audit_motion.py','--','work/reduction_master.blend','stride_corrected'];runpy.run_path(str(P/'scripts/audit_motion.py'),run_name='__main__')
