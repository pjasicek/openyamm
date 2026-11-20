"""One-channel enhanced tunic coverage and native nonlinear palette lighting."""
import numpy as np
from PIL import Image
LUMA=np.array([.2126,.7152,.0722])

def coverage(image):
    from scipy import ndimage
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    hsv=np.array(image.convert("RGB").convert("HSV")).astype(float);h=hsv[:,:,0]*360/255;s=hsv[:,:,1]/255
    # Orange fabric is redder than protected olive-brown leather, bow and gold.
    w=np.clip((r-1.50*g)/.045,0,1)*np.clip((31-h)/5,0,1)*np.clip((s-.30)/.12,0,1)
    # Reject isolated narrow orange arrow shafts and leather glints; retain broad cloth regions.
    seeds=ndimage.distance_transform_edt(w>.6)>2
    labels,count=ndimage.label(seeds);sizes=np.bincount(labels.ravel());sizes[0]=0
    keep=sizes>=max(12,sizes.max()*.015)
    support=ndimage.binary_dilation(keep[labels],iterations=3)
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
    base=colors[767];r,g,b=base.T
    selected=(counts>0)&(np.arange(256)>0)&(np.arange(256)<=35)
    y=(base@LUMA)*255;out={}
    for p in [766,768]:
        curve=[]
        for level in range(256):
            d=(y[selected]-level)**2;w=counts[selected]*np.exp(-(d-d.min())/32)
            curve.append((w@colors[p][selected]/w.sum()).tolist())
        out[p]=curve
    return out

def recolor(image,mask,palette,config,vectors):
    if palette==767:return image.copy()
    a=np.array(image);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255
    coefficients=np.array(config["native_tunic_rgb_affine"]["coefficients"][str(palette)])
    target=np.clip(c@coefficients[:3]+coefficients[3],0,1)
    out=c*(1-w[:,:,None])+target*w[:,:,None]
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8)
    return Image.fromarray(a)
