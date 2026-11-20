"""Closed anatomical proxy contact checks; garment proximity is reported separately."""
from pathlib import Path
import bpy,bmesh,sys,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated.blend'));r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data
rest=np.array([v.co[:] for v in me.vertices]);piece=np.array([d.value for d in me.attributes['piece'].data]);gn=[g.name for g in o.vertex_groups];wt=np.zeros((len(rest),len(gn)))
for v in me.vertices:
 for g in v.groups:wt[v.index,g.group]=g.weight
arm={s:wt[:,[i for i,n in enumerate(gn) if n.startswith(f'B_{s}_') and any(t in n for t in ['Clavicle','UpperArm','Forearm','Hand','Finger'])]].sum(1)>.2 for s in 'RL'}
samples={s:wt[:,[i for i,n in enumerate(gn) if n.startswith(f'B_{s}_') and any(t in n for t in ['Forearm','Hand','Finger'])]].sum(1)>.5 for s in 'RL'}
faces=[tuple(p.vertices) for p in me.polygons];proxies={};caps={}
for s in 'RL':
 proxies[s]=[];caps[s]=[]
 for part in [0,1,2,3,4,6,7]:
  fl=[f for f in faces if piece[f[0]]==part and not any(arm[s][i] for i in f)]
  if not fl:continue
  bm=bmesh.new();ids=sorted({i for f in fl for i in f});idmap=bm.verts.layers.int.new('source');vs={}
  for i in ids:v=bm.verts.new(rest[i]);v[idmap]=i;vs[i]=v
  for f in fl:bm.faces.new([vs[i] for i in f])
  before=len(bm.faces);bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
  closed=all(e.is_manifold for e in bm.edges);caps[s].append({'piece':part,'closure_faces':len(bm.faces)-before,'closed':closed})
  if closed:proxies[s].append((part,[tuple(v[idmap] for v in f.verts) for f in bm.faces]))
  bm.free()
def inside(tree,p):
 votes=0
 for d in [Vector((1,.271,.137)).normalized(),Vector((-.193,1,.317)).normalized(),Vector((.239,.173,1)).normalized()]:
  start=Vector(p);n=0
  for _ in range(48):
   hit,_,_,_=tree.ray_cast(start,d,10)
   if hit is None:break
   n+=1;start=hit+d*.00001
  votes+=n%2
 return votes>=2
E=np.array([tuple(e.vertices) for e in me.edges]);length=np.maximum(np.linalg.norm(rest[E[:,0]]-rest[E[:,1]],axis=1),1e-6);report={}
for name in ['Standing','Walking','Running','Attack','Hit','Death','Fidget']:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];worst={};edge={}
 for f in np.arange(0,float(a.frame_range[1])+.001,2):
  bpy.context.scene.frame_set(int(f));ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear()
  rat=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1)/length
  for part in np.unique(piece):
   inds=np.where(piece[E[:,0]]==part)[0];k=inds[rat[inds].argmax()]
   if rat[k]>edge.get(str(part),[0])[0]:edge[str(part)]=[float(rat[k]),float(f),E[k].tolist()]
  for s in 'RL':
   pts=co[samples[s]]
   for part,fl in proxies[s]:
    tree=BVHTree.FromPolygons(co,fl);key=f'{s}_into_{part}'
    for point in pts:
     hit,norm,idx,dist=tree.find_nearest(Vector(point),.06)
     if hit is not None and dist>.001 and dist>worst.get(key,[0])[0] and (Vector(point)-hit).dot(norm)<-.7*dist and inside(tree,point):worst[key]=[float(dist),float(f),point.tolist()]
 report[name]={'contacts_m':worst,'piece_edge_stretch':edge};print('SURFACE',name,worst,flush=True)
(P/'work/surface_checks.json').write_text(json.dumps({'proxies':caps,'roles':report},indent=2))
