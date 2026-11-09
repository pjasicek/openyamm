"""One-channel enhanced blue waist skirt coverage and native nonlinear palette lighting."""
import numpy as np
from PIL import Image
LUMA=np.array([.2126,.7152,.0722])

def coverage(image):
    from scipy import ndimage
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    w=np.clip((b-np.maximum(r,g)-.005)/.018,0,1)
    # Native blue gemstones do not change; accept only the large coherent skirt.
    seeds=ndimage.distance_transform_edt(w>.6)>2
    labels,count=ndimage.label(seeds);sizes=np.bincount(labels.ravel());sizes[0]=0
    support=ndimage.binary_dilation((sizes>=max(32,sizes.max()*.10))[labels],iterations=4)
    w*=support
    core=ndimage.distance_transform_edt(a[:,:,3]>=250)>3
    if core.any():
        d,ix=ndimage.distance_transform_edt(~core,return_indices=True);edge=(a[:,:,3]>0)&~core&(d<=5);w[edge]=w[ix[0],ix[1]][edge]
    w[a[:,:,3]==0]=0
    return Image.fromarray(np.round(w*255).astype(np.uint8),'L')

def fit(config,inv,repo):
    colors={int(p):np.fromfile(repo/f'assets_dev/worlds/mm6/textures/pal{p}.act',np.uint8)[:768].reshape(256,3)/255 for p in inv['variants']}
    counts=np.zeros(256)
    for n,s in inv['sources'].items():
        if s['referenced']:counts+=np.bincount(np.array(Image.open(repo/s['path'])).ravel(),minlength=256)
    base=colors[771];r,g,b=base.T
    selected=(counts>0)&(np.arange(256)>0)&(b>r+.02)&(b>g+.02)
    y=(base@LUMA)*255;out={}
    for p in [772,773]:
        curve=[]
        for level in range(256):
            d=(y[selected]-level)**2;w=counts[selected]*np.exp(-(d-d.min())/32)
            curve.append((w@colors[p][selected]/w.sum()).tolist())
        out[p]=curve
    return out

def recolor(image,mask,palette,config,vectors):
    if palette==771:return image.copy()
    a=np.array(image);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255
    level=np.clip(np.round((c@LUMA)*255),0,255).astype(int)
    out=c*(1-w[:,:,None])+np.array(vectors[palette])[level]*w[:,:,None]
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8)
    return Image.fromarray(a)
