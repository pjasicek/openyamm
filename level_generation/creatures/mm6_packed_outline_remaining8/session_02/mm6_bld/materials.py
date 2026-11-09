"""Enhanced teal body and ochre wing masks, fixed native palette lookup curves."""
import numpy as np
from PIL import Image
from scipy import ndimage
REGIONS={'mask_r':'Teal body','mask_g':'Tan wing membrane','mask_b':'Cyan eyes','mask_a':'Pink maw and underside; not sprite alpha'}
LUMA=np.array([.2126,.7152,.0722])

def coverage(image):
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    body=np.clip((g-r-.008)/.035,0,1)*np.clip((b-r+.005)/.03,0,1)
    hsv=np.array(image.convert('RGB').convert('HSV')).astype(float);h=hsv[:,:,0]*360/255;s=hsv[:,:,1]/255
    wing=np.clip((h-19)/4,0,1)*np.clip((64-h)/12,0,1)*np.clip((s-.16)/.12,0,1)*(1-body)
    eye=np.clip((np.minimum(g,b)-r-.07)/.12,0,1)*np.clip((np.minimum(g,b)-.20)/.16,0,1)
    body*=1-eye
    mouth=np.clip((24-h)/6,0,1)*np.clip((s-.23)/.18,0,1)*np.clip((r-g-.025)/.05,0,1)*(1-body)*(1-wing)*(1-eye)
    w=np.stack([body,wing,eye,mouth],axis=2)
    core=ndimage.distance_transform_edt(a[:,:,3]>=250)>3
    if core.any():
        d,ix=ndimage.distance_transform_edt(~core,return_indices=True);edge=(a[:,:,3]>0)&~core&(d<=5);w[edge]=w[ix[0],ix[1]][edge]
    w/=np.maximum(1,w.sum(axis=2,keepdims=True));o=np.floor(w*255).astype(np.uint8);o[a[:,:,3]==0]=0
    return Image.fromarray(o,'RGBA')

def fit(config,inv,repo):
    colors={int(p):np.fromfile(repo/f'assets_dev/worlds/mm6/textures/pal{p}.act',np.uint8)[:768].reshape(256,3)/255 for p in inv['variants']}
    counts=np.zeros(256)
    for n,s in inv['sources'].items():counts+=np.bincount(np.array(Image.open(repo/s['path'])).ravel(),minlength=256)
    base=colors[672];r,g,b=base.T
    body=(g>r+.015)&(b>r-.01)
    hsv=np.array(Image.fromarray(np.round(base*255).astype(np.uint8).reshape(1,256,3)).convert('HSV'))[0].astype(float);h=hsv[:,0]*360/255;s=hsv[:,1]/255
    target=colors[162];wing=(target[:,2]>target[:,0]*1.12)&(target[:,2]>target[:,1]*1.25)&(h>20)&~body
    eye=(np.minimum(g,b)>r+.10)&(np.minimum(g,b)>.30)
    body &= ~eye
    mouth=(h<24)&(s>.23)&(r>g+.035)&~body&~wing
    y=(base@LUMA)*255;out={}
    for p in [162,673]:
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
    if palette==672:return image.copy()
    a=np.array(image);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255
    level=np.clip(np.round((c@LUMA)*255),0,255).astype(int);out=c*(1-w.sum(axis=2,keepdims=True))
    for i in range(4):out+=w[:,:,i,None]*np.array(vectors[palette][i])[level]
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8)
    return Image.fromarray(a)
