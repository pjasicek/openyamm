"""Limit visible fabric strain in bone translation space, with body and floor constraints."""
import bpy,json,numpy as np,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
from volume_contact import inside
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v7p.blend'))
r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;sc=bpy.context.scene
assert np.max(abs(np.array(r.matrix_world)-np.eye(4)))<1e-5
assert np.max(abs(np.array(body.matrix_world)-np.eye(4)))<1e-5
groups=[json.loads(sc[n]) for n in ['nobl_cloak','nobl_tabard','nobl_skirt_back']]
chains=[c for group in groups for c in group];names=[n for c in chains for n in c['bones']];nb=len(names)
idx={n:i for i,n in enumerate(names)};vg={g.index:g.name for g in body.vertex_groups}
W=np.zeros((len(me.vertices),nb))
for v in me.vertices:
 for e in v.groups:
  if vg[e.group] in idx:W[v.index,idx[vg[e.group]]]=e.weight
pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
C=np.where(np.isin(pv,[0,8,9])&(W.sum(1)>.2))[0];cmask=np.zeros(len(W),bool);cmask[C]=True
E=np.array([tuple(e.vertices) for e in me.edges if cmask[e.vertices[0]] and cmask[e.vertices[1]]])
R=np.array([tuple(v.co) for v in me.vertices]);rl=np.linalg.norm(R[E[:,1]]-R[E[:,0]],axis=1)
target=np.minimum(rl*1.8,rl+.03)
DW=W[E[:,1]]-W[E[:,0]]
faces=[tuple(f.vertices) for f in me.polygons if all(pv[i] in [1,2,4,5,6,7,10,11,13,14,18,19,20,21,29,30,110] for i in f.vertices)]
reg=np.eye(nb)*.003
for c in chains:
 reg[idx[c['bones'][0]],idx[c['bones'][0]]]+=.05
 for a,b in zip(c['bones'],c['bones'][1:]):
  v=np.zeros(nb);v[idx[a]]=1;v[idx[b]]=-1;reg+=.015*np.outer(v,v)
for group in groups:
 order=sorted(group,key=lambda c:c['deg'])
 for a,b in zip(order,order[1:]):
  for na,nb_ in zip(a['bones'],b['bones']):
   v=np.zeros(nb);v[idx[na]]=1;v[idx[nb_]]=-1;reg+=.01*np.outer(v,v)
REG=np.kron(reg,np.eye(3))
report={}
for act in list(bpy.data.actions):
 if act.name not in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:continue
 r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];results=[]
 for f in range(int(act.frame_range[1])+1):
  sc.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
  P=np.array([tuple(v.co) for v in mesh.vertices]);ev.to_mesh_clear()
  original={n:r.pose.bones[n].matrix.copy() for n in names}
  tree=BVHTree.FromPolygons(P.tolist(),faces);delta=np.zeros((nb,3))
  rearfaces=[tuple(f.vertices) for f in me.polygons if all(pv[i]==8 for i in f.vertices)]
  reartree=BVHTree.FromPolygons(P.tolist(),rearfaces)
  initial=float(np.max(np.linalg.norm(P[E[:,1]]-P[E[:,0]],axis=1)-rl))
  for iteration in range(30):
   d=P[E[:,1]]-P[E[:,0]];length=np.linalg.norm(d,axis=1)
   bad=length>target+.001
   rows=[];rhs=[]
   if bad.any():
    unit=d[bad]/length[bad,None]
    rows.extend((DW[bad,:,None]*unit[:,None,:]).reshape(-1,nb*3))
    rhs.extend(target[bad]-length[bad])
   for i in C:
    if P[i,2]<.003:
     a=np.zeros((nb,3));a[:,2]=W[i];rows.append(a.ravel()*2);rhs.append((.003-P[i,2])*2)
    loc,normal,face,dist=tree.find_nearest(Vector(P[i]),.035)
    if loc is not None and dist>.001 and (Vector(P[i])-loc).dot(normal)<-.7*dist and inside(tree,P[i]):
     rows.append((W[i,:,None]*np.array(normal)[None,:]).ravel()*2);rhs.append((dist+.010)*2)
    elif loc is not None and dist<.008 and (Vector(P[i])-loc).dot(normal)>0:
     rows.append((W[i,:,None]*np.array(normal)[None,:]).ravel()*2);rhs.append((.008-dist)*2)
    if pv[i]==0:
     loc,normal,face,dist=reartree.find_nearest(Vector(P[i]),.005)
     if loc is not None and dist<.005:
      out=P[i,:2];out=out/max(np.linalg.norm(out),1e-6)
      direction=np.array([out[0],out[1],0.])
      rows.append((W[i,:,None]*direction[None,:]).ravel());rhs.append(.005-dist)
   if not rows:break
   A=np.array(rows);b=np.array(rhs)
   change=np.linalg.solve(A.T@A+REG,A.T@b).reshape(nb,3)*.8
   norm=np.linalg.norm(change,axis=1);change*=np.minimum(1,.025/np.maximum(norm,1e-9))[:,None]
   delta+=change;P+=W@change
   if np.max(np.linalg.norm(change,axis=1))<.0001:break
  desired={}
  for n in names:
   M=original[n].copy();M.translation+=Vector(delta[idx[n]]);desired[n]=M
  for n in names:
   pb=r.pose.bones[n];parent=pb.parent.name;pm=desired[parent] if parent in desired else r.pose.bones[parent].matrix
   mu=pm@r.data.bones[parent].matrix_local.inverted()@r.data.bones[n].matrix_local
   local=mu.inverted()@desired[n];pb.location=local.translation;pb.rotation_quaternion=local.to_quaternion()
   pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f)
  bpy.context.view_layer.update()
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();actual=np.array([tuple(v.co) for v in mesh.vertices]);ev.to_mesh_clear()
  error=float(np.max(np.linalg.norm(actual[C]-P[C],axis=1)))
  assert error<.0002,(act.name,f,error)
  final=float(np.max(np.linalg.norm(actual[E[:,1]]-actual[E[:,0]],axis=1)-rl))
  move=float(np.max(np.linalg.norm(delta,axis=1)))
  assert np.isfinite(actual).all() and move<.4,(act.name,f,move)
  results.append({'frame':f,'before_cm':initial*100,'after_cm':final*100,'max_bone_move_cm':move*100,'floor_cm':float(actual[C,2].min()*100)})
 report[act.name]=results
 print('STRAIN',act.name,'max growth cm',round(max(x['before_cm'] for x in results),2),'->',round(max(x['after_cm'] for x in results),2),'max bone move cm',round(max(x['max_bone_move_cm'] for x in results),2),flush=True)
(p/'work/cloth_strain_limit.json').write_text(json.dumps(report,indent=1))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v7s.blend'))
