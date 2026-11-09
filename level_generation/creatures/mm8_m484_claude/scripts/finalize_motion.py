import bpy,json,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilots_cloth.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];ax=bpy.data.objects['AxeMesh'];sc=bpy.context.scene;sc.render.fps=30
roles=['Standing','Walking','Running','Attack','Hit','Death','Fidget'];names=list(r.pose.bones.keys());restpel=r.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()
def act(a):
 r.animation_data.action=a
 if a and len(a.slots):r.animation_data.action_slot=a.slots[0]
def snap():return {p.name:p.matrix_basis.copy() for p in r.pose.bones}
def blend(a,b,t):
 m=a.to_quaternion().slerp(b.to_quaternion(),t).to_matrix().to_4x4();m.translation=a.translation.lerp(b.translation,t);return m
act(bpy.data.actions['Standing']);sc.frame_set(0);home=snap();poses={};floor={}
for nm in roles:
 a=bpy.data.actions[nm];rows=[];N=float(a.frame_range[1]);moves=[]
 for f in np.arange(0,N+.01,.5):
  act(a);sc.frame_set(int(f),subframe=f%1);row=snap();act(None)
  weight=0
  if nm in ['Hit','Fidget','Death']:
   weight=max(0,1-f/3)
   if nm!='Death':weight=max(weight,max(0,1-(N-f)/3))
   weight=weight*weight*(3-2*weight)
  for n,m in row.items():r.pose.bones[n].matrix_basis=blend(m,home[n],weight)
  bpy.context.view_layer.update();low=1e9
  for o in [b,ax]:
   ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low=min(low,min(v.co.z for v in me.vertices));ev.to_mesh_clear()
  dz=max(0,-low) if nm=='Running' else -low;r.pose.bones['B_Pelvis'].location+=restpel@Vector((0,0,dz));bpy.context.view_layer.update();moves.append(dz);rows.append(snap())
 if nm in ['Standing','Walking','Running']:rows[-1]=rows[0]
 poses[nm]=rows;floor[nm]={'range_m':[min(moves),max(moves)]}
poses['Cast']=poses['Attack'];poses['Dead']=[poses['Death'][-1]]*61
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
for nm,rows in poses.items():
 a=bpy.data.actions.new(nm);a.use_fake_user=True;act(a);last={}
 for i,row in enumerate(rows):
  for n,m in row.items():
   pb=r.pose.bones[n];q=m.to_quaternion()
   if n in last and q.dot(last[n])<0:q=-q
   last[n]=q.copy();pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=m.translation;pb.scale=(1,1,1);pb.keyframe_insert('rotation_quaternion',frame=i*.5)
   if n=='B_Pelvis' or n=='Axe' or n.startswith('Skirt_'):pb.keyframe_insert('location',frame=i*.5)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=(len(rows)-1)*.5
 for lay in a.layers:
  for st in lay.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
act(bpy.data.actions['Standing']);sc.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/gated_master.blend'));(P/'review/final_motion_floor.json').write_text(json.dumps(floor,indent=2))
print('FINAL MOTIONS',{nm:(len(rows)-1)/60 for nm,rows in poses.items()})
