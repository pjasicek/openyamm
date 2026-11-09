"""Medusa enhanced material masks and native-used palette interpolation."""
import numpy as np
from PIL import Image
from scipy import ndimage
REGIONS={'mask_r':'Rust trousers','mask_g':'Gold necklace','mask_b':'Green pendant','mask_a':'Neutral fur'}
LUMA=np.array([.2126,.7152,.0722])
def coverage(image, name=None, guides=None):
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    pants=np.clip((r-g-.025)/.06,0,1)*np.clip((.72-g/np.maximum(r,.01))/.10,0,1)
    labels,count=ndimage.label((pants>.5)&(a[:,:,3]>128));sizes=np.bincount(labels.ravel());sizes[0]=0
    pants*=ndimage.binary_dilation((sizes>=max(64,sizes.max()*.18))[labels],iterations=2)
    if guides:
        assert guides['pants']['method']=='largest_warm_trouser_component'
        yy,xx=np.indices(pants.shape);alpha=a[:,:,3]>128;ys,xs=np.where(alpha);height=ys.max()-ys.min()
        cloth=(r>g*1.13)&(g>b*1.20)&(r>.065)&alpha&(yy>ys.min()+height*.37)&(yy<ys.min()+height*.70)
        labels,count=ndimage.label(cloth);sizes=np.bincount(labels.ravel());sizes[0]=0
        cloth=ndimage.binary_fill_holes(ndimage.binary_closing(labels==sizes.argmax(),iterations=1))&alpha
        pants[cloth]=1
    jewel=np.clip((np.minimum(g,b)-r-.01)/.03,0,1)
    gold=np.clip((g-b-.025)/.08,0,1)*np.clip((g/np.maximum(r,.01)-.38)/.10,0,1)*np.clip(((r-b)/np.maximum(r,.01)-.35)/.15,0,1)*(1-pants-jewel)
    fur=np.clip((.14-(c.max(2)-c.min(2)))/.06,0,1)*(1-pants-jewel-gold)
    w=np.stack([pants,gold,jewel,fur],2)
    core=ndimage.distance_transform_edt(a[:,:,3]>=250)>3
    if core.any():
        d,ix=ndimage.distance_transform_edt(~core,return_indices=True);edge=(a[:,:,3]>0)&~core&(d<=5);w[edge]=w[ix[0],ix[1]][edge]
    w/=np.maximum(1,w.sum(2,keepdims=True));out=np.floor(w*255).astype(np.uint8);out[a[:,:,3]==0]=0
    return Image.fromarray(out,'RGBA')
def fit(config,inv,repo):
    colors={int(p):np.fromfile(repo/f'assets_dev/worlds/mm6/textures/pal{p}.act',np.uint8)[:768].reshape(256,3)/255 for p in inv['variants']}
    counts=np.zeros(256)
    for src in inv['sources'].values():counts+=np.bincount(np.array(Image.open(repo/src['path'])).ravel(),minlength=256)
    counts[0]=0;base=colors[831];r,g,b=base.T
    idx=np.arange(256)
    selections=[(idx<82),(idx>=117)&(idx<=220)&(r>b+.03)&(g>b+.03),(idx>=98)&(idx<117),(idx>=221)]
    y=base@LUMA*255;out={}
    for pal in [832, 833]:
        curves=[]
        for sel in selections:
            sel&=counts>0;curve=[]
            for level in range(256):
                d=(y[sel]-level)**2;w=counts[sel]*np.exp(-(d-d.min())/32);curve.append((w@colors[pal][sel]/w.sum()).tolist())
            curves.append(curve)
        out[pal]=curves
    return out
def recolor(image,mask,palette,config,vectors):
    if palette==831:return image.copy()
    a=np.array(image);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255;level=np.clip(np.round(c@LUMA*255),0,255).astype(int)
    out=c*(1-w.sum(2,keepdims=True))
    for i in range(4):out+=w[:,:,i,None]*np.array(vectors[palette][i])[level]
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8);return Image.fromarray(a)
