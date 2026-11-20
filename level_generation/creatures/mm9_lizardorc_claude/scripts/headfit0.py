import sys; sys.path.insert(0,'scripts')
import numpy as np, json
from loadglb import *
from PIL import Image, ImageDraw
A,s,sx,tx=[float(x) for x in sys.argv[1:5]]; 
D=np.load('work/mhead0.npz'); P,T=D['P'].astype(float),D['T']
a=np.radians(A); c,sn=np.cos(a),np.sin(a)
def F(p):
    q=p*[sx,s,s]; y=q[:,1]*c+q[:,2]*sn; z=-q[:,1]*sn+q[:,2]*c; return np.c_[q[:,0],y,z]
tip=F(np.array([[0,-.012,.5]]))[0]; goal=np.array([0,.70,.47])
t=goal-tip; t[2]+=tx
Q=F(P)+t
print('t',t.round(3),'bbox',Q.min(0).round(3),Q.max(0).round(3))
Am,Tm,_=load('source/true/lizardorc_true.glb'); B=np.load('work/half1.npz'); Bq=B['co']; Bt=B['tri']
Bq2=np.vstack([Bq,Bq*[-1,1,1]]); Bt2=np.vstack([Bt,Bt+len(Bq)])
W=700;H=700;sc=600;cy=.45
def proj(p,ax): return np.c_[W/2+p[:,ax]*sc-(0 if ax==0 else 100), H/2-(p[:,1]-cy)*sc]
im=Image.new('RGB',(W*2,H),(30,30,30)); d=ImageDraw.Draw(im)
for k,(ax,off) in enumerate(((0,0),(2,W))):
    a_=proj(Am,ax)+[off,0]
    for tr in Tm: d.polygon([tuple(a_[i]) for i in tr],fill=(120,50,50))
    b=proj(Bq2,ax)+[off,0]
    for tr in Bt2: d.polygon([tuple(b[i]) for i in tr],outline=(90,90,160))
    b=proj(Q,ax)+[off,0]
    for tr in T[::2]: d.polygon([tuple(b[i]) for i in tr],outline=(120,255,120))
im.save('review/ref/hfit.png')
