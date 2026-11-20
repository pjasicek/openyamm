"""Plant the idle's two boots using the existing knee plane, without changing the crouch or foot orientation."""
import bpy,math,sys,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v5.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
vg=[g.name for g in body.vertex_groups]
foot={sd:np.array([sum(e.weight for e in v.groups if vg[e.group] in (f'B_{sd}_Foot',f'B_{sd}_Toe0'))>.5 for v in body.data.vertices]) for sd in 'LR'}
a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];keys=[]
for f in range(int(a.frame_range[1])+1):
 sc.frame_set(f);snap={pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones};rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis=snap[pb.name]
 bpy.context.view_layer.update()
 for sd in 'LR':
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();z=np.array([(body.matrix_world@v.co).z for v in m.vertices]);ev.to_mesh_clear();low=float(z[foot[sd]].min())
  th,ca,ft=[f'B_{sd}_{n}' for n in ('Thigh','Calf','Foot')];M1,M2,MF=[armik.W(rig,n) for n in (th,ca,ft)]
  H,K,A=[M.translation.copy() for M in (M1,M2,MF)];T=A.copy();T.z+=.003-low;l1=(K-H).length;l2=(A-K).length;u=(T-H).normalized();d=(T-H).length
  assert d<(l1+l2)*.999
  pole=K-H-u*(K-H).dot(u);pole.normalize();c=(l1*l1+d*d-l2*l2)/(2*l1*d);Kn=H+l1*(u*c+pole*math.sqrt(max(0,1-c*c)))
  q=(K-H).rotation_difference(Kn-H);armik.set_world(rig,th,armik.rot_world(M1,q.to_matrix()@M1.to_3x3()))
  M2=armik.W(rig,ca);q=(armik.W(rig,ft).translation-M2.translation).rotation_difference(T-M2.translation);armik.set_world(rig,ca,armik.rot_world(M2,q.to_matrix()@M2.to_3x3()))
  armik.set_world(rig,ft,armik.rot_world(armik.W(rig,ft),MF.to_3x3()))
 keys.append({n:rig.pose.bones[n].rotation_quaternion.copy() for n in [f'B_{sd}_{part}' for sd in 'LR' for part in ('Thigh','Calf','Foot')]})
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
for f,pose in enumerate(keys):
 for n,q in pose.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_mainfile()
