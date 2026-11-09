"""Enhanced cave dragon material masks, fixed native palette lookup curves."""
import numpy as np
from PIL import Image
from scipy import ndimage
REGIONS={'mask_r':'Teal scaly hide','mask_g':'Orange underside, fins and warm mottling','mask_b':'Pale horns, spines and claws','mask_a':'Mauve mouth; not sprite alpha'}
LUMA=np.array([.2126,.7152,.0722])

def coverage(image):
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    # Green-blue hide, warm underside/mottling, pale horns, and small mouth/eye accents.
    warm=np.clip((r-g-.006)/.035,0,1)*np.clip((g-b-.004)/.035,0,1)
    bone=np.clip((np.minimum(r,g)-.30)/.18,0,1)*np.clip((.23-(np.maximum(r,g)-b))/.12,0,1)
    mouth=np.clip((np.minimum(r,b)-g-.015)/.045,0,1)
    warm*=1-bone
    body=(1-warm)*(1-bone)*(1-mouth)
    w=np.stack([body,warm,bone,mouth],axis=2)
    core=ndimage.distance_transform_edt(a[:,:,3]>=250)>3
    if core.any():
        d,ix=ndimage.distance_transform_edt(~core,return_indices=True);edge=(a[:,:,3]>0)&~core&(d<=5);w[edge]=w[ix[0],ix[1]][edge]
    w/=np.maximum(1,w.sum(axis=2,keepdims=True));o=np.floor(w*255).astype(np.uint8);o[a[:,:,3]==0]=0
    return Image.fromarray(o,'RGBA')

def fit(config,inv,repo):
    colors={int(p):np.fromfile(repo/f'assets_dev/worlds/mm6/textures/pal{p}.act',np.uint8)[:768].reshape(256,3)/255 for p in inv['variants']}
    counts=np.zeros(256)
    for n,s in inv['sources'].items():counts+=np.bincount(np.array(Image.open(repo/s['path'])).ravel(),minlength=256)
    base=colors[689];ix=np.arange(256)
    body=(ix>=16)&(ix<67)
    wing=ix>=139
    eye=(ix>=67)&(ix<117)
    mouth=(ix>=1)&(ix<7)
    y=(base@LUMA)*255;out={}
    for p in [690,691]:
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
    if palette==689:return image.copy()
    a=np.array(image);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255
    level=np.clip(np.round((c@LUMA)*255),0,255).astype(int);out=c*(1-w.sum(axis=2,keepdims=True))
    for i in range(4):out+=w[:,:,i,None]*np.array(vectors[palette][i])[level]
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8)
    return Image.fromarray(a)
