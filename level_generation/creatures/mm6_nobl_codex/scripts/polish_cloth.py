"""Smooth the cloth deformation field down each strip while retaining the simulated joint positions."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Matrix
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v7.blend'))
r=bpy.data.objects['Rig'];sc=bpy.context.scene
body=bpy.data.objects['Body'];me=body.data
pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
neck=body.vertex_groups['B_Neck'];chest=body.vertex_groups['B_Spine2']
for v in me.vertices:
 if pv[v.index]!=0 and not (28<=pv[v.index]<=108 or pv[v.index] in [111,115]):continue
 weights={g.group:g.weight for g in v.groups};w=weights.get(neck.index,0)
 t=float(np.clip((.135-abs(v.co.x))/.065,0,1));t=t*t*(3-2*t)
 if w>0:
  neck.add([v.index],w*t,'REPLACE');chest.add([v.index],weights.get(chest.index,0)+w*(1-t),'REPLACE')

groups=[json.loads(sc[n]) for n in ['nobl_cloak','nobl_tabard','nobl_skirt_back']]
chains=[c for g in groups for c in g];names=[n for c in chains for n in c['bones']]
rest={n:r.data.bones[n].matrix_local.copy() for n in names}
for act in list(bpy.data.actions):
 if act.name not in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:continue
 r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];poses=[]
 for f in range(int(act.frame_range[1])+1):
  sc.frame_set(f)
  original={n:r.pose.bones[n].matrix.copy() for n in names}
  D={n:(original[n].to_3x3()@rest[n].to_3x3().inverted()).to_quaternion() for n in names}
  for _ in range(3):
   nxt={n:q.copy() for n,q in D.items()}
   for c in chains:
    ns=c['bones']
    for k,n in enumerate(ns):
     q=D[n]
     for j in [k-1,k+1]:
      if 0<=j<4:q=q.slerp(D[ns[j]],.25)
     nxt[n]=q
   D=nxt
  desired={}
  for n in names:
   M=(D[n].to_matrix()@rest[n].to_3x3()).to_4x4();M.translation=original[n].translation;desired[n]=M
  poses.append(desired)
 for f,desired in enumerate(poses):
  sc.frame_set(f)
  for n in names:
   pb=r.pose.bones[n];parent=pb.parent.name
   parentM=desired[parent] if parent in desired else r.pose.bones[parent].matrix
   Mu=parentM@r.data.bones[parent].matrix_local.inverted()@rest[n]
   local=Mu.inverted()@desired[n]
   pb.rotation_mode='QUATERNION';pb.rotation_quaternion=local.to_quaternion();pb.location=local.translation
   pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
  bpy.context.view_layer.update()
  err=max((r.pose.bones[n].head-desired[n].translation).length for n in names)
  assert err<1e-4,(act.name,f,err)
 print('CLOTH_POLISH',act.name,len(poses))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v7p.blend'))
