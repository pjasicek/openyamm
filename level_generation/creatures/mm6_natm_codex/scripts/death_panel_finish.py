"""Finish the falling rear panel against both skin-interior samples and all runtime cloth volumes."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path[:0]=[str(P/'scripts'),str(P.parent/'claude_shared/gates')];import run_gates as G,reduction_common as C
from collision import inside
cfg=json.loads((P/'gates.json').read_text());g=G.Glb(P/'export/mm6_natm.glb');rep=G.Report(cfg);meshes=G.load_meshes(g);names=['ClothBack','ClothBack1','ClothBack2','ClothBack3'];MW={}
for m in meshes:
 G.configure_mesh(m,cfg,rep);w=np.column_stack([m.weight([n])for n in names]);w[:,0]=w.sum(1);MW[m.label]=w
a=next(a for n,a,s,e in g.clips()if n=='Death');bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod0.blend'));r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;co=np.array([v.co[:]for v in me.vertices]);pv=np.array([d.value for d in me.attributes['piece'].data]);me.calc_loop_triangles();tri=np.array([t.vertices[:]for t in me.loop_triangles]);skintri=tri[np.all(pv[tri]==0,axis=1)];ct=tri[np.all(pv[tri]==10,axis=1)&(np.max(co[tri,2],axis=1)<.93)];bary=np.array([[1,0,0],[0,1,0],[0,0,1],[.5,.5,0],[0,.5,.5],[.5,0,.5],[1/3]*3]);W=np.zeros((len(co),4))
for v in me.vertices:
 for w in v.groups:
  n=body.vertex_groups[w.group].name
  if n in names:W[v.index,names.index(n)]=w.weight
W[:,0]=W.sum(1);cw=np.einsum('sk,tkj->tsj',bary,W[ct]).reshape(-1,4);changes=[];rows=[]
def worst_inside(tree,pts):
 worst=(0,None,None)
 for i,p in enumerate(pts):
  q,n,fi,d=tree.find_nearest(Vector(p))
  if d>worst[0]and(Vector(p)-q).dot(n)<-.00005 and inside(tree,Vector(p)):worst=(d,i,np.array(n))
 return worst
for f in range(161):
 C.activate('Death',f/48);base={n:r.pose.bones[n].location.copy()for n in names};ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();points=np.array([v.co[:]for v in em.vertices]);ev.to_mesh_clear();skin=BVHTree.FromPolygons(points.tolist(),skintri.tolist(),all_triangles=True);cp=np.einsum('sk,tkj->tsj',bary,points[ct]).reshape(-1,3);pose=g.pose(a,np.array([f/48]))[0];cases=[]
 for m in meshes:
  pts=m.posed(pose);_,surf,samples,_=next(row for row in m.cloth if row[0]=='ClothBack');cases.append((m,pts,surf,samples))
 delta=np.zeros((4,3));forward=worst_inside(skin,cp);before=forward[0];worst=0
 if before>.0008:
  for it in range(65):
   d,i,n=worst_inside(skin,cp+cw@delta)
   if d>.0005:
    w=cw[i];delta+=np.outer(w,n*(d+.0005))*.65/max(w@w,1e-9)
   rev=0
   for m,pts,surf,samples in cases:
    mw=MW[m.label];pp=pts+mw@delta;surf.build(pp,pose);ids=np.flatnonzero(samples);ds,faces=surf.signed(pp[ids]);j=int(ds.argmin());depth=max(0,-ds[j]);rev=max(rev,depth)
    if depth>.0007:
     q,n,fi,d=surf.tree.find_nearest(Vector(pp[ids[j]]))
     if fi<len(surf.faces):
      ids2=m.weld_first[surf.faces[fi]];vv=pp[ids2];uv=np.linalg.lstsq(np.column_stack([vv[1]-vv[0],vv[2]-vv[0]]),np.array(q)-vv[0],rcond=None)[0];b=np.array([1-uv.sum(),uv[0],uv[1]]);w=b@mw[ids2];delta+=np.outer(w,-np.array(n)*(d+.0005))*.4/max(w@w,1e-9)
   ids=np.flatnonzero((pv==10)&(co[:,2]<.93)&(W[:,0]>.25));z=points[ids,2]+W[ids]@delta[:,2]
   j=int(z.argmin())
   if z[j]<.0005:w=W[ids[j]];delta[:,2]+=w*(.0005-z[j])/max(w@w,1e-9)
   if d<.001 and rev<.001:break
  forward=worst_inside(skin,cp+cw@delta)
  for m,pts,surf,samples in cases:
   pp=pts+MW[m.label]@delta;depth,_=G.penetration(surf.build(pp,pose),pp[samples]);worst=max(worst,depth)
  print('FALL PANEL',f,'before',round(before*1000,3),'after',round(forward[0]*1000,3),'reverse',round(worst,3),'delta',round(np.linalg.norm(delta,axis=1).max()*1000,2),flush=True)
 changes.append((base,delta));rows.append({'frame':f,'before_mm':before*1000,'forward_mm':forward[0]*1000,'reverse_mm':worst,'control_shift_mm':float(np.linalg.norm(delta,axis=1).max()*1000)})
for level in range(4):
 path=P/f'work/runtime_lod{level}.blend';bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['Rig']
 for f,(base,delta)in enumerate(changes):
  C.activate('Death',f/48)
  for n in names:r.pose.bones[n].location=base[n]
  bpy.context.view_layer.update()
  for k,n in enumerate(names):
   pb=r.pose.bones[n];basis=pb.matrix.to_3x3()@pb.rotation_quaternion.to_matrix().inverted();pb.location+=basis.inverted()@Vector(delta[k]);bpy.context.view_layer.update();pb.keyframe_insert('location',frame=f)
 C.activate('Death',160/48);last={n:r.pose.bones[n].location.copy()for n in names};a0=bpy.data.actions['Dead'];r.animation_data.action=a0;r.animation_data.action_slot=a0.slots[0]
 for f in [0,1]:
  for n,l in last.items():r.pose.bones[n].location=l;r.pose.bones[n].keyframe_insert('location',frame=f)
 C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(path))
 if level==0:bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_natm.blend'))
(P/'review/death_panel_finish.json').write_text(json.dumps(rows,indent=2))
