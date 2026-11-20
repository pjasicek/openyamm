"""Head-only Smart Topology -> half clean in Meshy's frame: work/head_half.npz (co, tri, protect), tooth sites work/head_sites.npz. Cut at the neck plane, teeth and scraps removed, x>=0 kept."""
import sys; sys.path.insert(0,'scripts')
import numpy as np
from loadglb import comps
from clip import clip
import headfr as H
D=np.load('work/mhead0.npz'); P,T,l=D['P'].astype(float),D['T'],D['l']
sz=np.bincount(l); main=int(sz.argmax())
sites=[]
for c in np.where(sz<200)[0]:
    q=P[l==c]; ce=q.mean(0); ext=np.ptp(q,0).max()
    u,s,vt=np.linalg.svd(q-ce); ax=vt[0]
    # root -> tip: the row is upper if it lies above the line of lower teeth
    sites.append((c,ce,ax,ext,sz[c]))
Fc=np.array([s[1] for s in sites]); 
# upper or lower by the height above the mid line in Meshy's frame (rows: upper y ~ .07 -> -.02, lower -.05 -> -.19)
mid=lambda z: -.02-.14*(z-.15)/.3*1.0+.03
up=Fc[:,1]>mid(Fc[:,2])
print('sites',len(sites),'upper',up.sum())
out=[]
for (c,ce,ax,ext,n),u in sorted(zip(sites,up),key=lambda s:-(s[0][1][0])):
    if n>100: continue                # three teeth fused: their twins on the other side stand in
    a=ax if (ax[1]<0)==u else -ax      # root to tip: upper teeth down, lower up
    if ce[0]<0: ce=ce*[-1,1,1]; a=a*[-1,1,1]
    if out and min(np.linalg.norm(np.array(o_[:3])-ce) for o_ in out)<.014: continue
    out.append([*ce,*a,ext,float(u)])
out=np.array(out); o=np.lexsort((out[:,2],out[:,7])); out=out[o]; print(np.round(out[:,[0,1,2,6,7]],3))
np.savez('work/head_sites.npz',s=out)
Tm=T[l[T[:,0]]==main]
# neck plane in Meshy's frame: map two points
pm=H.Fi(H.PLANE_P[None])[0]; q=H.Fi((H.PLANE_P+H.PLANE_N*.1)[None])[0]
# a plane maps to a plane; normal by inverse transpose
e1=H.Fi((H.PLANE_P+np.array([1,0,0])*.1)[None])[0]-pm; e2=H.Fi((H.PLANE_P+np.cross(H.PLANE_N,[1,0,0])*.1)[None])[0]-pm
nm=np.cross(e1,e2); nm/=np.linalg.norm(nm)
if nm@(q-pm)<0: nm=-nm
print('plane',pm.round(3),nm.round(3))
Pc,Tc,_,rim=clip(P,Tm,pm,nm); ring0=set(rim.tolist())
Pc2,Tc2,_,rim2=clip(Pc,Tc,np.zeros(3),np.array([1.,0,0])); Pc2[rim2,0]=0
used,inv=np.unique(Tc2,return_inverse=True); co=Pc2[used]; tri=inv.reshape(-1,3)
d=np.abs((co-pm)@nm); ring=d<1e-6
# keep only the largest connected piece
n2,l2=comps(len(co),tri); s2=np.bincount(l2); big=int(s2.argmax()); print('pieces',np.sort(s2)[-6:])
mk=l2[tri[:,0]]==big; tri=tri[mk]; used,inv=np.unique(tri,return_inverse=True); co=co[used]; tri=inv.reshape(-1,3); ring=ring[used]
pr=np.zeros(len(co)); pr[np.abs(co[:,0])<1e-7]=1; pr[ring]=1
# lips: vertices near the tooth rows keep their shape
from scipy.spatial import cKDTree
dd,_=cKDTree(out[:,:3]).query(co); pr[dd<.05]=np.maximum(pr[dd<.05],.65)
print('half',len(co),len(tri),'ring',ring.sum(),'bbox',co.min(0).round(3),co.max(0).round(3))
np.savez('work/head_half.npz',co=co,tri=tri,protect=pr)
