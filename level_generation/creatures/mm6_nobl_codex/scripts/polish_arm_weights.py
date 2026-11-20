"""Regularize short-edge weight gradients after reduction; retain four influences used by the runtime."""
import bpy,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v5.blend'))
ob=bpy.data.objects['Body'];me=ob.data
if not bpy.context.scene.get('arm_weights_polished'):
 co=np.array([tuple(v.co) for v in me.vertices]);pv=np.zeros(len(co),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
 names=[g.name for g in ob.vertex_groups];W=np.zeros((len(co),len(names)))
 for v in me.vertices:
  for g in v.groups:W[v.index,g.group]=g.weight
 adj=[[] for _ in co]
 for e in me.edges:
  a,b=e.vertices
  if pv[a]==pv[b]==1:
   w=1/max(np.linalg.norm(co[a]-co[b]),.002)**2
   adj[a].append((b,w));adj[b].append((a,w))
 strength=np.clip((abs(co[:,0])-.11)/.05,0,1)*np.clip((.38-abs(co[:,0]))/.06,0,1)*np.clip((co[:,2]-1.13)/.06,0,1)*np.clip((1.44-co[:,2])/.06,0,1)
 ids=np.where((pv==1)&(strength>0))[0]
 for _ in range(4):
  U=W.copy()
  for i in ids:
   if not adj[i]:continue
   js,ws=zip(*adj[i]);ws=np.array(ws);average=np.sum(W[list(js)]*ws[:,None],axis=0)/ws.sum()
   a=.6*strength[i];U[i]=(1-a)*W[i]+a*average
  W=U
 j0,j1=names.index('B_Spine'),names.index('B_Spine1')
 W[ids,j1]+=W[ids,j0];W[ids,j0]=0
 for i,row in enumerate(W):
  keep=np.argsort(-row)[:4];row[np.argsort(-row)[4:]]=0;row/=row.sum()
 for g in ob.vertex_groups:g.remove(list(range(len(co))))
 for i,row in enumerate(W):
  for j in np.flatnonzero(row>1e-6):ob.vertex_groups[int(j)].add([i],float(row[j]),'REPLACE')
 assert np.max(abs(W.sum(1)-1))<1e-6 and np.max((W>1e-6).sum(1))<=4
 bpy.context.scene['arm_weights_polished']=True
 bpy.ops.wm.save_mainfile()
 print('ARM_POLISH',len(ids),'vertices; four runtime influences')
