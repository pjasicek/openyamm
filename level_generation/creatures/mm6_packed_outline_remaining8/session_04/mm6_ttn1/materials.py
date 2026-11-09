"""Medusa enhanced material masks and native-used palette interpolation."""
import numpy as np
from PIL import Image
from scipy import ndimage
REGIONS={'mask_r':'Violet armor','mask_g':'Gold trim','mask_b':'Red plume','mask_a':'Unused'}
LUMA=np.array([.2126,.7152,.0722])
def coverage(image):
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    armor=np.clip((b-np.maximum(r,g)-.002)/.016,0,1)*np.clip((r/np.maximum(g,.01)-.65)/.15,0,1)
    gold=np.clip(((g-b)/np.maximum(g,.01)-.22)/.18,0,1)*np.clip((r/np.maximum(g,.01)-1.06)/.10,0,1)
    # Saturated red crest bristles must not enter the gold-trim channel.
    red_separation=np.clip((r/np.maximum(g,.01)-2.0)/.6,0,1)
    gold*=1-red_separation
    plume=np.clip((r-np.maximum(g,b)-.04)/.10,0,1)*(1-gold)
    w=np.stack([armor,gold,plume,np.zeros_like(r)],2)
    core=ndimage.distance_transform_edt(a[:,:,3]>=250)>3
    if core.any():
        d,ix=ndimage.distance_transform_edt(~core,return_indices=True);edge=(a[:,:,3]>0)&~core&(d<=5);w[edge]=w[ix[0],ix[1]][edge]
    w/=np.maximum(1,w.sum(2,keepdims=True));out=np.floor(w*255).astype(np.uint8);out[a[:,:,3]==0]=0
    return Image.fromarray(out,'RGBA')
def fit(config,inv,repo):
    colors={int(p):np.fromfile(repo/f'assets_dev/worlds/mm6/textures/pal{p}.act',np.uint8)[:768].reshape(256,3)/255 for p in inv['variants']}
    counts=np.zeros(256)
    for src in inv['sources'].values():counts+=np.bincount(np.array(Image.open(repo/src['path'])).ravel(),minlength=256)
    counts[0]=0;base=colors[828];r,g,b=base.T
    idx=np.arange(256)
    selections=[(idx>=117)&(idx<=243),(idx>=67)&(idx<=116)&(r>b+.04)&(g>b+.04),(idx<38)&(r>g*1.2),counts>0]
    y=base@LUMA*255;out={}
    for pal in [829, 830]:
        curves=[]
        for sel in selections:
            sel&=counts>0;curve=[]
            for level in range(256):
                d=(y[sel]-level)**2;w=counts[sel]*np.exp(-(d-d.min())/32);curve.append((w@colors[pal][sel]/w.sum()).tolist())
            curves.append(curve)
        out[pal]=curves
    return out
def recolor(image,mask,palette,config,vectors):
    if palette==828:return image.copy()
    a=np.array(image);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255;level=np.clip(np.round(c@LUMA*255),0,255).astype(int)
    out=c*(1-w.sum(2,keepdims=True))
    # Native 829 retains the 828 gold and red ramps byte for byte.
    for i in range(4):
        target=c if palette==829 and i in (1,2) else np.array(vectors[palette][i])[level]
        out+=w[:,:,i,None]*target
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8);return Image.fromarray(a)
