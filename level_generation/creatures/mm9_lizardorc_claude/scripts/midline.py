import sys; sys.path.insert(0,'scripts')
import numpy as np, headfr as H
D=np.load('work/head_half.npz'); co,tri=D['co'],D['tri']
S=np.load('work/head_sites.npz')['s']
f=H.F(co); fs=H.F(S[:,:3])
print('upper',np.round(fs[S[:,7]==1][::3],3).tolist()); print('lower',np.round(fs[S[:,7]==0][::3],3).tolist())
# centre line x<0.012: y vs z
m=co[:,0]<.008
q=f[m]; o=np.argsort(q[:,2]); 
for z in np.arange(-.18,.5,.04):
    k=np.abs(q[:,2]-z)<.012
    print(round(z,2),np.round(np.sort(q[k,1]),3).tolist()[:14])
