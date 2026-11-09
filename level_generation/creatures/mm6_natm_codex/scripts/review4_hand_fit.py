"""Fit the few coarse off-hand faces that bridge the shaft during grasp/release, without changing topology."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as S
cfg=json.loads((P/'gates.json').read_text());g=S.Glb(P/'export/mm6_natm.glb');meshes=S.load_meshes(g)[:4];props=S.load_props(cfg,P,g,S.Report(cfg));spear=props[0];dense=S.load_meshes(S.Glb(P/'review/round4_dense_spear.glb'));a=next(a for a in g.doc['animations']if a['name']=='Attack');frames=[f for f in range(28,74)if not 42<=f<=52];poses=g.pose(a,np.array(frames)/48);gripposes=g.pose(a,np.array([42,52])/48);receipts=[]
for level,m in enumerate(meshes):
 S.configure_mesh(m,cfg,S.Report(cfg));initial=m.vertices.copy();initial_rest=m.rest.copy();surface=S.Surface(m,m.solid&~m.regions['hand_R']);weld={}
 for i,p in enumerate(initial_rest):weld.setdefault(tuple(np.round(p,6)),[]).append(i)
 groups=list(weld.values());mats=[];pp=[]
 def blend(pose):
  matrices=pose[m.skin_nodes]@m.bind;return sum(matrices[m.joints[:,k]]*m.weights[:,k,None,None]for k in range(m.weights.shape[1]))
 for pose in poses:mats.append(blend(pose));pp.append(S.transform(pose[g.names['Spear']]@np.linalg.inv(S.C),dense[level].rest))
 gripmats=[blend(pose)for pose in gripposes];spec=S.grip_points(m,'L',cfg);tris,bary,labels,signature=spec;history=[]
 for iteration in range(36):
  corrections=np.zeros_like(initial);counts=np.zeros(len(initial));worst=0;wf=0
  def move(ids,weights,delta,M):
   weights=np.maximum(weights,0);weights/=max(weights@weights,1e-9);delta*=min(1,.0015/max(np.linalg.norm(delta),1e-12))
   for vi,w in zip(ids,weights):
    if w>0:
     corrections[vi]+=np.linalg.solve(M[vi,:3,:3],delta*w);counts[vi]+=1
  for f,pose,M,prop in zip(frames,poses,mats,pp):
   points=np.einsum('nij,nj->ni',M[:,:3,:3],m.vertices)+M[:,:3,3];depth,vi=S.penetration(surface.build(points),prop)
   if depth>worst:worst=depth;wf=f
   if depth>.05:
    hit=surface.tree.find_nearest(Vector(prop[vi]));ids=m.weld_first[surface.faces[hit[2]]];assert np.all(m.regions['hand_L'][ids]),(level,f,depth,ids.tolist());tri=points[ids];w=np.linalg.lstsq(np.vstack([tri.T,np.ones(3)]),np.r_[hit[0],1],rcond=None)[0];move(ids,w,-np.array(hit[1])*(depth/1000+.0005),M)
  maxgap=0;maxinside=0
  for pose,M in zip(gripposes,gripmats):
   points=np.einsum('nij,nj->ni',M[:,:3,:3],m.vertices)+M[:,:3,3];world=np.einsum('sk,tkj->tsj',bary,points[tris]).reshape(-1,3);to_prop=S.C@np.linalg.inv(pose[g.names['Spear']]);local=S.transform(to_prop,world);gs=spear['grip_surfaces']['L'][level];solid=spear['solid_surfaces'][level];signed,_=solid.signed(local);maxinside=max(maxinside,float(max(0,-signed.min())*1000));rot=np.linalg.inv(to_prop)[:3,:3]
   for mask in labels:
    gap=gs.gap(local[mask])*1000;maxgap=max(maxgap,gap)
    if gap>2.3:
     ids=np.flatnonzero(mask);hits=[gs.tree.find_nearest(Vector(local[i]))for i in ids];j=min(range(len(ids)),key=lambda j:hits[j][3]);idx=ids[j];hit=hits[j];fi,bi=divmod(idx,len(bary));move(tris[fi],bary[bi],rot@(np.array(hit[0])+np.array(hit[1])*.0015-local[idx]),M)
   for idx in np.flatnonzero(signed<-.0023):
    hit=solid.tree.find_nearest(Vector(local[idx]));fi,bi=divmod(idx,len(bary));move(tris[fi],bary[bi],rot@(np.array(hit[0])+np.array(hit[1])*.0015-local[idx]),M)
  history.append({'iteration':iteration,'shaft_in_hand_mm':worst,'frame':wf,'grip_gap_mm':maxgap,'hand_in_shaft_mm':maxinside})
  if iteration%4==0:print('HAND_FIT',level,history[-1],flush=True)
  if worst<=.05 and maxgap<=2.3 and maxinside<=2.3:break
  for ids in groups:
   chosen=[i for i in ids if counts[i]>0]
   if chosen:
    delta=np.mean([corrections[i]/counts[i]for i in chosen],axis=0)*.8
    for i in ids:m.vertices[i]+=delta
  assert np.linalg.norm(m.vertices-initial,axis=1).max()<.018,(level,history[-1])
 delta=(m.vertices-initial)@S.C[:3,:3].T;rows=[]
 for ids in groups:
  i=ids[0]
  if np.linalg.norm(delta[i])>1e-8:rows.append({'rest':initial_rest[i].tolist(),'delta':delta[i].tolist()})
 receipts.append({'lod':level,'max_move_mm':float(np.linalg.norm(delta,axis=1).max()*1000),'vertices':rows,'history':history});print('HAND_FIT_RESULT',level,receipts[-1]['max_move_mm'],history[-1],flush=True)
(P/'work/round4_hand_corrections.json').write_text(json.dumps(receipts,indent=2));(P/'review/round4_hand_fit.json').write_text(json.dumps([{k:v for k,v in row.items()if k!='vertices'}for row in receipts],indent=2))
