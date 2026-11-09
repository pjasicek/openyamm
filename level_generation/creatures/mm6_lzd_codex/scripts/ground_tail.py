"""Three fitted tail joints and per-frame floor contact, without changing gameplay root motion."""
import bpy,json,math,sys
import numpy as np
from mathutils import Vector,Matrix,Quaternion
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_reweighted.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
co=np.array([tuple(v.co)for v in me.vertices]);pv=np.array([x.value for x in me.attributes['piece'].data]);tail=(pv==1)&(co[:,1]>.14)&(co[:,2]>.50)&(abs(co[:,0])<.17)
centres=[Vector((0,.155,.765))]
for y in [.27,.37,.47]:
 pts=co[tail&(abs(co[:,1]-y)<.025)];assert len(pts)>2;centres.append(Vector(pts.mean(0)))
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for i in range(3):
 n=rig.data.edit_bones.new('Tail'+str(i));n.head=centres[i];n.tail=centres[i+1];n.parent=rig.data.edit_bones['B_Pelvis'if i==0 else'Tail'+str(i-1)];n.align_roll(Vector((0,0,1)))
bpy.ops.object.mode_set(mode='OBJECT')
for i in range(3):body.vertex_groups.new(name='Tail'+str(i))
names=[g.name for g in body.vertex_groups]
for vi in np.where(tail)[0]:
 y=co[vi,1];weights={}
 if y<.21:
  t=float(np.clip((y-.14)/.07,0,1));weights={'B_Pelvis':1-t,'Tail0':t}
 elif y<.32:
  t=float((y-.21)/.11);weights={'Tail0':1-t,'Tail1':t}
 else:
  t=float(np.clip((y-.32)/.11,0,1));weights={'Tail1':1-t,'Tail2':t}
 for g in body.vertex_groups:g.remove([int(vi)])
 for n,w in weights.items():
  if w>1e-5:body.vertex_groups[n].add([int(vi)],w,'REPLACE')
# Keep the character's soles on the authored floor; the corrected ankle differs from the source mannequin's.
feet=np.where((pv==1)&(co[:,2]<.15))[0];rootinv=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted();rep={}
for act in bpy.data.actions:
 if act.name not in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:continue
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];N=int(act.frame_range[1]);floor=[]
 for f in range(N+1):
  scene.frame_set(f)
  for i in range(3):
   pb=rig.pose.bones['Tail'+str(i)];pb.rotation_mode='QUATERNION';amp=math.radians(4 if act.name in ('Standing','Fidget')else 7);period=max(N,1)
   pb.rotation_quaternion=Quaternion((0,0,1),amp*math.sin(2*math.pi*f/period-i*.45))
   if act.name in ('Death','Dead'):
    u=1 if act.name=='Dead' else min(1,max(0,(f-5)/10));pb.rotation_quaternion=Quaternion()
    if i==0:
     bpy.context.view_layer.update();M=pb.matrix.copy();cur=M.to_3x3()@Vector((0,1,0));target=Vector((0,1,-.18)).normalized();q=cur.rotation_difference(target);t=M.translation.copy();M=Quaternion().slerp(q,u).to_matrix().to_4x4()@M;M.translation=t;pb.matrix=M
   pb.keyframe_insert('rotation_quaternion',frame=f)
  bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();xyz=np.array([tuple(v.co)for v in m.vertices]);ev.to_mesh_clear();z=float(xyz[:,2].min())if act.name in ('Death','Dead')else float(xyz[feet,2].min());dz=-z
  rig.pose.bones['B_Pelvis'].location+=rootinv@Vector((0,0,dz));rig.pose.bones['B_Pelvis'].keyframe_insert('location',frame=f);floor.append(dz)
 rep[act.name]={'floor_correction_m':[min(floor),max(floor)]}
rig.animation_data.action=None
(P/'work/tail_floor.json').write_text(json.dumps({'tail_joints':[list(v)for v in centres],'clips':rep},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_grounded.blend'))
