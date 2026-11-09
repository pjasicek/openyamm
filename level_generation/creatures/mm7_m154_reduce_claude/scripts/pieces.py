#!/usr/bin/env python3
"""Connected pieces of the rest mesh (work/mesh_in.npz) with face count, head-atlas faces, bounds and dominant bones
-> work/piece.npy (piece id per face; the README pieces table). Usage: pieces.py"""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d=np.load('work/mesh_in.npz'); f=d['faces']; v=d['verts']; n=len(v)
e=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]])
_,lab=connected_components(coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(n,n)),directed=False)
fl=lab[f[:,0]]; sizes=np.bincount(fl)
g=np.load('work/groups.npz'); W=g['W']; names=list(g['names'])
uv=d['wuv'].reshape(-1,3,2); headuv=(uv[:,:,0].mean(1)>0.5)
print('head-atlas faces',headuv.sum(), 'u range body', uv[~headuv][:,:,0].max())
for p in np.argsort(-sizes):
    if not sizes[p]: continue
    m=fl==p; vs=np.unique(f[m]); 
    dom=np.bincount(W[vs].argmax(1),minlength=len(names)); top=[ (names[i],int(dom[i])) for i in np.argsort(-dom)[:3] if dom[i]]
    lo=v[vs].min(0); hi=v[vs].max(0)
    print(p,sizes[p],'headuv',int(headuv[m].sum()),'lo',lo.round(3),'hi',hi.round(3),top)
np.save('work/piece.npy',fl)
