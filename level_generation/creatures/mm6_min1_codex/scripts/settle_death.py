"""Mirror the source forward fall into the native backward collapse; settle the back on the floor."""
import bpy,math,json
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/pre_settle.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;a=bpy.data.actions['Death'];rows=[]
r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
for f in range(int(a.frame_range[1])+1):
 sc.frame_set(f);rows.append({n:(p.rotation_quaternion.copy(),p.location.copy()) for n,p in r.pose.bones.items()})
new=[]
for f,row in enumerate(rows):
 r.animation_data.action=None
 for n,(q,l) in row.items():r.pose.bones[n].rotation_quaternion=q;r.pose.bones[n].location=l
 bpy.context.view_layer.update();axe=r.pose.bones['Axe'].matrix.copy();root=r.pose.bones['B_Pelvis'];direction=(r.pose.bones['B_Neck'].head-root.head).normalized();horizontal=Vector((direction.x,direction.y,0));axis=Vector((0,0,1)).cross(horizontal).normalized();theta=math.atan2(horizontal.length,direction.z);u=min(1,max(0,(f-4)/8));u=u*u*(3-2*u);m=root.matrix.copy();pos=m.translation.copy();m=Matrix.Rotation(-2*theta*u,4,axis)@m;m.translation=pos;root.matrix=m;bpy.context.view_layer.update()
 ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low=min(v.co.z for v in me.vertices);ev.to_mesh_clear();m=root.matrix.copy();m.translation.z-=low;root.matrix=m;bpy.context.view_layer.update();
 if f>=6:r.pose.bones['Axe'].matrix=axe
 bpy.context.view_layer.update();new.append({n:(p.rotation_quaternion.copy(),p.location.copy()) for n,p in r.pose.bones.items()})
for nm,frames in [('Death',list(enumerate(new))),('Dead',[(0,new[-1]),(30,new[-1])])]:
 
 if nm=='Dead':
  r.animation_data.action=None;bpy.data.actions.remove(bpy.data.actions['Dead']);act=bpy.data.actions.new('Dead');act.use_fake_user=True;act.use_frame_range=True;act.frame_start=0;act.frame_end=30
 else:act=bpy.data.actions[nm]
 r.animation_data.action=act
 if len(act.slots):r.animation_data.action_slot=act.slots[0]
 previous={}
 for f,row in frames:
  for n,(q,l) in row.items():
   if n in previous and q.dot(previous[n])<0:q=-q
   pb=r.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;previous[n]=q;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
for nm in ['Death','Dead']:
 for lay in bpy.data.actions[nm].layers:
  for strip in lay.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
for out in ['gated_master.blend','uv_master.blend']:bpy.ops.wm.save_as_mainfile(filepath=str(P/'work'/out))
