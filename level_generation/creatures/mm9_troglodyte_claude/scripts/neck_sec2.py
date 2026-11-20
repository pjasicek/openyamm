import sys, numpy as np
sys.path.insert(0,'scripts')
from meshlib import section; from PIL import Image, ImageDraw
D=np.load('work/body1.npz'); P,T=D['co'],D['tri']
H=np.load('work/head_tmp.npz'); Q,Th=H['co'],H['tri']
a=np.radians(25.8); n=np.array([0,-np.sin(a),np.cos(a)])
im=Image.new('RGB',(4*520,2*520),(30,30,30)); d=ImageDraw.Draw(im)
top=np.array([0,.499,-.091]);
for k,off in enumerate([-.04,0,.02,.04,.06,.08,.1,.12]):
    ox,oy=(k%4)*520+260,(k//4)*520+260; p0=top+n*off+np.array([0,-.13,-.0])
    u=np.array([1.,0,0]); v=np.cross(n,u)
    for M,TT,col in ((P,T,(255,255,0)),(Q,Th,(0,255,255))):
        for L in section(M,TT,p0,n):
            q=L['pts']-p0
            for pp in q: d.ellipse([ox+pp@u*420-1,oy-pp@v*420-1,ox+pp@u*420+1,oy-pp@v*420+1],fill=col)
    d.text((ox-250,oy-250),f'off={off} p0={np.round(p0,3)}',fill=(255,255,255))
im.save('work/necksec2.png')
