"""Actual surface contact checks at 48 Hz, in metres; attached grip and strap contacts are separate."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/contact_master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;FPS=sc.render.fps
co=np.array([tuple(v.co)for v in body.data.vertices]);pv=np.array([d.value for d in body.data.attributes['piece'].data]);body.data.calc_loop_triangles();tri=np.array([list(t.vertices)for t in body.data.loop_triangles]);skintri=tri[np.all(pv[tri]==0,axis=1)]
clothtri=tri[np.all(np.isin(pv[tri],[1,10]),axis=1)&(np.max(co[tri,2],axis=1)<.93)]
bary=np.array([[1,0,0],[0,1,0],[0,0,1],[.5,.5,0],[.5,0,.5],[0,.5,.5],[1/3]*3])
def vertices(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=np.empty((len(me.vertices),3));me.vertices.foreach_get('co',v.ravel());ev.to_mesh_clear();return v
RAYS=[Vector(d).normalized() for d in [(1,.173,.231),(-.231,1,.173),(.173,-.231,1)]]
def inside(tree,p):
 votes=0
 for direction in RAYS:
  origin=p+direction*.000003;count=0
  for _ in range(30):
   hit,n,idx,dist=tree.ray_cast(origin,direction,5.0)
   if hit is None:break
   count+=1;origin=hit+direction*.00002
  votes+=count%2
 return votes>=2
def penetration(tree,points):
 worst=0;where=None
 for p in points:
  q,n,idx,d=tree.find_nearest(Vector(p))
  if q is not None and (Vector(p)-q).dot(n)<-.00001 and d>worst and inside(tree,Vector(p)):worst=d;where=p.tolist()
 return worst,where
props={}
for name in ['Spear','Buckler']:
 ob=bpy.data.objects[name+'Mesh'];local=np.array([tuple(rig.data.bones[name].matrix_local.inverted()@v.co)for v in ob.data.vertices]);ob.data.calc_loop_triangles();tt=np.array([list(t.vertices)for t in ob.data.loop_triangles])
 if name=='Spear':tt=tt[np.all(np.abs(local[tt,2])>.15,axis=1)]
 else:tt=tt[np.all(local[tt,1]<.021,axis=1)]
 props[name]=(ob,tt)
report={}
for act in bpy.data.actions:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];row={'cloth_penetration_m':0,'spear_body_penetration_m':0,'buckler_shell_penetration_m':0,'body_min_z':1e9,'prop_min_z':1e9};sample=[]
 for f in np.arange(0,act.frame_range[1]+.0001,FPS/48):
  sc.frame_set(int(f),subframe=float(f-int(f)));v=vertices(body);tree=BVHTree.FromPolygons([Vector(p)for p in v],skintri.tolist(),all_triangles=True);pts=np.einsum('kj,tjd->tkd',bary,v[clothtri]).reshape(-1,3);d,where=penetration(tree,pts)
  if d>row['cloth_penetration_m']:row.update(cloth_penetration_m=d,cloth_frame=float(f),cloth_point=where)
  row['body_min_z']=min(row['body_min_z'],float(v[pv==0,2].min()))
  for name,(ob,tt)in props.items():
   vp=vertices(ob);pts=np.einsum('kj,tjd->tkd',bary,vp[tt]).reshape(-1,3);d,where=penetration(tree,pts);key='spear_body_penetration_m' if name=='Spear' else 'buckler_shell_penetration_m'
   if d>row[key]:row[key]=d;row[key+'_frame']=float(f);row[key+'_point']=where
   row['prop_min_z']=min(row['prop_min_z'],float(vp[:,2].min()))
 report[act.name]=row;print('CONTACT',act.name,row,flush=True)
(P/'review/contact_audit.json').write_text(json.dumps({'sample_hz':48,'cloth_samples':'all lower-panel triangle vertices, edge midpoints and centroids against signed skin BVH','grip_exclusion_m':.15,'buckler_shell_only':True,'clips':report},indent=2))
