"""Meshy body -> half (x>=0) without rivets and without the head pieces: work/half0.npz (co, tri, comp id per vertex, cls per vertex). Frame: MM9's (glTF: x left of the figure, y up, z forward), scale 2.015, floor at MM9's -0.926.
cls: 0 main hide, >0 separate shell id."""
import sys; sys.path.insert(0,'scripts')
import numpy as np
from loadglb import comps
from clip import clip
D=np.load('work/meshy0.npz'); P,T,l=D['P'].astype(float),D['T'],D['l']
S=2.015; Q=P*S; Q[:,1]+=-.926-Q[:,1].min(); Q[:,2]-=.45
sz=np.bincount(l); nc=len(sz); keep=np.ones(nc,bool); main=int(sz.argmax())
for c in range(nc):
    q=Q[l==c]; e=np.ptp(q,0).max(); ce=(q.min(0)+q.max(0))/2
    if c==main: continue
    if e<.05 and sz[c]<=32: keep[c]=False; continue      # rivets and studs: the paint carries them
    if ce[1]>.58 and ce[2]>.12: keep[c]=False; continue  # helm, teeth, eyes: the head model
print('kept',[(c,int(sz[c])) for c in np.where(keep)[0]])
fk=keep[l[T[:,0]]]; T2=T[fk]
Pc,Tc,ex,rim=clip(Q,T2,np.array([0,0,0.]),np.array([1.,0,0]),extras=(l[:,None].astype(float),))
lc=np.rint(ex[0][:,0]).astype(int)
Pc[rim,0]=0
used,inv=np.unique(Tc,return_inverse=True); co=Pc[used]; tri=inv.reshape(-1,3); lc=lc[used]
print('half',len(co),len(tri))
n2,l2=comps(len(co),tri); print('pieces',n2,np.sort(np.bincount(l2))[::-1][:24])
np.savez('work/half0.npz',co=co,tri=tri,src=lc,comp=l2,main=main)
for c in np.argsort(-np.bincount(l2))[:30]:
    q=co[l2==c]; print(c,(l2==c).sum(),q.min(0).round(2).tolist(),q.max(0).round(2).tolist(),'srcid',lc[l2==c][0])
