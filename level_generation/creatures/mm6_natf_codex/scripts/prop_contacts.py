import bpy,json,sys,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/gate_master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;props=[bpy.data.objects[n]for n in ['ForearmBlade','LeafShield']];me=body.data;part=np.array([a.value for a in me.attributes['piece'].data]);co=np.array([tuple(v.co)for v in me.vertices]);bodyfaces=[tuple(p.vertices)for p in me.polygons if part[p.vertices[0]] in [0,1,3,5]]
facepart=[int(part[f[0]])for f in bodyfaces]
def inside(tree,p):
 votes=0
 for d in [Vector((1,.113,.053)).normalized(),Vector((-.327,1,.073)).normalized(),Vector((.613,-1,-.051)).normalized()]:
  q=p.copy();count=0
  for k in range(40):
   hit,n,j,dist=tree.ray_cast(q,d,5)
   if hit is None:break
   count+=1;q=hit+d*.00001
  votes+=count%2
 return votes>=2
# Only the blade beyond its straps is a weapon surface. Mounts intentionally contact the forearm.
locals={o.name:np.array([tuple(rig.data.bones[o.name].matrix_local.inverted()@v.co)for v in o.data.vertices])for o in props};report={};trace=[]
for role in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']:
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];row={o.name:{'floor_min_m':100,'body_penetration_mm':0}for o in props}
 for f in np.arange(0,a.frame_range[1]+.001,sc.render.fps/48):
  sc.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();c=[v.co.copy()for v in mesh.vertices];ev.to_mesh_clear();tree=BVHTree.FromPolygons(c,bodyfaces);trees={k:BVHTree.FromPolygons(c,[face for face,pp in zip(bodyfaces,facepart)if pp==k])for k in [0,1,3,5]}
  for ob in props:
   ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();points=np.array([tuple(v.co)for v in mm.vertices]);ev.to_mesh_clear();dd=row[ob.name];dd['floor_min_m']=min(dd['floor_min_m'],float(points[:,2].min()));loc=locals[ob.name];ids=np.where(loc[:,2]>.19)[0]if ob.name=='ForearmBlade'else np.where(loc[:,1]<.014)[0]
   for i in ids:
    hit,n,faceid,dist=tree.find_nearest(Vector(points[i]));v=Vector(points[i])-hit;signed=v.dot(n)
    if signed<-.0001 and -signed>v.length*.707 and -signed*1000>dd['body_penetration_mm'] and inside(trees[facepart[faceid]],Vector(points[i])):dd.update(body_penetration_mm=-signed*1000,seconds=float(f/sc.render.fps),vertex=int(i),point=points[i].tolist())
  if role=='Attack':
   M=rig.pose.bones['ForearmBlade'].matrix;trace.append({'t':float(f/sc.render.fps),'M':[list(r)for r in M]})
 report[role]=row;print('PROPCONTACT',role,row,flush=True)
(P/'review/prop_contacts.json').write_text(json.dumps(report,indent=2));(P/'work/blade_trace.json').write_text(json.dumps(trace))
