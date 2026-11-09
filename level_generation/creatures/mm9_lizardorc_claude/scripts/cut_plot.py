import numpy as np
from PIL import Image, ImageDraw
D=np.load('work/cutlass.npz'); P,T=D['P'].astype(float),D['T']
c=P.mean(0); u,s,vt=np.linalg.svd(P-c); a=vt[0]; b=vt[1]; n=vt[2]
if a[2]<0: a=-a          # toward the tip (+z)
if b@np.array([.9,.39,-.19])<0: b=-b
n=np.cross(a,b)
Q=np.c_[(P-c)@a,(P-c)@b,(P-c)@n]
print('frame c',c.round(4),'a',a.round(4),'b',b.round(4),'n',n.round(4)); print('bbox',Q.min(0).round(3),Q.max(0).round(3))
S=1500; sc=1400; ox=720; oy=500
im=Image.new('RGB',(S,1000),(30,30,30)); d=ImageDraw.Draw(im)
pr=lambda q:(ox+q[0]*sc,oy-q[1]*sc)
for t in T: d.polygon([pr(Q[i]) for i in t],outline=(200,200,120))
for x in np.arange(-.5,.6,.05):
    d.line([ox+x*sc,0,ox+x*sc,1000],fill=(70,70,90)); d.text((ox+x*sc+2,2),f'{x:.2f}',fill=(150,200,255))
for y in np.arange(-.3,.35,.05):
    d.line([0,oy-y*sc,S,oy-y*sc],fill=(70,70,90)); d.text((2,oy-y*sc),f'{y:.2f}',fill=(150,200,255))
im.save('review/ref/cut_plot.png')
np.savez('work/cut_frame.npz',c=c,a=a,b=b,n=n,Q=Q,T=T)
# side view
im=Image.new('RGB',(S,500),(30,30,30)); d=ImageDraw.Draw(im); pr=lambda q:(ox+q[0]*sc,250-q[2]*sc)
for t in T: d.polygon([pr(Q[i]) for i in t],outline=(200,200,120))
im.save('review/ref/cut_plot2.png')
