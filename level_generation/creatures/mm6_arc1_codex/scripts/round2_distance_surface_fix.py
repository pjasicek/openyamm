"""Fit coarse hand surfaces to the actual retained grip, align feet and remove sampled floor intersections."""
import bpy,json,sys,math,numpy as np,runpy,shutil
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];W=P/'work/round2';D=P/'review/round2/reduction';sys.dont_write_bytecode=True
records=[]
def posed(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=np.array([x.co[:]for x in m.vertices]);ev.to_mesh_clear();return v
def transform(rig,ob,index):
 names={g.index:g.name for g in ob.vertex_groups};v=ob.data.vertices[index]
 return sum((np.array(rig.pose.bones[names[g.group]].matrix@rig.data.bones[names[g.group]].matrix_local.inverted())*g.weight for g in v.groups),np.zeros((4,4)))[:3,:3]
def action(rig,name,f):
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(int(f),subframe=f-int(f))
for level in [1,2,3]:
 bpy.ops.wm.open_mainfile(filepath=str(W/f'lod{level}.blend'));body=bpy.data.objects['Body'];prop=bpy.data.objects['BowAsset'];rig=bpy.data.objects['Rig'];action(rig,'Standing',0)
 piece=np.array([v.value for v in body.data.attributes['piece'].data]);finger=np.array([v.value for v in body.data.attributes['finger'].data]);co=posed(body);original=co.copy();bow=np.array(rig.pose.bones['Bow'].matrix);inv=np.linalg.inv(bow);local=(np.c_[co,np.ones(len(co))]@inv.T)[:,:3]
 pb=rig.data.bones['Bow'].matrix_local.inverted();pv=[pb@v.co for v in prop.data.vertices];faces=[tuple(f.vertices)for f in prop.data.polygons if all(abs(pv[i].z)<.076 and math.hypot(pv[i].x,pv[i].y)<.019 for i in f.vertices)];tree=BVHTree.FromPolygons(pv,faces)
 body.data.calc_loop_triangles();tri=np.array([list(t.vertices)for t in body.data.loop_triangles if all(piece[i]==2 for i in t.vertices)]);weights=np.array([[i/8,j/8,(8-i-j)/8]for i in range(9)for j in range(9-i)]);labels=finger[tri[:,np.argmax(weights,axis=1)]]
 for iteration in range(200):
  for digit in range(6):
   points=np.einsum('sj,tjk->tsk',weights,local[tri]);available=np.argwhere((labels==digit)&(abs(points[:,:,2])<.052))
   if not len(available):raise AssertionError(('Missing digit region',level,digit))
   nearest=[]
   for ti,si in available:
    point=points[ti,si];hit,n,ix,dist=tree.find_nearest(Vector(point));nearest.append((dist,ti,si,np.array(hit)))
   dist,ti,si,hit=min(nearest,key=lambda x:x[0])
   if dist>.0024:
    w=weights[si];correction=(hit-points[ti,si])*((dist-.0015)/dist)
    for i,a in zip(tri[ti],w):local[i]+=correction*a/max(.05,float(w@w))
  worst=0
  for ids in tri:
   points=weights@local[ids];valid=np.flatnonzero(abs(points[:,2])<.052)
   if not len(valid):continue
   ix=valid[np.linalg.norm(points[valid,:2],axis=1).argmin()];p=points[ix];rad=np.linalg.norm(p[:2])
   if rad>=.00825:continue
   w=weights[ix];direction=p[:2]/rad if rad>1e-7 else local[ids,:2].mean(0);direction/=max(1e-9,np.linalg.norm(direction));correction=(.0083-rad)*direction
   for i,a in zip(ids,w):local[i,:2]+=correction*a/max(.05,float(w@w))
   worst=max(worst,.0083-rad)
  points=np.einsum('sj,tjk->tsk',weights,local[tri]);gaps=[]
  for digit in range(6):
   pts=points[(labels==digit)&(abs(points[:,:,2])<.052)];gaps.append(min(tree.find_nearest(Vector(p))[3]for p in pts))
  if max(gaps)<.0028 and worst<.00005:break
 ids=np.flatnonzero(piece==2);co[ids]=(np.c_[local[ids],np.ones(len(ids))]@bow.T)[:,:3]
 for i in ids:
  if np.linalg.norm(co[i]-original[i])>1e-9:body.data.vertices[i].co+=Vector(np.linalg.solve(transform(rig,body,i),co[i]-original[i]))
 body.data.update()
 # Fit the coarse sole's measured long axis to the accepted forward direction.
 names={g.index:g.name for g in body.vertex_groups};foot_turn={}
 if level==3:
  co=posed(body)
  for side in 'LR':
   ids=[v.index for v in body.data.vertices if sum(g.weight for g in v.groups if names[g.group]in[f'B_{side}_Foot',f'B_{side}_Toe0'])>.8];sole=[i for i in ids if body.data.vertices[i].co.z<.009];heel=[i for i in sole if body.data.vertices[i].co.y>.005];toe=[i for i in sole if body.data.vertices[i].co.y<-.065];direction=co[toe].mean(0)-co[heel].mean(0);angle=math.atan2(direction[0],-direction[1]);foot_turn[side]=math.degrees(angle);center=co[sole].mean(0);c,s=math.cos(-angle),math.sin(-angle);rotation=np.array([[c,-s,0],[s,c,0],[0,0,1]])
   for i in ids:
    delta=rotation@(co[i]-center)+center-co[i];body.data.vertices[i].co+=Vector(np.linalg.solve(transform(rig,body,i),delta))
  body.data.update()
 floor_changes=0
 for sweep in range(8):
  worst=0
  for a in list(bpy.data.actions):
   for f in np.arange(0,float(a.frame_range[1])+.001,.25):
    action(rig,a.name,float(f))
    for ob in [body,prop]:
     co=posed(ob)
     for i in np.flatnonzero(co[:,2]<.0001):
      depth=.00025-co[i,2];worst=max(worst,depth);delta=np.array([0,0,depth]);bodymat=transform(rig,ob,int(i))
      if abs(np.linalg.det(bodymat))<1e-6:continue
      ob.data.vertices[int(i)].co+=Vector(np.linalg.solve(bodymat,delta));floor_changes+=1
     ob.data.update()
  if worst<.00015:break
 action(rig,'Standing',0);bpy.ops.wm.save_as_mainfile(filepath=str(W/f'lod{level}.blend'))
 # Keep component selections reproducible after the constrained surface corrections.
 bpy.ops.wm.save_as_mainfile(filepath=str(W/f'body_l{level}_final.blend'));records.append({'lod':level,'grip_iterations':iteration+1,'grip_gaps_m':gaps,'foot_turn_deg':foot_turn,'floor_constraints_applied':floor_changes,'floor_sweeps':sweep+1});(D/'distance_surface_repairs.json').write_text(json.dumps(records,indent=2));print('DISTANCE_SURFACE_REPAIR',records[-1],flush=True)
