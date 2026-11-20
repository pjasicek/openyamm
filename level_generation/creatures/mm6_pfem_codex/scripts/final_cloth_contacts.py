"""Check hidden leg surfaces against the outer dress, including half frames."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/reduced.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];m=o.data;sc=bpy.context.scene
pv=np.array([x.value for x in m.attributes['piece'].data]);rest=np.array([v.co[:] for v in m.vertices])
skin=np.flatnonzero(np.isin(pv,[8,10])&(rest[:,2]>.35)&(rest[:,2]<.92))
polys=[]
for f in m.polygons:
 if all(pv[i]==100 for i in f.vertices):
  c=f.center;rad=Vector((c.x,c.y,0))
  polys.append(tuple(f.vertices))
report={}
for name in ('Standing','Walking','Hit','Death','Fidget'):
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 worst=(0,None,None);floor=(10,None)
 for f in np.arange(0,a.frame_range[1]+.01,.5):
  sc.frame_set(int(f),subframe=float(f%1));ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh()
  P=np.array([v.co[:] for v in mm.vertices]);ev.to_mesh_clear()
  tree=BVHTree.FromPolygons(P.tolist(),polys)
  for i in skin:
   # Pleat normals alone misclassify enclosed skin. Compare with the outermost
   # intersection along the ray from the paired-leg centreline to the skin.
   u=float(np.clip((rest[i,2]-.09)/(.515-.09),0,1))
   centre=sum((r.pose.bones[f'B_{side}_Foot'].head.lerp(r.pose.bones[f'B_{side}_Calf'].head,u) for side in 'LR'),Vector())*.5
   d=Vector(P[i])-centre;length=d.length
   if length<1e-6:continue
   direction=d/length;distance=0.;outer=None
   for hit in range(20):
    loc,no,fi,dist=tree.ray_cast(centre+direction*(distance+.00001),direction,.8-distance)
    if loc is None:break
    distance=(loc-centre).length;outer=distance
   if outer is not None:
    depth=length-outer
    if depth>.002 and depth>worst[0]:worst=(float(depth),float(f),int(i))
  z=float(P[:,2].min())
  if z<floor[0]:floor=(z,float(f))
 report[name]={'leg_through_outer_cloth':worst,'whole_mesh_min_z':floor}
 print('FINAL CLOTH CONTACT',name,report[name])
common.workbench_clay(sc)
for name,f in [('Standing',0),('Walking',6),('Walking',18),('Hit',5),('Death',40),('Death',48),('Death',71)]:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(f)
 lo,hi=common.world_bounds([o]);c=(lo+hi)*.5
 common.render_views(str(p/f'review/reduced_{name}_{f}'),c.z,max(hi-lo)*1.3,views=('front','left','three_quarter'),resolution=(900,800),target=(c.x,c.y))
(p/'work/reduced_cloth_contacts.json').write_text(json.dumps(report,indent=2))
