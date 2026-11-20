"""One-channel enhanced whole slime coverage and native nonlinear palette lighting."""
import numpy as np
from PIL import Image
LUMA=np.array([.2126,.7152,.0722])

def coverage(image):
    a=np.array(image)
    return Image.fromarray(np.where(a[:,:,3]>0,255,0).astype(np.uint8),'L')


def fit(config,inv,repo):
    colors={int(p):np.fromfile(repo/f'assets_dev/worlds/mm6/textures/pal{p}.act',np.uint8)[:768].reshape(256,3)/255 for p in inv['variants']}
    counts=np.zeros(256)
    for n,s in inv['sources'].items():
        if s['referenced']:counts+=np.bincount(np.array(Image.open(repo/s['path'])).ravel(),minlength=256)
    base=colors[780];r,g,b=base.T
    selected=(counts>0)&(np.arange(256)>0)&(g>=r)&(g>=b)
    y=(base@LUMA)*255;out={}
    for p in [781,782]:
        curve=[]
        for level in range(256):
            d=(y[selected]-level)**2;w=counts[selected]*np.exp(-(d-d.min())/32)
            curve.append((w@colors[p][selected]/w.sum()).tolist())
        out[p]=curve
    return out

def recolor(image,mask,palette,config,vectors):
    if palette==780:return image.copy()
    a=np.array(image);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255
    level=np.clip(np.round((c@LUMA)*255),0,255).astype(int)
    out=c*(1-w[:,:,None])+np.array(vectors[palette])[level]*w[:,:,None]
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8)
    return Image.fromarray(a)
