import sys; sys.path.insert(0,'scripts')
import numpy as np
from loadglb import *
from PIL import Image, ImageDraw
P,T,_=load('meshy/smart_v1/model_urls_glb.glb'); P0,T0=P,T
P,T,_,_=weld(P,T); print(len(P),len(T))
nc,l=comps(len(P),T); sz=np.bincount(l)
S=2.015; Q=P*S
Q[:,1]+= -.926-Q[:,1].min(); Q[:,2]-=.40
o=np.argsort(-sz)
for c in o[:95]:
    q=Q[l==c]; 
    print(c,sz[c],np.round(q.min(0),2).tolist(),np.round(q.max(0),2).tolist())
# overlay on MM9
sys.path.insert(0,'scripts')
Am,Tm,_=load('source/true/lizardorc_true.glb')
W=700;H=900;sc=420
def proj(p,ax): return np.c_[W/2+p[:,ax]*sc, H/2-p[:,1]*sc]
im=Image.new('RGB',(W*2,H),(30,30,30)); d=ImageDraw.Draw(im)
for k,(ax,off) in enumerate(((0,0),(2,W))):
    # MM9 triangles filled
    a=proj(Am,ax)+[off,0]
    for t in Tm: d.polygon([tuple(a[i]) for i in t],fill=(120,50,50))
    b=proj(Q,ax)+[off,0]
    for x,y in b: im.putpixel((int(min(max(x,0),W*2-1)),int(min(max(y,0),H-1))),(120,255,120))
im.save('review/ref/overlay0.png')
np.savez('work/meshy0.npz',P=P,T=T,l=l)
