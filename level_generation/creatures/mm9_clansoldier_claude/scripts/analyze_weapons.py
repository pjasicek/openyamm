import numpy as np
for n in ('sword','shield'):
    P=np.load(f'work/{n}_verts.npy').astype(float); idx=np.load(f'work/{n}_idx.npy'); uv=np.load(f'work/{n}_uv.npy')
    # unique
    U=np.unique(P.round(4),axis=0); print(n,'unique',len(U)); c=U.mean(0); w,V=np.linalg.eigh(np.cov((U-c).T)); print(' centre',c.round(3),'axes',V[:,::-1].T.round(3),'ext',np.sqrt(w[::-1]).round(3))
    Q=(U-c)@V[:,::-1]
    o=np.argsort(Q[:,0]); print(np.c_[Q[o]].round(3).tolist())
