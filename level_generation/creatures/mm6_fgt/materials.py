"""Leather fighter enhanced material masks and native-used palette interpolation."""
import numpy as np
from PIL import Image
from scipy import ndimage
REGIONS={'mask_r':'Green cloth','mask_g':'Brown leather','mask_b':'Unused','mask_a':'Unused'}
LUMA=np.array([.2126,.7152,.0722])
def coverage(image):
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    hsv=np.array(image.convert('RGB').convert('HSV')).astype(float);h=hsv[:,:,0]*360/255;s=hsv[:,:,1]/255
    cloth=np.clip((g-r-.002)/.012,0,1)*np.clip((g-b-.002)/.02,0,1)
    leather=np.clip((r-g-.035)/.08,0,1)*np.clip((g-b-.025)/.06,0,1)*np.clip((.56-r)/.12,0,1)*(1-cloth)
    # Keep the pale face/highlights, dark scarf, steel and gold trim outside leather coverage.
    leather*=np.clip((h-8)/8,0,1)*np.clip((36-h)/10,0,1)
    w=np.stack([cloth,leather,np.zeros_like(r),np.zeros_like(r)],2)
    core=ndimage.distance_transform_edt(a[:,:,3]>=250)>3
    if core.any():
        d,ix=ndimage.distance_transform_edt(~core,return_indices=True);edge=(a[:,:,3]>0)&~core&(d<=5);w[edge]=w[ix[0],ix[1]][edge]
    w/=np.maximum(1,w.sum(2,keepdims=True));out=np.floor(w*255).astype(np.uint8);out[a[:,:,3]==0]=0
    return Image.fromarray(out,'RGBA')
def fit(config,inv,repo):
    colors={int(p):np.fromfile(repo/f'assets_dev/worlds/mm6/textures/pal{p}.act',np.uint8)[:768].reshape(256,3)/255 for p in inv['variants']}
    counts=np.zeros(256)
    for src in inv['sources'].values():counts+=np.bincount(np.array(Image.open(repo/src['path'])).ravel(),minlength=256)
    counts[0]=0;base=colors[733];r,g,b=base.T
    selections=[(g>r+.02)&(g>b+.01),(r>g+.05)&(g>b+.025)&(r<.6),counts>0,counts>0]
    y=base@LUMA*255;out={}
    for pal in [734,735]:
        curves=[]
        for sel in selections:
            sel&=counts>0;curve=[]
            for level in range(256):
                d=(y[sel]-level)**2;w=counts[sel]*np.exp(-(d-d.min())/32);curve.append((w@colors[pal][sel]/w.sum()).tolist())
            curves.append(curve)
        out[pal]=curves
    return out
def recolor(image,mask,palette,config,vectors):
    if palette==733:return image.copy()
    a=np.array(image);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255;level=np.clip(np.round(c@LUMA*255),0,255).astype(int)
    out=c*(1-w.sum(2,keepdims=True))
    for i in range(4):out+=w[:,:,i,None]*np.array(vectors[palette][i])[level]
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8);return Image.fromarray(a)
