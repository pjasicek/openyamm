"""Fit the retained cloth's rest shape to its library-driven motion envelope."""
from pathlib import Path
import bpy,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v13.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;me=body.data
piece=[x.value for x in me.attributes['piece'].data];ids=[v.index for v in me.vertices if piece[v.index] in (14,19)];idx={v:i for i,v in enumerate(ids)}
faces=[tuple(f.vertices) for f in me.polygons if all(piece[i]==0 for i in f.vertices)]
cf=[tuple(idx[i] for i in f.vertices) for f in me.polygons if piece[f.vertices[0]] in (14,19)]
rest=np.array([tuple(me.vertices[i].co) for i in ids]);sign=np.array([1 if piece[i]==14 else -1 for i in ids]);offset=np.zeros((len(ids),3));samples=[]
for name in ['Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for f in range(int(a.frame_range[1])+1):
  sc.frame_set(f);deps=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(deps);em=ev.to_mesh();co=[v.co.copy() for v in em.vertices];ev.to_mesh_clear();tree=BVHTree.FromPolygons(co,faces)
  mats={g.index:rig.pose.bones[g.name].matrix@rig.data.bones[g.name].matrix_local.inverted() for g in body.vertex_groups if g.name in rig.pose.bones}
  dirs=[];invs=[]
  for i in ids:
   v=me.vertices[i];d=sum((np.array(mats[g.group].to_3x3())*g.weight for g in v.groups),np.zeros((3,3)));dirs.append(d);invs.append(np.linalg.inv(d))
  samples.append((name,f,tree,np.array([tuple(co[i]) for i in ids]),np.array(dirs),np.array(invs)))
for iteration in range(18):
 demand=np.zeros((len(ids),3));severity=np.zeros(len(ids));worst=(0,None,None)
 for name,f,tree,co,dirs,invs in samples:
  posed=co+np.einsum("nij,nj->ni",dirs,offset)
  for face in cf:
   for local,weights in [(i,[(i,1)]) for i in face]+[(None,[(i,1/len(face)) for i in face])]:
    pos=sum((posed[i]*w for i,w in weights),np.zeros(3));loc,n,fi,d=tree.find_nearest(Vector(pos),.06)
    if loc is None or (Vector(pos)-loc).dot(n)>=-.707*d:continue
    if d>worst[0]:worst=(d,name,f)
    for i,w in weights:
     if d>severity[i]:
      demand[i]=invs[i]@np.array(n)*min(d+.003,.02);severity[i]=d
 print('CLOTH_ENVELOPE',iteration,worst,'max_rest_offset',offset.max(),flush=True)
 if worst[0]<.002:break
 # Smooth the fitted surface slightly while keeping each worst contact's direction.
 smooth=demand.copy();counts=np.ones(len(ids))
 for face in cf:
  for i in face:
   for j in face:
    if i!=j:smooth[i]+=demand[j]*.1;counts[i]+=.1
 offset+=smooth/counts[:,None]
 assert np.linalg.norm(offset,axis=1).max()<.12,np.linalg.norm(offset,axis=1).max()
else:raise AssertionError(worst)
for i,co,s,d in zip(ids,rest,sign,offset):me.vertices[i].co=Vector(co)+Vector(d)
me.update();rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v14.blend'))
(p/'revision_02/motion/cloth_fit.json').write_text(json.dumps({'max_depth_m':worst[0],'max_rest_offset_m':float(np.linalg.norm(offset,axis=1).max()),'iterations':iteration+1,'method':'Rest-shape cloth clearance; original library-driven leg-following weights retained.'},indent=2)+'\n')
