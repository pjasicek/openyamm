"""Finish head clearance with small constant fitting offsets and inspect actual cloth/skin contact."""
from pathlib import Path
import bpy,sys,math,json,numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));from g6_head_clearance import Clearance
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v12.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;c=Clearance(body);report={}
def turn(n,axis,angle):
 pb=rig.pose.bones[n];h=pb.head.copy();pb.matrix=Matrix.Translation(h)@Matrix.Rotation(angle,4,axis)@Matrix.Translation(-h)@pb.matrix;bpy.context.view_layer.update()
def apply(pose,offset):
 for n,(q,l) in pose.items():
  pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l
 bpy.context.view_layer.update();pb=rig.pose.bones['B_Head'];m=pb.matrix.copy()
 deformation=m.to_3x3()@rig.data.bones['B_Head'].matrix_local.to_3x3().inverted()
 m.translation+=deformation@Vector(offset);pb.matrix=m;bpy.context.view_layer.update()
for name in ['Attack','Death']:
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];poses=[]
 for f in range(int(act.frame_range[1])+1):
  sc.frame_set(f);poses.append({b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones})
 rig.animation_data.action=None;probes=[]
 candidates=[(0,y,z) for y in [0,.01,-.01,.02,-.02,.03,-.03,.035,.04] for z in [0,.01,.02,.03]]
 for offset in sorted(candidates,key=lambda v:sum(x*x for x in v)):
  worst=0
  for pose in poses:apply(pose,offset);worst=max(worst,c.measure()[0])
  probes.append((offset,worst));print('FINAL_HEAD_PROBE',name,offset,worst,flush=True)
  if worst<.01:break
 best=min(probes,key=lambda r:(r[1]>.01,sum(x*x for x in r[0]) if r[1]<.01 else r[1]));assert best[1]<.01,(name,probes)
 out=[]
 for pose in poses:
  apply(pose,best[0]);out.append({n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in ['B_Neck','B_Head']})
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 for f,pose in enumerate(out):
  for n,(q,l) in pose.items():
   pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
 report[name]={'head_fit_offset_rest_m':best[0],'max_head_depth_m':best[1]}
# Refresh the held library endpoint.
a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(int(a.frame_range[1]));held={b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones}
bpy.data.actions.remove(bpy.data.actions['Dead']);a=bpy.data.actions.new('Dead');a.use_fake_user=True;rig.animation_data.action=a
for f in [0,30]:
 for n,(q,l) in held.items():
  pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
# Direct cloth-against-skin check complements the older skin-side approximation at free cloth edges.
me=body.data;pv=me.attributes['piece'];skin=[tuple(f.vertices) for f in me.polygons if all(pv.data[i].value==0 for i in f.vertices)];cloth=[f for f in me.polygons if pv.data[f.vertices[0]].value in [14,19]]
for name in ['Standing','Running','Death','Dead']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];worst=(0,None,None)
 for f in range(int(a.frame_range[1])+1):
  sc.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=[v.co.copy() for v in m.vertices];ev.to_mesh_clear();tree=BVHTree.FromPolygons(co,skin)
  for face in cloth:
   pts=[co[i] for i in face.vertices];pts.append(sum(pts,Vector())/len(pts))
   for v in pts:
    loc,n,fi,d=tree.find_nearest(v,.05)
    if loc is not None and d>worst[0] and (v-loc).dot(n)<-.707*d:worst=(d,f,int(pv.data[face.vertices[0]].value))
 print('DIRECT_CLOTH_SKIN',name,worst);report[name]=dict(report.get(name,{}),cloth_depth_m=worst[0],cloth_frame=worst[1])
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v13.blend'));(p/'revision_02/motion/final_fit.json').write_text(json.dumps(report,indent=2)+'\n')
