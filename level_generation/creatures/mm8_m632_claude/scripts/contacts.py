"""Half-frame surface contacts. Close only diagnostic skin cuts; open armour uses proximity."""
import os,bpy,bmesh,sys,json
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/os.environ.get('M632_CHECK_BLEND','work/motion_native.blend')))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];prop=bpy.data.objects['Crossbow'];me=body.data;sc=bpy.context.scene
pv=np.array([v.value for v in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups]
weights=np.zeros((len(me.vertices),len(names)))
for v in me.vertices:
 for g in v.groups:weights[v.index,g.group]=g.weight
def region(s,parts):return weights[:,[i for i,n in enumerate(names) if n.startswith('B_'+s+'_') and any(p in n for p in parts)]].sum(1)
arms={s:region(s,('Clavicle','UpperArm','Forearm','Hand','Finger'))>.2 for s in 'LR'}
samples={s:region(s,('Forearm','Hand','Finger'))>.5 for s in 'LR'}
caps=[]
def closed_faces(keep):
 bm=bmesh.new();bm.from_mesh(me);idx=bm.verts.layers.int.new('original_index')
 for v in bm.verts:v[idx]=v.index
 bmesh.ops.delete(bm,geom=[f for f in bm.faces if not all(keep[v[idx]] for v in f.verts)],context='FACES')
 boundary=[e for e in bm.edges if e.is_boundary]
 bmesh.ops.holes_fill(bm,edges=boundary,sides=0);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 boundary=[e for e in bm.edges if e.is_boundary]
 if boundary:
  adjacency={}
  for e in boundary:
   a,b=e.verts;adjacency.setdefault(a,set()).add(b);adjacency.setdefault(b,set()).add(a)
  seen=set()
  for start in adjacency:
   if start in seen:continue
   todo=[start];group=set()
   while todo:
    v=todo.pop()
    if v in group:continue
    group.add(v);todo.extend(adjacency[v]-group)
   seen|=group
   indices=[v[idx] for v in group];center=bm.verts.new(sum((v.co for v in group),Vector())/len(group))
   center[idx]=len(me.vertices)+len(caps);caps.append(indices)
   for e in boundary:
    if e.verts[0] in group:
     a,b=e.verts
     bm.faces.new((a,b,center))
  bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 assert not any(e.is_boundary for e in bm.edges),'Diagnostic skin cap incomplete'
 faces=[tuple(v[idx] for v in f.verts) for f in bm.faces];bm.free();return faces
skin=np.isin(pv,(0,5,12,14))
closed={'prop':closed_faces(skin),**{s:closed_faces(skin&~arms[s]) for s in 'LR'}}
beard=closed_faces(np.isin(pv,(1,2,3,6,10,13)))
shells=[tuple(p.vertices) for p in me.polygons if not skin[p.vertices[0]] and pv[p.vertices[0]] not in (7,8)]
def coords(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();c=np.array([tuple(o.matrix_world@v.co) for v in m.vertices]);ev.to_mesh_clear();return c
prop_edges=np.array([e.vertices[:] for e in prop.data.edges])
def inside(tree, point):
 # Nearest-face normals alone misclassify points beside a concave shoulder cut.
 votes=0
 for direction in (Vector((1,.137,.229)).normalized(),Vector((.213,1,.173)).normalized(),Vector((.179,.239,1)).normalized()):
  origin=Vector(point);hits=0
  for _ in range(64):
   loc,normal,index,d=tree.ray_cast(origin,direction,5)
   if loc is None:break
   hits+=1;origin=loc+direction*.00001
  else:raise AssertionError('Contact ray did not leave the skin')
  votes+=hits%2
 return votes>=2
report={}
for name in ('Standing','Walking','Running','Attack','Hit','Death','Fidget','Dead'):
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 worst={};floors=[]
 for f in np.arange(a.frame_range[0],a.frame_range[1]+.001,sc.render.fps/120):
  sc.frame_set(int(f),subframe=float(f-int(f)));pts=coords(body);weapon=coords(prop)
  weapon=np.vstack([weapon,(weapon[prop_edges[:,0]]+weapon[prop_edges[:,1]])*.5])
  floors.append((float(f),float(pts[:,2].min()),float(weapon[:,2].min())))
  for label,mask in [('prop',weapon),('L',pts[samples['L']]),('R',pts[samples['R']])]:
   for kind,faces in [('skin',closed[label]),('hair',beard)]:
    tree=BVHTree.FromPolygons(np.vstack([pts,*[pts[ids].mean(0)[None,:] for ids in caps]]).tolist(),faces)
    for point in mask:
     loc,norm,index,d=tree.find_nearest(Vector(point),.12)
     if loc is not None and d>.001 and (Vector(point)-loc).dot(norm)<-.75*d:
      key=label+'_'+kind
      if d>worst.get(key,{}).get('depth_m',0) and inside(tree,point):worst[key]={'depth_m':float(d),'frame':float(f),'point':point.tolist(),'piece':int(pv[next(v for v in faces[index] if v<len(pv))])}
  tree=BVHTree.FromPolygons(pts.tolist(),shells);near=0
  for point in weapon:
   if tree.find_nearest(Vector(point),.002)[0] is not None:near+=1
  if near>worst.get('prop_shell_proximity',{}).get('samples',0):worst['prop_shell_proximity']={'samples':near,'frame':float(f)}
 report[name]={'contacts':worst,'floor_min':{'body':min(x[1] for x in floors),'prop':min(x[2] for x in floors)},'body_floor_max':max(x[1] for x in floors)}
 print('CONTACT',name,report[name],flush=True)
(P/'work/contacts.json').write_text(json.dumps(report,indent=2))
