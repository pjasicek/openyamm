import sys
import numpy as np
from PIL import Image
sys.path.insert(0,'../claude_shared/floor')
from glb_pose import Glb, Model
import json
g=Glb('export/mm9_banshee.glb'); m=Model(g); doc=g.json
mesh=next(x for x in doc['meshes'] if x['name']=='Banshee')
nm=[doc['materials'][p['material']]['name'].rsplit('_',1)[0] for p in mesh['primitives']]
print(sorted({doc['materials'][p['material']].get('doubleSided',False) for p in mesh['primitives']}))
c,t,az,el,D=sys.argv[1],float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4]),float(sys.argv[5])
S=m.skinned_positions(m.world(m.sample(c,t)))
kn=nm.index('BansheeNeck'); tgt=np.array(S[kn][0].mean(0))
a,e=np.radians(az),np.radians(el)
eye=tgt+D*np.array([np.sin(a)*np.cos(e),np.sin(e),np.cos(a)*np.cos(e)])
f=(tgt-eye)/D; r=np.cross(f,[0,1,0]); r/=np.linalg.norm(r); u=np.cross(r,f)
W,H=480,360; fov=1.0/np.tan(np.radians(20))
kh=nm.index('BansheeHead'); UV=g.accessor(mesh['primitives'][kh]['attributes']['TEXCOORD_0']); rx,ry,rs=json.load(open('scripts/bag_rect.json'))
isbag=(np.abs(UV[:,0]-(rx+rs/2)/1024)<rs/2048+0.002)&(np.abs(UV[:,1]-(ry+rs/2)/1024)<rs/2048+0.002)
BG=[]
Z=np.full((H,W),1e9); Id=np.zeros((H,W),np.int32)
for k,(P,T) in enumerate(S):
    T=np.asarray(T).reshape(-1,3)
    q=P-eye; x=q@r; y=q@u; z=q@f
    sx=W/2+x/z*fov*H/2; sy=H/2-y/z*fov*H/2
    for tri in T:
        A,B,C=tri
        if min(z[A],z[B],z[C])<0.02: continue
        ax,ay,bx,by,cx,cy=sx[A],sy[A],sx[B],sy[B],sx[C],sy[C]
        d=(bx-ax)*(cy-ay)-(cx-ax)*(by-ay)
        if abs(d)<1e-9: continue
        x0,x1=int(max(min(ax,bx,cx),0)),int(min(max(ax,bx,cx)+1,W)); y0,y1=int(max(min(ay,by,cy),0)),int(min(max(ay,by,cy)+1,H))
        if x0>=x1 or y0>=y1: continue
        xs,ys=np.meshgrid(np.arange(x0,x1)+.5,np.arange(y0,y1)+.5)
        l1=((xs-ax)*(cy-ay)-(cx-ax)*(ys-ay))/d; l2=((bx-ax)*(ys-ay)-(xs-ax)*(by-ay))/d; l0=1-l1-l2
        ok=(l0>=0)&(l1>=0)&(l2>=0)
        if not ok.any(): continue
        zz=l0*z[A]+l1*z[B]+l2*z[C]
        front=d<0        # screen y is down, CCW in glTF appears with negative d
        val=(k+1)*(1 if front else -1)
        if k==kh and isbag[A] and isbag[B] and isbag[C]: val=99
        yy=(ys[ok]).astype(int); xx=(xs[ok]).astype(int); zv=zz[ok]
        better=zv<Z[yy,xx]; Z[yy[better],xx[better]]=zv[better]; Id[yy[better],xx[better]]=val
pal={0:(40,40,40)}
base={'BansheeNeck':(230,60,60),'BansheeHead':(240,170,60),'Banshee':(70,110,240)}
img=np.zeros((H,W,3),np.uint8)
for v in np.unique(Id):
    if v==0: col=(40,40,40)
    elif v==99: col=(255,0,255)
    else:
        n=nm[abs(v)-1]; col=base.get(n,(90,190,90))
        if v<0: col=tuple(255-x//3 for x in col)    # first hit is a back face: pale
    img[Id==v]=col
Image.fromarray(img).save(sys.argv[6])
print('BAGPX',int((Id==99).sum()),{nm[abs(v)-1][7:]+('-back' if v<0 else ''):int((Id==v).sum()) for v in np.unique(Id) if v and v!=99 and 'Neck' in nm[abs(v)-1]})
