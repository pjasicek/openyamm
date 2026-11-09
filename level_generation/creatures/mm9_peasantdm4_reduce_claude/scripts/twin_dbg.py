import sys; sys.path.insert(0,'scripts')
import numpy as np, bglbio
from scipy.spatial import cKDTree
doc,b=bglbio.read('before/mm9_peasantdm4.glb')
node=next(n for n in doc['nodes'] if n.get('name')=='PeasantDM4' and 'mesh' in n)
pr=bglbio.prims(doc,b,node['mesh'])[0]
P=pr['POSITION'].astype(float);T=pr['T'];U=pr['TEXCOORD_0'].astype(float);J=pr['JOINTS_0'].astype(int);W=pr['WEIGHTS_0'].astype(float)
_,tp=np.unique(np.round(P,6),axis=0,return_inverse=True);tp=tp.ravel();n=tp.max()+1
X=np.zeros((n,3));X[tp]=P;TF=tp[T]
ua=np.abs((U[T[:,1],0]-U[T[:,0],0])*(U[T[:,2],1]-U[T[:,0],1])-(U[T[:,2],0]-U[T[:,0],0])*(U[T[:,1],1]-U[T[:,0],1]));z=ua<1e-10
fn=np.cross(X[TF[:,1]]-X[TF[:,0]],X[TF[:,2]]-X[TF[:,0]])
N=np.zeros((n,3))
for c in range(3): np.add.at(N,TF[:,c],fn)
N/=np.maximum(np.linalg.norm(N,axis=1,keepdims=True),1e-12)
rep=np.zeros(n,int);rep[tp]=np.arange(len(P))
WD=np.zeros((n,J.max()+1))
for c in range(4): WD[np.arange(n),J[rep,c]]+=W[rep,c]
lv=np.unique(TF[z]); ov=np.unique(TF[~z])
lo=np.setdiff1d(lv,ov)
d,q=cKDTree(X).query(X[lo],k=8)
stats={'none_within':0,'normal_fail':0,'along_fail':0,'w_fail':0,'ok':0}
for i,v in enumerate(lo):
    best=None
    for dd,j in zip(d[i],q[i]):
        if j==v or dd<1e-7 or dd>0.0042 or j in lo: continue
        dv=X[j]-X[v]; L=np.linalg.norm(dv)
        r=[N[v]@N[j]<-0.3, abs(dv@N[v])>0.7*L, np.abs(WD[v]-WD[j]).sum()<=0.35]
        if all(r): best='ok'; break
        best = best or ('normal_fail' if not r[0] else 'along_fail' if not r[1] else 'w_fail')
    stats[best or 'none_within']+=1
print(stats)
front=-np.ones(n,int)
dd_,qq_=cKDTree(X).query(X,k=10)
for v in range(n):
    for dd,j in zip(dd_[v],qq_[v]):
        if j==v or dd<1e-7 or dd>0.0042: continue
        dv=X[j]-X[v]; L=np.linalg.norm(dv)
        if N[v]@N[j]<-0.3 and abs(dv@N[v])>0.7*L and np.abs(WD[v]-WD[j]).sum()<=0.35 and (X[j]-X[v])@N[j]>0:
            front[v]=j; break
fall={}
for f,t in enumerate(TF): fall.setdefault(frozenset(t.tolist()),[]).append(f)
res={'no_front':0,'tri_hit':0,'miss':0}
miss=[]
for f in np.flatnonzero(z):
    t=TF[f]
    if (front[t]<0).any(): res['no_front']+=1; continue
    k=frozenset(front[t].tolist())
    if len(k)<3: res['miss']+=1; miss.append(f); continue
    if k in fall: res['tri_hit']+=1
    else: res['miss']+=1; miss.append(f)
print(res)
# for missed: are the 3 front vertices connected (edges exist)?
E=set()
for t in TF:
    for a,b2 in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])): E.add((min(a,b2),max(a,b2)))
ce=[sum(((min(a,b2),max(a,b2)) in E) for a,b2 in ((front[TF[f][0]],front[TF[f][1]]),(front[TF[f][1]],front[TF[f][2]]),(front[TF[f][2]],front[TF[f][0]]))) for f in miss]
print('missed faces: front-edges present 0/1/2/3', np.bincount(ce,minlength=4))
