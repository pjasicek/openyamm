"""Enhanced skull, neutral horns/face and iris coverage with native ramps."""
import numpy as np
from scipy import ndimage
from PIL import Image
REGIONS={'mask_r':'Blue skull skin','mask_g':'Neutral gray face, horns and teeth','mask_b':'Central colored iris and native eye flare','mask_a':'Unused; not sprite alpha'}
LUMA=np.array([.2126,.7152,.0722])

def coverage(image):
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    purple=np.clip((np.minimum(r,b)-g-.015)/.04,0,1)
    seeds=(purple>.5)&(a[:,:,3]>128)
    labels,_=ndimage.label(seeds);sizes=np.bincount(labels.ravel());keep=sizes>=8;keep[0]=False;seeds=keep[labels]
    near=ndimage.binary_dilation(seeds,iterations=6)
    chroma=np.clip((b-g-.015)/.04,0,1)
    iris=np.maximum(purple,near*chroma)
    skin=np.clip((b-r-.012)/.04,0,1)*np.clip((b-g-.008)/.03,0,1)*(1-iris)
    neutral=(1-skin-iris)*np.clip((c.max(axis=2)-.025)/.055,0,1)
    # Bright white eye catchlight and pupil remain protected.
    neutral*=1-(near*np.clip((c.min(axis=2)-.6)/.15,0,1))
    w=np.stack([skin,neutral,iris,iris*0],axis=2);w/=np.maximum(1,w.sum(axis=2,keepdims=True))
    core=ndimage.distance_transform_edt(a[:,:,3]>=250)>3
    if core.any():
        dist,ix=ndimage.distance_transform_edt(~core,return_indices=True);edge=(a[:,:,3]>0)&~core&(dist<=5);w[edge]=w[ix[0],ix[1]][edge]
    out=np.floor(np.clip(w,0,1)*255).astype(np.uint8);out[a[:,:,3]==0]=0
    return Image.fromarray(out,'RGBA')

def fit(config,inv,repo):
    colors={int(p):np.fromfile(repo/f'assets_dev/worlds/mm6/textures/pal{p}.act',np.uint8)[:768].reshape(256,3)/255 for p in inv['variants']}
    counts=np.zeros(256)
    for n,s in inv['sources'].items():counts+=np.bincount(np.array(Image.open(repo/s['path'])).ravel(),minlength=256)
    base=colors[670];r,g,b=base.T;ids=np.arange(256)
    skin=(ids<145)&(b>r+.02)&(b>g+.02)
    neutral=(ids>0)&(ids<145)&~skin
    iris=(ids>=145)&(b>g+.025)
    y=(base@LUMA)*255;out={}
    for p in [669,671]:
        curves=[]
        for region in [skin,neutral,iris]:
            selected=region&(counts>0);curve=[]
            for level in range(256):
                d=(y[selected]-level)**2;w=counts[selected]*np.exp(-(d-d.min())/32)
                curve.append((w@colors[p][selected]/w.sum()).tolist())
            curves.append(curve)
        out[p]=curves+[np.zeros((256,3)).tolist()]
    return out

def recolor(image,mask,palette,config,vectors):
    if palette==670:return image.copy()
    a=np.array(image);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255
    level=np.clip(np.round((c@LUMA)*255),0,255).astype(int);out=c*(1-w.sum(axis=2,keepdims=True))
    for i in range(4):out+=w[:,:,i,None]*np.array(vectors[palette][i])[level]
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8)
    return Image.fromarray(a)
