"""Ghost enhanced material masks and native-used palette interpolation."""
import numpy as np
from PIL import Image
from scipy import ndimage
REGIONS={'mask_r':'Charcoal violet tabard','mask_g':'Green eyes','mask_b':'Unused','mask_a':'Unused'}
LUMA=np.array([.2126,.7152,.0722])
def coverage(image):
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    hsv=np.array(image.convert('RGB').convert('HSV')).astype(float);h=hsv[:,:,0]*360/255;s=hsv[:,:,1]/255
    eye=np.clip((g-np.maximum(r,b)-.03)/.10,0,1)*np.clip((g-.45)/.15,0,1)
    ys=np.where(a[:,:,3]>96)[0]
    if len(ys):eye[np.arange(a.shape[0])>ys.min()+.4*(ys.max()-ys.min())]=0
    cloth=np.clip((b-g-.001)/.005,0,1)*np.clip((b-r+.008)/.01,0,1)*np.clip((.55-b)/.12,0,1)*(1-eye)
    # Accept coherent violet fabric interiors, not cool antialiased shroud edges.
    seeds=(cloth>.6)&(a[:,:,3]>=250)&(ndimage.distance_transform_edt(a[:,:,3]>=250)>3)
    labels,count=ndimage.label(seeds)
    sizes=np.bincount(labels.ravel());sizes[0]=0
    keep=sizes>=max(24, sizes.max()*.08)
    coherent=keep[labels]
    support=ndimage.binary_dilation(coherent,iterations=3)
    cloth*=support
    holes=ndimage.binary_fill_holes(cloth>.35)
    cloth=np.maximum(cloth,holes.astype(float))*(1-eye)
    # Neutral shroud highlights/tips must never inherit the tabard palette.
    cloth*=np.clip((b-np.minimum(r,g)-.08*b)/np.maximum(.04*b,.001),0,1)
    w=np.stack([cloth,eye,np.zeros_like(r),np.zeros_like(r)],2)
    core=ndimage.distance_transform_edt(a[:,:,3]>=250)>3
    if core.any():
        d,ix=ndimage.distance_transform_edt(~core,return_indices=True);edge=(a[:,:,3]>0)&~core&(d<=5);w[edge]=w[ix[0],ix[1]][edge]
    w/=np.maximum(1,w.sum(2,keepdims=True));out=np.floor(w*255).astype(np.uint8);out[a[:,:,3]==0]=0
    return Image.fromarray(out,'RGBA')
def fit(config,inv,repo):
    colors={int(p):np.fromfile(repo/f'assets_dev/worlds/mm6/textures/pal{p}.act',np.uint8)[:768].reshape(256,3)/255 for p in inv['variants']}
    counts=np.zeros(256)
    for src in inv['sources'].values():counts+=np.bincount(np.array(Image.open(repo/src['path'])).ravel(),minlength=256)
    counts[0]=0;base=colors[742];r,g,b=base.T
    selections=[(b>r+.005)&(b>g+.015),(g>r+.05)&(g>b+.05),counts>0,counts>0]
    y=base@LUMA*255;out={}
    for pal in [743,744]:
        curves=[]
        for sel in selections:
            sel&=counts>0;curve=[]
            for level in range(256):
                d=(y[sel]-level)**2;w=counts[sel]*np.exp(-(d-d.min())/32);curve.append((w@colors[pal][sel]/w.sum()).tolist())
            curves.append(curve)
        out[pal]=curves
    return out
def recolor(image,mask,palette,config,vectors):
    if palette==742:return image.copy()
    a=np.array(image);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255;level=np.clip(np.round(c@LUMA*255),0,255).astype(int)
    out=c*(1-w.sum(2,keepdims=True))
    for i in range(4):out+=w[:,:,i,None]*np.array(vectors[palette][i])[level]
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8);return Image.fromarray(a)
