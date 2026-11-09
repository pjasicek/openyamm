"""Region of the head skin reached from the neck ring without crossing a sharp crease: the neck and jaw hide. What is not reached is helm (rigid on the head). Writes work/head_region.npy (1 hide, 0 helm) for head1 vertices."""
import sys; sys.path.insert(0,'scripts')
import numpy as np
from collections import deque
D=np.load('work/head1.npz'); co,tri,part=D['co_open'],D['tri'],D['part']; LIM=float(sys.argv[1]) if len(sys.argv)>1 else 55
mf=part[tri[:,0]]==1; ft=np.where(mf)[0]
T=tri[ft]; n=np.cross(co[T[:,1]]-co[T[:,0]],co[T[:,2]]-co[T[:,0]]); n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-12)
ed={}
for i,f in enumerate(T):
    for a,b in ((f[0],f[1]),(f[1],f[2]),(f[2],f[0])): ed.setdefault((min(a,b),max(a,b)),[]).append(i)
adj=[[] for _ in T]; bnd=set()
for k,v in ed.items():
    if len(v)==2:
        ang=np.degrees(np.arccos(np.clip(n[v[0]]@n[v[1]],-1,1)))
        if ang<LIM: adj[v[0]].append(v[1]); adj[v[1]].append(v[0])
    elif len(v)==1: bnd.add(v[0])
seen=np.zeros(len(T),bool); q=deque(bnd); 
for b in bnd: seen[b]=True
while q:
    x=q.popleft()
    for y in adj[x]:
        if not seen[y]: seen[y]=True; q.append(y)
print('faces',len(T),'hide',seen.sum())
vh=np.zeros(len(co)); 
np.add.at(vh,T[seen].ravel(),1)
vh2=np.zeros(len(co)); np.add.at(vh2,T[~seen].ravel(),1)
r=(vh>0).astype(int); np.save('work/head_region.npy',r)
np.savez('work/head1r.npz',co=D['co'],tri=tri[ft],r=r)
