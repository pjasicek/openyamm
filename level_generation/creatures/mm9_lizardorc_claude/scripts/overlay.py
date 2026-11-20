"""Mesh npz against MM9 (filled): overlay.py <npz> <out.png> [mirror]"""
import sys; sys.path.insert(0,'scripts')
import numpy as np
from loadglb import *
from PIL import Image, ImageDraw
D=np.load(sys.argv[1]); Q=D['co'].astype(float); Tq=D['tri']
if len(sys.argv)>3: Tq=np.vstack([Tq,Tq+len(Q)]); Q=np.vstack([Q,Q*[-1,1,1]])
Am,Tm,_=load('source/true/lizardorc_true.glb')
W=700;H=900;sc=420
def proj(p,ax): return np.c_[W/2+p[:,ax]*sc, H/2-p[:,1]*sc]
im=Image.new('RGB',(W*2,H),(30,30,30)); d=ImageDraw.Draw(im)
for k,(ax,off) in enumerate(((0,0),(2,W))):
    a=proj(Am,ax)+[off,0]
    for t in Tm: d.polygon([tuple(a[i]) for i in t],fill=(130,50,50))
    b=proj(Q,ax)+[off,0]
    for t in Tq: d.polygon([tuple(b[i]) for i in t],outline=(120,255,120))
im.save(sys.argv[2])
