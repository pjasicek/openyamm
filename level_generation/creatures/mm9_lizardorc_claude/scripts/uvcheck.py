import numpy as np
U=np.load('work/uv.npz'); J=np.load('work/joined.npz'); co=J['co']
for k,(u,o) in {'body':(U['ub'],U['ob']),'head':(U['uh'],U['oh'])}.items():
    P=co[o]; a3=np.linalg.norm(np.cross(P[:,1]-P[:,0],P[:,2]-P[:,0]),axis=1)/2; a2=np.abs((u[:,1,0]-u[:,0,0])*(u[:,2,1]-u[:,0,1])-(u[:,2,0]-u[:,0,0])*(u[:,1,1]-u[:,0,1]))/2
    d=np.sqrt(a2/np.maximum(a3,1e-9)); w=a3/a3.sum(); q=np.argsort(d); c=np.cumsum(w[q]); p=lambda x:d[q][np.searchsorted(c,x)]
    print(k,'density p10/50/90',round(p(.1),3),round(p(.5),3),round(p(.9),3),'spread',round(p(.9)/p(.1),2),'zero-area',int((a2<1e-9).sum()), 'uv range',u.min().round(3),u.max().round(3))
