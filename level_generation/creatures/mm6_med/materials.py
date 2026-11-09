"""Medusa enhanced material masks and native-used palette interpolation."""
import numpy as np
from PIL import Image
from scipy import ndimage
REGIONS={'mask_r':'Navy armor','mask_g':'Neutral belly plates','mask_b':'Unused','mask_a':'Unused'}
LUMA=np.array([.2126,.7152,.0722])
def coverage(image, armor_max_y=None):
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    armor=np.clip((b-np.maximum(r,g)-.003)/.016,0,1)
    belly=np.clip((.04-(c.max(2)-c.min(2)))/.025,0,1)*(1-armor)
    blue_y=np.where((armor>.9)&(a[:,:,3]>128))[0]
    if len(blue_y):belly[np.arange(a.shape[0])<blue_y.min()]=0
    labels,count=ndimage.label((belly>.5)&(a[:,:,3]>128));sizes=np.bincount(labels.ravel());sizes[0]=0
    belly*=ndimage.binary_dilation((sizes>=32)[labels],iterations=2)
    if armor_max_y is not None:
        # Explicitly reviewed torso boundary: blue-lit belly plates are not armor.
        below = np.arange(a.shape[0])[:, None] > armor_max_y
        belly = np.where(below, np.maximum(belly, armor), belly)
        armor = np.where(below, 0, armor)
    w=np.stack([armor,belly,np.zeros_like(r),np.zeros_like(r)],2)
    core=ndimage.distance_transform_edt(a[:,:,3]>=250)>3
    if core.any():
        d,ix=ndimage.distance_transform_edt(~core,return_indices=True);edge=(a[:,:,3]>0)&~core&(d<=5);w[edge]=w[ix[0],ix[1]][edge]
    w/=np.maximum(1,w.sum(2,keepdims=True));out=np.floor(w*255).astype(np.uint8);out[a[:,:,3]==0]=0
    return Image.fromarray(out,'RGBA')
def fit(config,inv,repo):
    colors={int(p):np.fromfile(repo/f'assets_dev/worlds/mm6/textures/pal{p}.act',np.uint8)[:768].reshape(256,3)/255 for p in inv['variants']}
    counts=np.zeros(256)
    for src in inv['sources'].values():counts+=np.bincount(np.array(Image.open(repo/src['path'])).ravel(),minlength=256)
    counts[0]=0;base=colors[250];r,g,b=base.T
    idx=np.arange(256)
    selections=[(idx>=180)&(b>r+.025)&(b>g+.025),(idx>=180)&(idx<=237)&((base.max(1)-base.min(1))<.01),counts>0,counts>0]
    y=base@LUMA*255;out={}
    for pal in [769,251]:
        curves=[]
        for sel in selections:
            sel&=counts>0;curve=[]
            for level in range(256):
                d=(y[sel]-level)**2;w=counts[sel]*np.exp(-(d-d.min())/32);curve.append((w@colors[pal][sel]/w.sum()).tolist())
            curves.append(curve)
        out[pal]=curves
    return out
def recolor(image,mask,palette,config,vectors):
    if palette==250:return image.copy()
    a=np.array(image);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255;level=np.clip(np.round(c@LUMA*255),0,255).astype(int)
    out=c*(1-w.sum(2,keepdims=True))
    for i in range(4):out+=w[:,:,i,None]*np.array(vectors[palette][i])[level]
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8);return Image.fromarray(a)
