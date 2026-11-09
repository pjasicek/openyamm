"""Contact checks on the exported/reimported surface at frame and half-frame times."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/roundtrip.blend'))
o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];sc=bpy.context.scene;m=o.data
pv=np.array([x.value for x in m.attributes['piece'].data]);rest=np.array([tuple(v.co) for v in m.vertices])
cloth=[tuple(f.vertices) for f in m.polygons if all(pv[i]==100 for i in f.vertices)]
neck=[tuple(f.vertices) for f in m.polygons if all(pv[i]==1 for i in f.vertices)]
hands=np.flatnonzero(np.isin(pv,[3,4,9,11]))
braid=np.flatnonzero((pv==19)&(rest[:,2]<1.43))
report={}
for name in ('Standing','Walking','Hit','Death','Dead','Fidget'):
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 worst_hand=(0,None,None);worst_braid=(0,None,None)
 for f in np.arange(0,a.frame_range[1]+.01,.5):
  sc.frame_set(int(f),subframe=float(f%1));ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh()
  V=np.array([tuple(o.matrix_world@v.co) for v in mm.vertices]);ev.to_mesh_clear()
  tree=BVHTree.FromPolygons(V.tolist(),cloth)
  waist=sum((r.matrix_world@r.pose.bones['B_'+s+'_Thigh'].head for s in 'LR'),Vector())*.5
  knee=sum((r.matrix_world@r.pose.bones['B_'+s+'_Calf'].head for s in 'LR'),Vector())*.5
  ankle=sum((r.matrix_world@r.pose.bones['B_'+s+'_Foot'].head for s in 'LR'),Vector())*.5
  for i in hands:
   x=Vector(V[i]);axis=knee-waist;u=(x-waist).dot(axis)/axis.length_squared
   if u<-.08 or u>1.5:continue
   center=waist+axis*max(0.,min(1.,u));d=x-center;length=d.length
   if length<.01:continue
   direction=d/length;distance=0.;outer=None
   for hit in range(16):
    loc,n,fi,dist=tree.ray_cast(center+direction*(distance+.00001),direction,.9-distance)
    if loc is None:break
    distance=(loc-center).length;outer=distance
   if outer is not None:
    depth=outer-length
    if depth>.002 and depth>worst_hand[0]:worst_hand=(float(depth),float(f),int(i))
  tree=BVHTree.FromPolygons(V.tolist(),neck)
  for i in braid:
   loc,n,fi,d=tree.find_nearest(Vector(V[i]))
   depth=-(Vector(V[i])-loc).dot(n)
   if depth>.002 and d<.06 and depth>worst_braid[0]:worst_braid=(float(depth),float(f),int(i))
 report[name]={'arm_inside_skirt_m':worst_hand,'braid_inside_neck_m':worst_braid}
 print('EXPORTED CONTACTS',name,report[name])
(p/'work/exported_contacts.json').write_text(json.dumps(report,indent=2))
