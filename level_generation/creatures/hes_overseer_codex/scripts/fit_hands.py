"""Fit six claw chains to the retained hand; no hand geometry is added or removed.
Centreline landmarks are measured in the retained bind mesh (review/hand_topology.png).
The model has a thumb and five claw fingers; the sixth chain uses B_*_Finger5.
"""
import bpy,json,sys,os,heapq
from pathlib import Path
from mathutils import Matrix,Vector
import numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/winged_base_rig.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
SRC=json.loads((P/'source/humanoid_source_rest.json').read_text())
paths=np.array([
 [[.283,-.242,.612],[.270,-.265,.591],[.253,-.283,.563],[.229,-.300,.544]],
 [[.350,-.267,.584],[.354,-.287,.542],[.310,-.308,.489],[.238,-.337,.486]],
 [[.360,-.251,.579],[.369,-.253,.521],[.313,-.279,.451],[.234,-.302,.445]],
 [[.369,-.223,.582],[.370,-.225,.513],[.308,-.249,.432],[.222,-.248,.425]],
 [[.362,-.192,.582],[.362,-.189,.525],[.308,-.211,.466],[.232,-.226,.457]],
 [[.350,-.169,.584],[.347,-.157,.532],[.308,-.179,.502],[.216,-.213,.486]],
])
co=np.array([v.co[:] for v in body.data.vertices])
# Native automatic weights reach into the claws. Put distal palm/digit skin on the hand before fitting fingers.
for sd,sg in [('L',1),('R',-1)]:
 hand=body.vertex_groups[f'B_{sd}_Hand'];wrist=np.array(rig.data.bones[f'B_{sd}_Hand'].head_local);knuckles=paths[:,0].mean(0);knuckles[0]*=sg;axis=knuckles-wrist;axis/=np.linalg.norm(axis)
 for v in body.data.vertices:
  hw=next((g.weight for g in v.groups if g.group==hand.index),0)
  if hw<.1:continue
  blend=float(np.clip(((co[v.index]-wrist)@axis+.01)/.035,0,1));moved=0
  for group in list(v.groups):
   name=body.vertex_groups[group.group].name
   if name in [f'B_{sd}_Forearm',f'B_{sd}_UpperArm']:
    value=group.weight*blend;body.vertex_groups[group.group].add([v.index],group.weight-value,'REPLACE');moved+=value
  if moved:hand.add([v.index],hw+moved,'REPLACE')
