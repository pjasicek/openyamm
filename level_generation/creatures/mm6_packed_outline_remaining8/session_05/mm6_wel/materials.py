"""Enhanced-art water-elemental material coverage and native ROI palette fits."""
import numpy as np
from PIL import Image
from scipy import ndimage
REGIONS={'mask_r':'Gray-green skin','mask_g':'Green/gold scaled tail','mask_b':'Sandy hair and beard','mask_a':'Reddish trident, crown and bands; not sprite alpha'}
LUMA=np.array([.2126,.7152,.0722])
# These native aligned rectangles sample material colors only; they are never resized as artwork masks.
NATIVE_SAMPLE_RECTS=[[(294,186,344,237)],[(296,274,342,325)],[(309,154,334,180)],[(274,287,286,303),(309,128,331,143),(278,233,286,251)]]

def coverage(image):
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    hsv=np.array(image.convert('RGB').convert('HSV')).astype(float);h=hsv[:,:,0]*360/255;s=hsv[:,:,1]/255
    solid=a[:,:,3]>128; yy=np.indices(r.shape)[0]
    skin_seed=solid&(h>65)&(h<130)&(s<.30)&(g>.15)
    split=float(np.median(yy[skin_seed])) if skin_seed.any() else image.height*.55
    lower=np.clip((yy-split-12)/16,0,1)
    metal=np.clip(((r-g)/np.maximum(r,.03)-.08)/.14,0,1)*np.clip((35-h)/12,0,1)*np.clip((s-.30)/.15,0,1)
    warm=np.clip((h-27)/12,0,1)*np.clip((80-h)/15,0,1)*np.clip((s-.23)/.15,0,1)*(1-metal)
    green=np.clip((h-65)/20,0,1)*np.clip((165-h)/20,0,1)*np.clip((s-.28)/.16,0,1)
    tail=np.maximum(green,warm*lower)
    hair=warm*(1-lower)*(1-tail)
    skin=np.clip((h-38)/12,0,1)*np.clip((160-h)/15,0,1)*np.clip((.50-s)/.12,0,1)*(1-tail)*(1-hair)*(1-metal)
    w=np.stack([skin,tail,hair,metal],axis=2)
    core=ndimage.distance_transform_edt(a[:,:,3]>=250)>3
    if core.any():
        d,ix=ndimage.distance_transform_edt(~core,return_indices=True);edge=(a[:,:,3]>0)&~core&(d<=5);w[edge]=w[ix[0],ix[1]][edge]
    w/=np.maximum(1,w.sum(axis=2,keepdims=True));out=np.floor(w*255).astype(np.uint8);out[a[:,:,3]==0]=0
    return Image.fromarray(out,'RGBA')

def fit(config,inv,repo):
    colors={int(p):np.fromfile(repo/f'assets_dev/worlds/mm6/textures/pal{p}.act',np.uint8)[:768].reshape(256,3)/255 for p in inv['variants']}
    src=inv['sources']['welsta0'];index=np.array(Image.open(repo/src['path']));ox=(inv['logical_canvas'][0]-index.shape[1])//2;oy=inv['logical_canvas'][1]-index.shape[0]
    aligned=np.zeros((inv['logical_canvas'][1],inv['logical_canvas'][0]),np.uint8);aligned[oy:oy+index.shape[0],ox:ox+index.shape[1]]=index
    counts=[]
    for rects in NATIVE_SAMPLE_RECTS:
        count=np.zeros(256)
        for x0,y0,x1,y1 in rects:count+=np.bincount(aligned[y0:y1,x0:x1].ravel(),minlength=256)
        count[0]=0;counts.append(count)
    # Remove other materials' dither indices from the native color samples.
    base=colors[730]; blue=colors[731]
    filters=[(abs(base[:,0]-base[:,1])<.07)&(base[:,1]>base[:,2]),
             (blue[:,0]>blue[:,1]*1.15)&(blue[:,2]>blue[:,1]*1.1),
             (blue[:,2]>blue[:,0]*1.25)&(blue[:,2]>blue[:,1]*1.1),
             (base[:,0]>base[:,1]*1.2)&(abs(base[:,1]-base[:,2])<.025)&(blue[:,1]>blue[:,0]*1.2)]
    global_count=np.bincount(index.ravel(),minlength=256).astype(float);global_count[0]=0
    for i,select in enumerate(filters):
        counts[i]*=select
        if np.count_nonzero(counts[i])<4:counts[i]=global_count*select
    y=colors[730]@LUMA*255;out={} 
    for pal in [731,732]:
        curves=[]
        for count in counts:
            selected=count>0;assert selected.sum()>3;curve=[]
            for level in range(256):
                d=(y[selected]-level)**2;w=count[selected]*np.exp(-(d-d.min())/32)
                curve.append((w@colors[pal][selected]/w.sum()).tolist())
            curves.append(curve)
        out[pal]=curves
    return out

def recolor(image,mask,palette,config,vectors):
    if palette==730:return image.copy()
    a=np.array(image);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255
    level=np.clip(np.round(c@LUMA*255),0,255).astype(int);out=c*(1-w.sum(axis=2,keepdims=True))
    for i in range(4):out+=w[:,:,i,None]*np.array(vectors[palette][i])[level]
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8)
    return Image.fromarray(a)
