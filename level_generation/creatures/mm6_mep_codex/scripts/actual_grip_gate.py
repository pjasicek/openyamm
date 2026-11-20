"""Actual staff triangle samples against the hand surface at 48 Hz, including reduced props."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];report={}
def inside(tree,v):
 direction=Vector((.811,.357,.463)).normalized();count=0;origin=v.copy()
 for _ in range(64):
  hit=tree.ray_cast(origin,direction,2)[0]
  if hit is None:return count%2==1
  count+=1;origin=hit+direction*.00001
 raise AssertionError('unresolved hand ray')
def solid_inside(triangles,point):
 q=triangles-np.array(point);a,b,c=q[:,0],q[:,1],q[:,2];la,lb,lc=np.linalg.norm(a,axis=1),np.linalg.norm(b,axis=1),np.linalg.norm(c,axis=1);numerator=np.einsum('ij,ij->i',a,np.cross(b,c));denominator=la*lb*lc+np.einsum('ij,ij->i',a,b)*lc+np.einsum('ij,ij->i',b,c)*la+np.einsum('ij,ij->i',c,a)*lb
 return abs(float(np.arctan2(numerator,denominator).sum()*2))>2*np.pi
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(p/f'work/final_lod{level}.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];sc=bpy.context.scene;pv=np.array([x.value for x in b.data.attributes['piece'].data]);inv=r.data.bones['Staff'].matrix_local.inverted();rest=np.array([inv@v.co for v in b.data.vertices]);faces=[tuple(f.vertices) for f in b.data.polygons if all(pv[i]==3 for i in f.vertices)];staff_faces=[tuple(f.vertices) for f in b.data.polygons if all(pv[i]==100 for i in f.vertices)];staff=[i for i in range(len(pv)) if pv[i]==100 and abs(rest[i,1])<.055];edges=[tuple(e.vertices) for e in b.data.edges if all(i in staff for i in e.vertices)];assert staff
 b.data.calc_loop_triangles();staff_triangles=[tuple(t.vertices) for t in b.data.loop_triangles if all(pv[i]==100 for i in t.vertices)];result={}
 for a in bpy.data.actions:
  if not a.use_fake_user or a.name=='Dead':continue
  r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];gaps=[];penetration=0.;count=0
  for t in sorted(set(list(np.arange(0,float(a.frame_range[1])/30+.00001,1/48))+[float(a.frame_range[1])/30])):
   if a.name=='Death' and t>=.15:continue
   f=t*30;sc.frame_set(int(f),subframe=f%1);ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();coords=[v.co.copy() for v in me.vertices];ev.to_mesh_clear();tree=BVHTree.FromPolygons(coords,faces);points=[coords[i] for i in staff]+[(coords[i]+coords[j])/2 for i,j in edges];dist=[]
   for point in points:
    hit,normal,index,d=tree.find_nearest(point);dist.append(d)
    if (point-hit).dot(normal)<0 and d<.015 and inside(tree,point):penetration=max(penetration,d*1000)
   # Check both surfaces: a low-LOD shaft may have no vertex at the nearest contact point.
   stree=BVHTree.FromPolygons(coords,staff_faces);triangles=np.array(coords)[staff_triangles];inv_pose=r.pose.bones['Staff'].matrix.inverted()
   for i in np.where(pv==3)[0]:
    if abs((inv_pose@coords[i]).y)<.055:
     point=coords[i];hit,normal,index,d=stree.find_nearest(point);dist.append(d)
     if (point-hit).dot(normal)<0 and d<.015 and solid_inside(triangles,point):penetration=max(penetration,d*1000)
   gaps.append(min(dist)*1000);count+=1
  result[a.name]={'samples_48hz':count,'max_nearest_surface_gap_mm':max(gaps),'worst_penetration_mm':penetration,'pass':max(gaps)<=3 and penetration<=3}
 report[level]=result;print('ACTUAL_GRIP',level,result,flush=True)
(p/'review/actual_grip_gate.json').write_text(json.dumps(report,indent=2));assert all(row['pass'] for vals in report.values() for row in vals.values())
