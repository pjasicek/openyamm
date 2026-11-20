import sys; sys.path.insert(0,'scripts')
import numpy as np, headfr as H
from meshlib import section
Db=np.load('work/half1.npz'); P=Db['co'].astype(float); T=Db['tri']; cp=Db['comp']; main=np.bincount(cp).argmax()
Tm=T[cp[T[:,0]]==main]; PP=np.vstack([P,P*[-1,1,1]]); TT=np.vstack([Tm,Tm[:,[0,2,1]]+len(P)])
for y in (.60,.625,.65,.68):
    pt=np.array([0,y,.1])
    print('body',y,[(np.round(l['c'],3).tolist(),round(l['per'],2),np.round(l['pts'].min(0),2).tolist(),np.round(l['pts'].max(0),2).tolist()) for l in section(PP,TT,pt,H.PLANE_N) if l['per']>.05])
Hb=np.load('work/head1.npz'); Q=Hb['co']; Th=Hb['tri']; part=Hb['part']; Th=Th[part[Th[:,0]]==1]
for y in (.60,.625,.65,.68,.72):
    pt=np.array([0,y,.1])
    print('head',y,[(np.round(l['c'],3).tolist(),round(l['per'],2),np.round(l['pts'].min(0),2).tolist(),np.round(l['pts'].max(0),2).tolist()) for l in section(Q,Th,pt,H.PLANE_N) if l['per']>.05])
