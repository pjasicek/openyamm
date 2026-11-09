"""Enhanced flying dragon material masks, fixed native palette lookup curves."""
import numpy as np
from PIL import Image
from scipy import ndimage
REGIONS={'mask_r':'Forest-green hide and wing struts','mask_g':'Olive wing membranes','mask_b':'Gold belly, fins and flame','mask_a':'Neutral horns and claws; not sprite alpha'}
LUMA=np.array([.2126,.7152,.0722])

def coverage(image):
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    hsv=np.array(image.convert('RGB').convert('HSV')).astype(float);h=hsv[:,:,0]*360/255;s=hsv[:,:,1]/255
    wing=np.clip((h-42)/8,0,1)*np.clip((96-h)/12,0,1)*np.clip((s-.08)/.10,0,1)
    body=np.clip((h-78)/12,0,1)*np.clip((g-r-.004)/.02,0,1)
    bone=np.clip((np.minimum(r,g)-.28)/.15,0,1)*np.clip((.20-s)/.10,0,1)
    gold=np.clip((48-h)/8,0,1)*np.clip((r-g-.015)/.025,0,1)*(1-bone)
    w=np.stack([body,wing,gold,bone],axis=2)
    core=ndimage.distance_transform_edt(a[:,:,3]>=250)>3
    if core.any():
        d,ix=ndimage.distance_transform_edt(~core,return_indices=True);edge=(a[:,:,3]>0)&~core&(d<=5);w[edge]=w[ix[0],ix[1]][edge]
    w/=np.maximum(1,w.sum(axis=2,keepdims=True));o=np.floor(w*255).astype(np.uint8);o[a[:,:,3]==0]=0
    return Image.fromarray(o,'RGBA')

def fit(config,inv,repo):
    colors={int(p):np.fromfile(repo/f'assets_dev/worlds/mm6/textures/pal{p}.act',np.uint8)[:768].reshape(256,3)/255 for p in inv['variants']}
    counts=np.zeros(256)
    for n,s in inv['sources'].items():counts+=np.bincount(np.array(Image.open(repo/s['path'])).ravel(),minlength=256)
    base=colors[692];ix=np.arange(256)
    body=ix>=184
    wing=(ix>=55)&(ix<177)
    r,g,b=base.T
    eye=((ix<55)|(ix>=177)&(ix<184))&(r>g+.015)&(g>b+.02)
    mouth=(ix<55)&(np.max(base,axis=1)-np.min(base,axis=1)<.08)&(np.min(base,axis=1)>.04)
    y=(base@LUMA)*255;out={}
    for p in [693,694]:
        curves=[]
        for region in [body,wing,eye,mouth]:
            selected=region&(counts>0);assert selected.sum()>3;curve=[]
            for level in range(256):
                d=(y[selected]-level)**2;w=counts[selected]*np.exp(-(d-d.min())/32)
                curve.append((w@colors[p][selected]/w.sum()).tolist())
            curves.append(curve)
        out[p]=curves
    return out

def recolor(image,mask,palette,config,vectors):
    if palette==692:return image.copy()
    a=np.array(image);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255
    level=np.clip(np.round((c@LUMA)*255),0,255).astype(int);out=c*(1-w.sum(axis=2,keepdims=True))
    for i in range(4):out+=w[:,:,i,None]*np.array(vectors[palette][i])[level]
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8)
    return Image.fromarray(a)
