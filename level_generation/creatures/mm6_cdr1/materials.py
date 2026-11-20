"""Enhanced cover dragon material masks, fixed native palette lookup curves."""
import numpy as np
from PIL import Image
from scipy import ndimage
REGIONS={'mask_r':'Orange hide and wing membranes','mask_g':'Golden belly and disintegration','mask_b':'Pale horns, spines and claws','mask_a':'Mauve mouth; not sprite alpha'}
LUMA=np.array([.2126,.7152,.0722])

def coverage(image):
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    hsv=np.array(image.convert('RGB').convert('HSV')).astype(float);h=hsv[:,:,0]*360/255;s=hsv[:,:,1]/255
    bone=np.clip((.60-s)/.20,0,1)*np.clip((np.minimum(r,g)-.15)/.12,0,1)*np.clip((h-28)/10,0,1)
    mouth=np.clip((np.minimum(r,b)-g-.03)/.05,0,1)
    warm=np.clip((h-27)/10,0,1)*np.clip((85-h)/15,0,1)*(1-bone)*(1-mouth)
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
    base=colors[698];ix=np.arange(256)
    hsv=np.array(Image.fromarray(np.round(base[None,:,:]*255).astype(np.uint8),'RGB').convert('HSV'))[0].astype(float)
    h=hsv[:,0]*360/255;s=hsv[:,1]/255
    body=(h<32)&(s>.25)
    wing=(h>=32)&(h<85)&(s>.25)
    eye=np.isin(ix,[22,76,163,200,202,203,230,231,232,250,252])
    mouth=(ix>=1)&(ix<7)
    y=(base@LUMA)*255;out={}
    for p in [699,700]:
        curves=[]
        for region in [body,wing,eye,mouth]:
            selected=region&(counts>0)&(ix>0);assert selected.sum()>3;curve=[]
            for level in range(256):
                d=(y[selected]-level)**2;w=counts[selected]*np.exp(-(d-d.min())/32)
                curve.append((w@colors[p][selected]/w.sum()).tolist())
            curves.append(curve)
        out[p]=curves
    return out

def recolor(image,mask,palette,config,vectors):
    if palette==698:return image.copy()
    a=np.array(image);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255
    level=np.clip(np.round((c@LUMA)*255),0,255).astype(int);out=c*(1-w.sum(axis=2,keepdims=True))
    for i in range(4):out+=w[:,:,i,None]*np.array(vectors[palette][i])[level]
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8)
    return Image.fromarray(a)
