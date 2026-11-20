import sys, numpy as np
sys.path.insert(0,'scripts')
from loadglb import *
from PIL import Image, ImageDraw
from pygltflib import GLTF2
P,T,_=load('meshy/smart_v1/model_urls_glb.glb'); P,T,_,_=weld(P,T)
S=1.24; P=P*S; P[:,1]+= -0.594 - P[:,1].min()
A,TA,_=load('source/true/trog2_true.glb')
def tri_fill(d,Q,T,col,view):
    for t in T:
        d.polygon([view(Q[i]) for i in t],fill=col)
def sv(q,cx=500): return (cx+q[2]*600, 480-q[1]*600)
def fv(q,cx=1500): return (cx+q[0]*600, 480-q[1]*600)
im=Image.new('RGB',(2000,960),(40,40,40)); 
a=Image.new('L',(2000,960),0); b=Image.new('L',(2000,960),0)
da,db=ImageDraw.Draw(a),ImageDraw.Draw(b)
shift=float(sys.argv[1]) if len(sys.argv)>1 else 0
Q=P.copy(); Q[:,2]+=shift
tri_fill(da,A,TA,255,sv); tri_fill(da,A,TA,255,fv); tri_fill(db,Q,T,255,sv); tri_fill(db,Q,T,255,fv)
im=Image.merge('RGB',(a,b,Image.new('L',(2000,960),30))); im.save('work/overlay.png')
