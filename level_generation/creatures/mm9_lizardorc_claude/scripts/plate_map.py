"""Front splat of the body paint, shell 11 and the hide around the neck, in fit coordinates, from the final pages. Writes review/ref/pm_shell.png, pm_neck.png"""
import sys, numpy as np
sys.path.insert(0,'scripts')
from PIL import Image, ImageDraw
import rast
J=np.load('work/joined.npz'); U=np.load('work/uv.npz'); Pg=np.load('work/pages.npz',allow_pickle=True); co,part=J['co'],J['part']; up=J['co_up']
ub2,page,own=Pg['ub2'],Pg['page'],Pg['own']; S=2048
ob=U['ob']; pf=part[ob].max(1)
def splat(sel,axes,lo,hi,out,sc):
    W=int((hi[0]-lo[0])*sc); H=int((hi[1]-lo[1])*sc); im=np.zeros((H,W,3),np.uint8)+60; z=-np.ones((H,W))*9
    for p in range(2):
        ids=np.where(own&(page==p)&sel)[0]
        if not len(ids): continue
        F,B=rast.raster(ub2[ids],S); Q,m=rast.positions(F,B,co[ob[ids]]); c=np.asarray(Image.open(f'textures/body{p}_final.png').convert('RGB'))
        q=Q[m]; xs=((q[:,axes[0]]-lo[0])*sc).astype(int); ys=((hi[1]-q[:,axes[1]])*sc).astype(int); k=(xs>=0)&(xs<W)&(ys>=0)&(ys<H)
        d=q[:,2]
        o=np.argsort(d[k]); im[ys[k][o],xs[k][o]]=c[m][k][o]
    I=Image.fromarray(im); dr=ImageDraw.Draw(I)
    for v in np.arange(np.ceil(lo[1]*20)/20,hi[1],.05):
        y=(hi[1]-v)*sc; dr.line([0,y,8,y],fill=(255,255,0)); dr.text((10,y-5),f'{v:.2f}',fill=(255,255,0))
    for v in np.arange(np.ceil(lo[0]*20)/20,hi[0],.05):
        x=(v-lo[0])*sc; dr.line([x,0,x,8],fill=(0,255,255)); dr.text((x+1,10),f'{v:.2f}',fill=(0,255,255))
    I.save(out)
splat(pf==11,(0,1),(0,.2),(.09,.53),'review/ref/pm_shell.png',2400)
splat(pf==0,(0,1),(0,.42),(.34,.68),'review/ref/pm_neck.png',2000)
print('ok')
