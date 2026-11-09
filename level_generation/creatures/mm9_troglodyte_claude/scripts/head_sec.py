import sys, numpy as np
sys.path.insert(0,'scripts')
from loadglb import *; from meshlib import section; from PIL import Image, ImageDraw
P,T,_=load('meshy/head_v1/model_urls_glb.glb'); P,T,_,_=weld(P,T); nc,l=comps(len(P),T); sz=np.bincount(l); m=np.argmax(sz); T=T[(l==m)[T[:,0]]]
xs=[-.003,-.05,-.1,-.16,-.22,-.28]
im=Image.new('RGB',(3*640,2*640),(30,30,30)); d=ImageDraw.Draw(im)
for k,x in enumerate(xs):
    ox,oy=(k%3)*640+320,(k//3)*640+320
    for L in section(P,T,np.array([x,0,0]),np.array([1.,0,0])):
        for q in L['pts']: d.ellipse([ox+q[2]*300-1,oy-q[1]*300-1,ox+q[2]*300+1,oy-q[1]*300+1],fill=(255,255,0))
    d.text((ox-310,oy-310),f'x={x}',fill=(255,255,255))
im.save('work/hsec.png')
