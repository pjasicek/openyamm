"""Enhanced demon material coverage and deterministic native palette curves."""
import numpy as np
from PIL import Image
from scipy import ndimage
REGIONS={'mask_r':'Gray scaly body; belly protected by reviewed anatomical ROI','mask_g':'Green harness','mask_b':'Ivory spikes, claws and clasp','mask_a':'Salmon effect and eyes; not sprite alpha'}
LUMA=np.array([.2126,.7152,.0722])

def coverage(image):
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    harness=np.clip((g-np.maximum(r,b)-.02)/.045,0,1)
    effect=np.clip((r-g-.035)/.06,0,1)*np.clip((r-b-.025)/.055,0,1)*np.clip((.055-np.abs(g-b))/.03,0,1)
    bone=np.clip((np.minimum(r,g)-b-.012)/.035,0,1)*np.clip((np.minimum(r,g)-.24)/.10,0,1)*(1-effect)
    w=np.stack([(1-harness)*(1-effect)*(1-bone),harness,bone,effect],axis=2)
    core=ndimage.distance_transform_edt(a[:,:,3]>=250)>3
    if core.any():
        d,ix=ndimage.distance_transform_edt(~core,return_indices=True);edge=(a[:,:,3]>0)&~core&(d<=5);w[edge]=w[ix[0],ix[1]][edge]
    w/=np.maximum(1,w.sum(axis=2,keepdims=True));o=np.floor(w*255).astype(np.uint8);o[a[:,:,3]==0]=0
    return Image.fromarray(o,'RGBA')

def fit(config,inv,repo):
    colors={int(p):np.fromfile(repo/f'assets_dev/worlds/mm6/textures/pal{p}.act',np.uint8)[:768].reshape(256,3)/255 for p in inv['variants']}
    counts=np.zeros(256)
    for n,s in inv['sources'].items():
        if s.get('fixed_palette') is not None:continue
        counts+=np.bincount(np.array(Image.open(repo/s['path'])).ravel(),minlength=256)
    base=colors[688];r,g,b=base.T;ix=np.arange(256)
    body=ix>=183;harness=(ix>=160)&(ix<183);effect=(r>g+.045)&(ix<160);bone=(ix<145)&~effect
    y=(base@LUMA)*255;out={}
    for p in [687,686]:
        curves=[]
        for region in [body,harness,bone,effect]:
            selected=region&(counts>0)&(ix>0);assert selected.sum()>3;curve=[]
            for level in range(256):
                d=(y[selected]-level)**2;w=counts[selected]*np.exp(-(d-d.min())/32)
                curve.append((w@colors[p][selected]/w.sum()).tolist())
            curves.append(curve)
        out[p]=curves
    return out

def recolor(image,mask,palette,config,vectors):
    if palette==688:return image.copy()
    a=np.array(image);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255
    level=np.clip(np.round((c@LUMA)*255),0,255).astype(int);out=c*(1-w.sum(axis=2,keepdims=True))
    for i in range(4):out+=w[:,:,i,None]*np.array(vectors[palette][i])[level]
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8)
    return Image.fromarray(a)
