import bpy,sys,json,math,numpy as np,runpy
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/before_death_surface.blend'))
r=bpy.data.objects['Rig'];s=bpy.context.scene;a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
frames=[];ratio=.84*1.55/1.18
for f in np.arange(0,float(a.frame_range[1])+.001,.25):
 s.frame_set(int(f),subframe=float(f%1));frames.append((float(f),{b.name:b.matrix_basis.copy()for b in r.pose.bones},{sd:r.pose.bones[f'B_{sd}_Foot'].matrix.copy()for sd in 'L'}))
r.animation_data.action=None
lens={sd:[(r.data.bones[f'B_{sd}_{b}'].head_local-r.data.bones[f'B_{sd}_{c}'].head_local).length for b,c in [('Thigh','Calf'),('Calf','Foot')]]for sd in 'LR'}
def aim(n,ch,v):
 b=r.pose.bones[n];M=b.matrix.copy();delta=(r.pose.bones[ch].head-b.head).normalized().rotation_difference(v.normalized()).to_matrix().to_4x4();T=M.translation.copy();M=delta@M;M.translation=T;b.matrix=M;bpy.context.view_layer.update()
poses=[];drops=[]
for f,pose,feet in frames:
 for n,M in pose.items():r.pose.bones[n].matrix_basis=M
 bpy.context.view_layer.update();pel=r.pose.bones['B_Pelvis'].matrix.copy();oldz=pel.translation.z
 for sd,M in feet.items():
  w=math.sin(math.pi*min(1,max(0,(f/30-.8)/1.0)))**2;M.translation.x-=.20*w;M.translation.y+=.15*w;M.translation.z=max(M.translation.z-.4*w,min(M.translation.z,.16));H=r.pose.bones[f'B_{sd}_Thigh'].head;reach=sum(lens[sd])-.003;xy=(M.translation.x-H.x)**2+(M.translation.y-H.y)**2;pel.translation.z=min(pel.translation.z,M.translation.z+math.sqrt(reach**2-xy)+oldz-H.z)
 # Preserve the library pelvis trajectory.
 for sd,M in feet.items():
  th,ca,ft=[f'B_{sd}_{n}'for n in ['Thigh','Calf','Foot']];H=r.pose.bones[th].head.copy();T=M.translation;A,B=lens[sd];d=(T-H).length
  if d>A+B-.002:T=H+(T-H).normalized()*(A+B-.002);M.translation=T;d=(T-H).length
  assert abs(A-B)<d<A+B
  pole=r.pose.bones[ca].head-H
  for floor_iteration in range(8):
   d=(T-H).length
   if d>A+B-.002:T=H+(T-H).normalized()*(A+B-.002);M.translation=T;d=(T-H).length
   u=(T-H).normalized();v=(pole-u*pole.dot(u)).normalized();c=(A*A+d*d-B*B)/(2*A*d);K=H+A*(u*c+v*math.sqrt(max(0,1-c*c)));aim(th,ca,K-H);aim(ca,ft,T-K);r.pose.bones[ft].matrix=M;bpy.context.view_layer.update()
   obj=bpy.data.objects['Body'];ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();low=min(v.co.z for v in mesh.vertices if obj.data.attributes['piece'].data[v.index].value==6);ev.to_mesh_clear()
   if low>=.003:break
   T.z+=.004-low;M.translation=T

 poses.append((f,{n:r.pose.bones[n].matrix_basis.copy()for n in [f'B_{sd}_{n}'for sd in 'L'for n in ['Thigh','Calf','Foot']]}))
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
(P/'review/death_leg_clearance.json').write_text(json.dumps({'source':'Standing Death Forward 02','window_seconds':[.8,1.8],'foot_delta_peak_m':[-.20,.15,-.4],'minimum_target_ankle_m':.16,'actual_boot_floor_m':.003,'pelvis_changed':False,'pole':'source knee direction','bake_hz':120},indent=2))