oldweights=[[(body.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in body.data.vertices]

label=np.zeros(len(co),np.int32);info={};rest={};chains={}
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for sd,sg in [('L',1),('R',-1)]:
 pp=paths.copy();pp[:,:,0]*=sg
 chains[sd]=[];info[sd]={}
 for digit,points in enumerate(pp):
  names=[f'B_{sd}_Finger{digit}',f'B_{sd}_Finger{digit}1',f'B_{sd}_Finger{digit}2']
  if sd=='R' and digit==0:names=['B_R_Finger0','B_R_Finger0.001','B_R_Finger0.002']
  chains[sd].append(names);info[sd][str(digit)]={'points':points.tolist(),'bones':names}
  for i,name in enumerate(names):
   srcdigit=min(digit,4);srcname=f'B_{sd}_Finger{srcdigit}'+('' if i==0 else str(i))
   if sd=='R' and digit==0:srcname=names[i]
   s=SRC[srcname];parent=rig.data.edit_bones[names[i-1] if i else f'B_{sd}_Hand']
   seg=Vector(s['seg']) if s['seg'] is not None else Vector((.04,0,0))
   q=seg.rotation_difference(Vector(points[i+1]-points[i]));R=q.to_matrix()@Matrix(s['rot'])
   b=rig.data.edit_bones.new(name);b.head=points[i];b.tail=b.head+R.col[1]*float(np.linalg.norm(points[i+1]-points[i]));b.align_roll(R.col[2]);b.parent=parent
bpy.ops.object.mode_set(mode='OBJECT')
# Each claw grows through welded mesh edges from its measured tip; palm is excluded at the knuckle band.
unique,inv=np.unique(np.round(co,5),axis=0,return_inverse=True)
adj=[[] for _ in unique]
for a,b in np.unique(np.sort(inv[np.array([e.vertices[:] for e in body.data.edges])],axis=1),axis=0):
 if a!=b:
  length=float(np.linalg.norm(unique[a]-unique[b]));adj[a].append((b,length));adj[b].append((a,length))
pieces={}
for sd,sg in [('L',1),('R',-1)]:
 points=paths.copy();points[:,:,0]*=sg
 allowed=(unique[:,0]*sg>.18)&(unique[:,0]*sg<.42)&(unique[:,1]<-.12)&(unique[:,1]>-.37)&(unique[:,2]<.625)&(unique[:,2]>.39)
 distances=[]
 for d,line in enumerate(points):
  seed=int(np.argmin(np.linalg.norm(unique-line[-1],axis=1)));assert allowed[seed]
  dist=np.full(len(unique),np.inf);dist[seed]=0;queue=[(0,seed)]
  while queue:
   cost,v=heapq.heappop(queue)
   if cost>dist[v]:continue
   for w,length in adj[v]:
    if allowed[w] and cost+length<dist[w]:dist[w]=cost+length;heapq.heappush(queue,(dist[w],w))
  distances.append(dist)
 owner=np.argmin(distances,axis=0);owner[~allowed]=-1;pieces[sd]=owner[inv]
 assert all(np.count_nonzero(pieces[sd]==d)>0 for d in range(6))
# Fit the repaired hand weights, keeping every bind vertex in place.
for sd,sg in [('L',1),('R',-1)]:
 pp=paths.copy();pp[:,:,0]*=sg;hn=f'B_{sd}_Hand'
 groups={n:body.vertex_groups.new(name=n) for chain in chains[sd] for n in chain}
 hand=body.vertex_groups[hn]
 for vi,ws in enumerate(oldweights):
  hw=dict(ws).get(hn,0)
  if hw<1e-6:continue
  point=co[vi];choices=[]
  for d,points in enumerate(pp):
   if pieces[sd][vi]>=0 and d!=pieces[sd][vi]:continue
   for j in range(3):
    ab=points[j+1]-points[j];t=float(np.clip((point-points[j])@ab/(ab@ab),0,1));dist=np.linalg.norm(point-(points[j]+t*ab))
    choices.append((float(dist),d,j,t))
  dist,d,j,t=min(choices)
  root=pp[d,0];axis=pp[d,1]-root;axis/=np.linalg.norm(axis)
  along=(point-root)@axis
  feather=float(np.clip((along+.012)/.030,0,1)) if j==0 else 1.0
  if pieces[sd][vi]<0 and dist>.045:feather*=float(np.clip((.065-dist)/.02,0,1))
  if feather<=1e-6:continue
  hand.add([vi],hw*(1-feather),'REPLACE')
  weights={j:1.0}
  if t<.35 and j>0:weights={j:t/.35,j-1:1-t/.35}
  elif t>.7 and j<2:weights={j:(1-t)/.3,j+1:(t-.7)/.3}
  for index,weight in weights.items():groups[chains[sd][d][index]].add([vi],hw*feather*weight,'REPLACE')
  if feather>.5:label[vi]=(1 if sd=='L' else 11)+d
# Welded-position weight smoothing makes UV seam copies identical and keeps the finger webs continuous.
unique, inv=np.unique(np.round(co,5),axis=0,return_inverse=True)
edges=np.unique(np.sort(inv[np.array([e.vertices[:] for e in body.data.edges])],axis=1),axis=0)
for sd in chains:
 hn=f'B_{sd}_Hand';names=[hn]+[n for chain in chains[sd] for n in chain]
 gs=[body.vertex_groups[n] for n in names];lookup={g.index:i for i,g in enumerate(gs)}
 raw=np.zeros((len(co),len(gs)))
 for v in body.data.vertices:
  for g in v.groups:
   if g.group in lookup:raw[v.index,lookup[g.group]]=g.weight
 total=raw.sum(1);u=np.zeros((len(unique),len(gs)));counts=np.bincount(inv)
 np.add.at(u,inv,raw);u/=counts[:,None];fraction=u.sum(1)
 use=edges[(fraction[edges[:,0]]>.01)&(fraction[edges[:,1]]>.01)]
 for _ in range(2):
  sums=u.copy();degree=np.ones(len(u))
  np.add.at(sums,use[:,0],u[use[:,1]]);np.add.at(sums,use[:,1],u[use[:,0]])
  np.add.at(degree,use[:,0],1);np.add.at(degree,use[:,1],1)
  u=.6*u+.4*sums/degree[:,None]
  u*=fraction[:,None]/np.maximum(u.sum(1)[:,None],1e-12)
 smoothed=u[inv];smoothed*=total[:,None]/np.maximum(smoothed.sum(1)[:,None],1e-12)
 for j,g in enumerate(gs):
  g.remove(list(range(len(co))))
  for vi in np.flatnonzero(smoothed[:,j]>1e-8):g.add([int(vi)],float(smoothed[vi,j]),'REPLACE')
 dominant=np.argmax(smoothed[:,1:].reshape(len(co),6,3).sum(2),axis=1)
 mask=total>.5;label[mask]=(1 if sd=='L' else 11)+dominant[mask]

# Runtime skinning uses four influences; fit and solve exactly the weights that will be exported.
for v in body.data.vertices:
 ws=sorted([(g.group,g.weight) for g in v.groups if g.weight>1e-8],key=lambda x:-x[1]);kept=ws[:4];total=sum(w for _,w in kept)
 for gi,w in ws:body.vertex_groups[gi].remove([v.index])
 for gi,w in kept:body.vertex_groups[gi].add([v.index],w/total,'REPLACE')
assert max(abs(sum(g.weight for g in v.groups)-1) for v in body.data.vertices)<1e-4
if 'finger' not in body.data.attributes:body.data.attributes.new('finger','INT','POINT')
body.data.attributes['finger'].data.foreach_set('value',label)
for sd in chains:
 for names in chains[sd]:
  for n in names:rest[n]=[list(r) for r in rig.data.bones[n].matrix_local]
(P/'work/finger_fit.json').write_text(json.dumps({'hands':info,'rest':rest,'ownership':'mesh-edge geodesic growth from measured claw tips; original hand geometry preserved','label_counts':{str(k):int((label==k).sum()) for k in np.unique(label)}},indent=2)+'\n')
# Export an optimization packet: original skin data and the new finger-local frames, with no animation active.
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
np.savez(P/'work/finger_skin.npz',positions=co,labels=label,faces=np.array([f.vertices[:] for f in body.data.polygons]),hand_weights=np.array([[next((g.weight for g in v.groups if body.vertex_groups[g.group].name==f'B_{sd}_Hand'),0) for sd in 'LR'] for v in body.data.vertices]),edges=np.array([e.vertices[:] for e in body.data.edges]),weights=np.array([[next((g.weight for g in v.groups if body.vertex_groups[g.group].name==n),0) for n in rest] for v in body.data.vertices]),bone_names=np.array(list(rest)))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/winged_hands.blend'))
print('HAND_FIT_DONE',len(rig.data.bones),'bones',flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
