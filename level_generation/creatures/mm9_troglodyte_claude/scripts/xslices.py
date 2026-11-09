import sys, numpy as np
sys.path.insert(0,'scripts')
from loadglb import *; from PIL import Image, ImageDraw
P,T,_=load('meshy/smart_v1/model_urls_glb.glb'); P,T,_,_=weld(P,T); nc,l=comps(len(P),T); T=T[(l==0)[T[:,0]]]
S=1.24; P=P*S; P[:,1]+= -0.594 - P[:,1].min()
sys.path.insert(0,'scripts'); from meshlib import section
xs=[.05,.12,.18,.22,.26,.3,.34,.38]
im=Image.new('RGB',(4*420,2*420),(30,30,30)); d=ImageDraw.Draw(im)
for k,x in enumerate(xs):
    ox,oy=(k%4)*420+210,(k//4)*420+210
    for L in section(P,T,np.array([x,0,0]),np.array([1.,0,0])):
        for q in L['pts']: d.ellipse([ox+q[2]*170-1,oy-q[1]*170-1,ox+q[2]*170+1,oy-q[1]*170+1],fill=(255,255,0))
    d.text((ox-200,oy-200),f'x={x}',fill=(255,255,255))
im.save('work/xslices.png')
