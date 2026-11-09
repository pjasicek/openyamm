import sys, numpy as np
sys.path.insert(0,'scripts')
from loadglb import *
from PIL import Image, ImageDraw
D=np.load(sys.argv[1]); Q,T=D['co'],D['tri']
A,TA,_=load('source/true/trog2_true.glb')
def tf(d,Q,T,view):
    for t in T: d.polygon([view(Q[i]) for i in t],fill=255)
def sv(q): return (560+q[2]*600, 480-q[1]*600)
def fv(q): return (1500+q[0]*600, 480-q[1]*600)
a=Image.new('L',(2000,960),0); b=Image.new('L',(2000,960),0); da,db=ImageDraw.Draw(a),ImageDraw.Draw(b)
tf(da,A,TA,sv); tf(da,A,TA,fv); tf(db,Q,T,sv); tf(db,Q,T,fv)
Image.merge('RGB',(a,b,Image.new('L',(2000,960),30))).save(sys.argv[2])
