"""Connectivity cuts of the returned claw hands; preserve digit ownership through the palm web."""
import json
import numpy as np
from pathlib import Path
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components,dijkstra
P=Path(__file__).resolve().parents[1]
m=np.load(P/'work/fitted_mesh.npz');co=m['vertices'];f=m['faces'];NV=len(co)
E=np.unique(np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),1),axis=0)
J=json.loads((P/'work/joints.json').read_text())['joints']
def components(mask):
 e=E[mask[E].all(1)];ad=coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(NV,NV));_,lab=connected_components(ad,directed=False)
 return [np.where(mask&(lab==k))[0] for k in np.unique(lab[mask])]
# Observed terminal branch positions only select connected pieces, never distance-weight neighbouring fingers.
branches={
'L':{'thumb':(.35,[1.06,.63,2.16]),'index':(.55,[1.39,.53,2.13]),'middle':(.55,[1.43,.76,2.03]),'ring':(.55,[1.37,.96,2.03])},
'R':{'thumb':(.35,[-.35,-.84,2.37]),'index':(.55,[-.24,-.98,2.3]),'middle':(.55,[-.20,-1.27,2.30]),'ring':(.55,[-.49,-1.22,2.22]),'pinky':(.45,[-.72,-1.16,2.30])}}
out={}
for side,palm in [('L',[1.104,.816,2.289]),('R',[-.571,-1.098,2.404])]:
 wr=np.array(J[side+'_Hand']);palm=np.array(palm);fd=palm-wr;fd/=np.linalg.norm(fd);depth=(co-wr)@fd
 radial=np.linalg.norm(co-wr-depth[:,None]*fd,axis=1);mask=(radial<.60)&(depth>-.05)&(np.linalg.norm(co-wr,axis=1)<1.1)
 part=min(components(mask),key=lambda p:np.linalg.norm(co[p]-palm,axis=1).min());mask[:]=False;mask[part]=True
 edges=E[mask[E].all(1)];length=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)
 graph=coo_matrix((length,(edges[:,0],edges[:,1])),shape=(NV,NV)).tocsr()
 start=int(part[np.argmin(np.linalg.norm(co[part]-wr,axis=1))]);distance=dijkstra(graph,directed=False,indices=start)
 output={'hand_vertices':part.tolist(),'palm':palm.tolist(),'chains':{}};seeds=[]
 for name,(cut,point) in branches[side].items():
  parts=[p for p in components(mask&(distance>cut)) if len(p)>=4]
  ids=min(parts,key=lambda p:np.linalg.norm(co[p].mean(0)-point));assert np.linalg.norm(co[ids].mean(0)-point)<.13
  seeds.append(ids);base_ids=ids[np.argsort(distance[ids])[:max(4,len(ids)//6)]];base=co[base_ids].mean(0)
  tip=co[ids[np.argmax(distance[ids])]];axis=tip-base;axis/=np.linalg.norm(axis);base-=axis*.10
  d=(co[ids]-base)@axis;end=(tip-base)@axis;points=[base]
  for t in (.38,.72):
   near=ids[np.argsort(np.abs(d-end*t))[:max(4,len(ids)//5)]];points.append(co[near].mean(0))
  points.append(tip)
  output['chains'][name]={'points':[p.tolist() for p in points],'terminal_vertices':ids.tolist(),'cut_geodesic_m':cut}
 assert len(set(i for ids in seeds for i in ids))==sum(map(len,seeds)),side
 # Grow ownership through connected edges toward the wrist, with a common palm transition.
 geos=np.array([np.min(dijkstra(graph,directed=False,indices=ids),axis=0) for ids in seeds]);labels=np.argmin(geos,axis=0)
 for k,name in enumerate(branches[side]):
  ids=np.where(mask&(labels==k)&(distance>.20))[0];output['chains'][name]['vertices']=ids.tolist()
 if side=='L':
  output['chains']['pinky']={'points':[[1.25,1.005,2.32],[1.35,1.15,2.22],[1.41,1.16,2.08],[1.40,1.105,1.98]],'vertices':[],
    'repair':'Missing digit in return; new connected-shape claw rooted inside the outer palm, matching adjacent ring finger.'}
 out[side]=output
(P/'work/fingers_fit.json').write_text(json.dumps(out,indent=2)+'\n')
print({s:{n:len(v['vertices']) for n,v in o['chains'].items()} for s,o in out.items()})
