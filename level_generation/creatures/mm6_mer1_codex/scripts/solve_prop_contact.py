import bpy,numpy as np,json,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];prop=bpy.data.objects['ClubMesh'];s=bpy.context.scene;faces=[tuple(f.vertices)for f in body.data.polygons];B=r.data.bones['Club'];axis=(B.tail_local-B.head_local).normalized();ids=[v.index for v in prop.data.vertices if (v.co-B.head_local).dot(axis)>.065]
def coords(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=[o.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear();return co
report={}
for role in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];keys=[];worst=0
 # Sample first, before adding corrections, to avoid cumulative key interpolation.
 for f in np.arange(0,float(a.frame_range[1])+.001,.25):
  s.frame_set(int(f),subframe=float(f%1));co=coords(body);pc=coords(prop);tree=BVHTree.FromPolygons(co,faces);delta=Vector((0,0,0));M=r.pose.bones['Club'].matrix.copy()
  for iteration in range(60):
   corrections=[]
   for i in ids:
    pos=pc[i]+delta;loc,n,fi,d=tree.find_nearest(pos,.12)
    if loc is not None and (pos-loc).dot(n)<-.7*d:corrections.append((d,n))
   if not corrections:break
   d,n=max(corrections,key=lambda x:x[0]);delta+=n*(d+.003)
   low=min(v.z for v in pc)+delta.z
   if low<.004:delta.z+=.004-low
  M.translation+=delta;worst=max(worst,delta.length);keys.append((float(f),M))
 pb=r.pose.bones['Club'];previous=None
 for f,M in keys:
  s.frame_set(int(f),subframe=f%1);pb.matrix=M;q=pb.rotation_quaternion.copy()
  if previous is not None and q.dot(previous)<0:q=-q
  previous=q;pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
 for curve in a.layers[0].strips[0].channelbag(a.slots[0]).fcurves:
  for k in curve.keyframe_points:k.interpolation='LINEAR'
 report[role]={'maximum_prop_translation_mm':worst*1000};print('PROP SOLVE',role,report[role],flush=True)
(P/'review/prop_contact_corrections.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/prop_clear.blend'))
