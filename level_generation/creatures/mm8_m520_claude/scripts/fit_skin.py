"""Continuous hand weights across every phalanx joint and the palm webs."""
import numpy as np

def apply(body,rig):
 me=body.data
 if me.get('cyclops_finger_skin_fit'):return
 co=np.array([v.co[:] for v in me.vertices]);names=[g.name for g in body.vertex_groups];index={n:i for i,n in enumerate(names)};w=np.zeros((len(co),len(names)))
 for v in me.vertices:
  for g in v.groups:w[v.index,g.group]=g.weight
 edges=np.array([e.vertices[:] for e in me.edges]);neighbours=[[] for _ in co]
 for a,b in edges:neighbours[a].append(b);neighbours[b].append(a)
 for side in 'LR':
  hand=index[f'B_{side}_Hand'];channels=[i for i,n in enumerate(names) if n==f'B_{side}_Hand' or n.startswith(f'B_{side}_Finger')];total=w[:,channels].sum(1);ids=np.flatnonzero(total>.05);chains=[]
  for digit in range(5):
   ns=[f'B_{side}_Finger{digit}']
   while rig.data.bones[ns[-1]].children:ns.append(rig.data.bones[ns[-1]].children[0].name)
   points=[np.array(rig.data.bones[n].head_local) for n in ns];points.append(points[-1]+(points[-1]-points[-2])*1.3);chains.append((ns,np.array(points)))
  for vi in ids:
   closest=None
   for fi,(ns,points) in enumerate(chains):
    for seg in range(3):
     direction=points[seg+1]-points[seg];t=(co[vi]-points[seg])@direction/(direction@direction);distance=np.linalg.norm(co[vi]-(points[seg]+np.clip(t,0,1)*direction))
     if closest is None or distance<closest[0]:closest=(distance,fi,seg,float(t))
   distance,fi,seg,t=closest
   if distance>.065:continue
   ns,points=chains[fi]
   if seg==0 and t<-.3:continue
   values={index[ns[seg]]:1.}
   if t<.3:
    prev=hand if seg==0 else index[ns[seg-1]];k=np.clip(.5+t/.6,0,1);values={prev:1-k,index[ns[seg]]:k}
   elif t>.7 and seg<2:
    k=np.clip((t-.7)/.6,0,.5);values={index[ns[seg]]:1-k,index[ns[seg+1]]:k}
   w[vi,channels]=0
   for gi,value in values.items():w[vi,gi]=value*total[vi]
  # Distal palm and digits belong entirely to the hand, with a short wrist transition.
  wrist=np.array(rig.data.bones[f'B_{side}_Hand'].head_local)
  knuckles=np.mean([rig.data.bones[f'B_{side}_Finger{i}'].head_local[:] for i in range(1,5)],axis=0);forward=knuckles-wrist
  along=(co-wrist)@forward/(forward@forward)
  gain=np.clip(along/.3,0,1);gain=gain*gain*(3-2*gain)
  for vi in ids:
   old=total[vi];target=old+(1-old)*gain[vi];shares=w[vi,channels].copy()/max(old,1e-12)
   w[vi]*=(1-gain[vi]);w[vi,channels]=shares*target
   total[vi]=target
  # Short edges need matching weights: distance-weighted averaging removes isolated hand-owned tip vertices.
  for _ in range(8):
   new=w.copy()
   for vi in ids:
    ns=[j for j in neighbours[vi] if total[j]>.05]
    if not ns:continue
    weights=1/np.maximum(np.linalg.norm(co[ns]-co[vi],axis=1),.001)**2;value=.5*w[vi,channels]+.5*np.average(w[np.ix_(ns,channels)],weights=weights,axis=0);new[vi,channels]=value/value.sum()*total[vi]
   w=new
 w/=w.sum(1,keepdims=True);assert np.isfinite(w).all() and np.allclose(w.sum(1),1)
 for g in body.vertex_groups:g.remove(list(range(len(co))))
 for vi,row in enumerate(w):
  for gi in np.flatnonzero(row>1e-7):body.vertex_groups[int(gi)].add([vi],float(row[gi]),'REPLACE')
 me['cyclops_finger_skin_fit']=True
