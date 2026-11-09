import sys; sys.path.insert(0,'scripts')
import numpy as np
from meshlib import section
D=np.load('work/meshy0.npz'); P,T,l=D['P'],D['T'],D['l']
sz=np.bincount(l); main=np.argmax(sz)
S=2.015;Q=P*S; Q[:,1]+=-.926-Q[:,1].min(); Q[:,2]-=.40
Tm=T[l[T[:,0]]==main]
print('main bbox',Q[l==main].min(0).round(3),Q[l==main].max(0).round(3))
print('leg by y (left, x>0)')
for y in np.arange(.2,-.93,-.08):
    L=section(Q,Tm,np.array([0,y,0.]),np.array([0,1.,0]))
    L=[a for a in L if a['c'][0]>0.02 and a['per']>.05]
    print(round(y,2),[ (np.round(a['c'],3).tolist(),round(a['per'],2)) for a in L][:4])
print('arm along dir')
s=np.array([.24,.60,.03]);e=np.array([.56,.08,.05]);u=(e-s)/np.linalg.norm(e-s)
for t in np.arange(-.05,.85,.06):
    L=section(Q,Tm,s+u*t,u)
    L=[a for a in L if a['c'][0]>.12 and a['per']>.03 and np.linalg.norm(a['c']-(s+u*t))<.4]
    print(round(t,2),[ (np.round(a['c'],3).tolist(),round(a['per'],2)) for a in L][:4])
print('tail by z')
for z in np.arange(-.15,-1.45,-.1):
    L=section(Q,Tm,np.array([0,0,z]),np.array([0,0,1.]))
    L=[a for a in L if abs(a['c'][0])<.05 and a['c'][1]<.3]
    print(round(z,2),[ (np.round(a['c'],3).tolist(),round(a['per'],2)) for a in L][:3])
print('neck/torso by y')
for y in np.arange(.2,.9,.06):
    L=section(Q,Tm,np.array([0,y,0.]),np.array([0,1.,0]))
    L=[a for a in L if abs(a['c'][0])<.05]
    print(round(y,2),[ (np.round(a['c'],3).tolist(),round(a['per'],2)) for a in L][:3])
