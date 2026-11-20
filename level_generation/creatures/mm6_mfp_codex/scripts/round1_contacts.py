"""Fit the existing finger pads to the handle surface without adding or reducing triangles."""
import bpy,numpy as np,json,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];report={}
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/round1/lod{level}.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];k=bpy.data.objects['KnifeAsset'];sc=bpy.context.scene
 r.animation_data.action=bpy.data.actions['Attack'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0);bpy.context.view_layer.update();ev=k.evaluated_get(bpy.context.evaluated_depsgraph_get());km=ev.to_mesh();tree=BVHTree.FromPolygons([v.co[:]for v in km.vertices],[list(f.vertices)for f in km.polygons]);ev.to_mesh_clear()
 gn={g.index:g.name for g in b.vertex_groups};mats={n:pb.matrix@r.data.bones[n].matrix_local.inverted()for n,pb in r.pose.bones.items()};rest=np.array([v.co[:]for v in b.data.vertices]);handids=[v.index for v in b.data.vertices if sum(g.weight for g in v.groups if gn[g.group].startswith('B_R_Hand')or gn[g.group].startswith('B_R_Finger'))>.5]; transforms={}
 for i in handids:
  v=b.data.vertices[i];M=sum((np.array(mats[gn[g.group]])*g.weight for g in v.groups if gn[g.group]in mats),np.zeros((4,4)));transforms[i]=Matrix(M)
 # Move penetrating pads to the actual handle surface; leave a small contact clearance.
 for repeat in range(3):
  for i,M in transforms.items():
   v=b.data.vertices[i];pnt=M@v.co;near,norm,face,d=tree.find_nearest(pnt)
   if near is not None and d<.008 and (pnt-near).dot(norm)<-.0005:v.co=M.inverted()@(near+norm*.0006)
  # The nearest existing pad of every digit closes the remaining gap; neighbours make a smooth local correction.
  for digit in range(5):
   ids=[i for i in handids if sum(g.weight for g in b.data.vertices[i].groups if gn[g.group].startswith(f'B_R_Finger{digit}'))>.3]
   opts=[]
   for i in ids:
    pnt=transforms[i]@b.data.vertices[i].co;near,norm,face,d=tree.find_nearest(pnt);opts.append((d,i,near,norm))
   if not opts:continue
   d,i,near,norm=min(opts,key=lambda x:x[0])
   if d<=.001:continue
   old=b.data.vertices[i].co.copy();target=transforms[i].inverted()@(near+norm*.0007);delta=target-old
   if delta.length>.010:delta*=.010/delta.length
   for j in ids:
    distance=(b.data.vertices[j].co-old).length;w=math.exp(-.5*(distance/.009)**2)
    b.data.vertices[j].co+=delta*w
 for i in handids:
  v=b.data.vertices[i];delta=v.co-Vector(rest[i]);limit=.010 if level==3 else .006
  if delta.length>limit:v.co=Vector(rest[i])+delta.normalized()*limit
 b.data.update()
 moved=np.linalg.norm(np.array([v.co[:]for v in b.data.vertices])-rest,axis=1);report[str(level)]={'pad_vertices_adjusted':int((moved>1e-6).sum()),'maximum_pad_adjustment_mm':float(moved.max()*1000)}
 # The coarse sole silhouettes inherited slight toe-out; align their existing geometry to the travelling feet.
 for v in b.data.vertices:
  if v.co.z>.085:continue
  if (level==2 and v.co.x<0)or(level==3 and v.co.x>0):
   side='R'if v.co.x<0 else'L';origin=r.data.bones[f'B_{side}_Foot'].head_local;angle=math.radians(4.5 if side=='R'else -2);v.co=origin+Matrix.Rotation(angle,3,'Z')@(v.co-origin)
  v.co.z+=.0005*max(0,min(1,(.085-v.co.z)/.03))
 for role in ['Attack','Hit']:
  factor=1.55 if role=='Attack'else 1.3;a=bpy.data.actions[role];end=float(a.frame_range[1]);start=float(a.frame_range[0])
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for key in fc.keyframe_points:
       for xy in [key.co,key.handle_left,key.handle_right]:xy.x*=factor
  a.frame_start=start*factor;a.frame_end=end*factor
 # Hold precisely the final fall pose.
 a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];end=float(a.frame_range[1]);sc.frame_set(int(end),subframe=end%1);held={n:(pb.rotation_quaternion.copy(),pb.location.copy(),pb.scale.copy())for n,pb in r.pose.bones.items()};r.animation_data.action=None;bpy.data.actions.remove(bpy.data.actions['Dead']);a=bpy.data.actions.new('Dead');a.use_fake_user=True;r.animation_data.action=a;a.use_frame_range=True;a.frame_start=0;a.frame_end=30
 for f in [0,30]:
  for n,(q,l,s)in held.items():
   pb=r.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.scale=s;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f);pb.keyframe_insert('scale',frame=f)
 r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/round1/lod{level}.blend'));print('CONTACTS',level,report[str(level)],flush=True)
(P/'review/round1/pad_fit.json').write_text(json.dumps(report,indent=2))
