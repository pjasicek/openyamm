"""Robot cap, reflective shell, belt and warm light coverage on enhanced art."""
import numpy as np
from PIL import Image
from scipy import ndimage
LUMA=np.array([.2126,.7152,.0722])
REGIONS={'mask_r':'Cool etched caps','mask_g':'Reflective shell','mask_b':'Red belt','mask_a':'Warm eye and destruction light'}
def coverage(image):
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    warm=np.clip((r-b-.05)/.12,0,1)*np.clip((g-b-.04)/.12,0,1)
    if ((warm>.5)&(a[:,:,3]>128)).sum()<.10*max(1,(a[:,:,3]>128).sum()):
        warm=np.clip((r-b-.35)/.15,0,1)*np.clip((g-b-.25)/.15,0,1)
    red=np.clip((r-np.maximum(g,b)-.025)/.08,0,1)*(1-warm)
    cap=np.clip((g-r+.003)/.035,0,1)*(1-red-warm)
    shell=np.maximum(0,1-cap-red-warm)
    w=np.stack([cap,shell,red,warm],2)
    core=ndimage.distance_transform_edt(a[:,:,3]>=250)>3
    if core.any():
        d,ix=ndimage.distance_transform_edt(~core,return_indices=True);edge=(a[:,:,3]>0)&~core&(d<=5);w[edge]=w[ix[0],ix[1]][edge]
    w/=np.maximum(1,w.sum(2,keepdims=True));out=np.floor(w*255).astype(np.uint8);out[a[:,:,3]==0]=0
    return Image.fromarray(out,'RGBA')
def fit(config,inv,repo):
    colors={int(p):np.fromfile(repo/f'assets_dev/worlds/mm6/textures/pal{p}.act',np.uint8)[:768].reshape(256,3)/255 for p in inv['variants']}
    counts=np.zeros(256)
    for src in inv['sources'].values():counts+=np.bincount(np.array(Image.open(repo/src['path'])).ravel(),minlength=256)
    counts[0]=0;base=colors[810];r,g,b=base.T;i=np.arange(256)
    selections=[(i>=174)&(i<=214),(i<174)&(r>=g)&((r-b)<.15),(i>=215),(i<174)&(r>b+.1)&(g>b+.08)]
    y=base@LUMA*255;out={}
    for pal in [811,812]:
        curves=[]
        for region,sel in enumerate(selections):
            sel&=counts>0;curve=[]
            for level in range(256):
                d=(y[sel]-level)**2;w=counts[sel]*np.exp(-(d-d.min())/32);curve.append((colors[pal][sel][np.argmax(w)] if region==3 else w@colors[pal][sel]/w.sum()).tolist())
            curves.append(curve)
        out[pal]=curves
    return out
def recolor(image,mask,palette,config,vectors):
    if palette==810:return image.copy()
    import json
    from pathlib import Path
    from scipy.spatial import cKDTree
    a=np.array(image);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255
    level=np.clip(np.round(c@LUMA*255),0,255).astype(int)
    out=c*(1-w.sum(2,keepdims=True))
    for i in range(4):out+=w[:,:,i,None]*np.array(vectors[palette][i])[level]
    lookup=json.loads((Path(__file__).parent/'warm_palette_lookup.json').read_text())
    selected=w[:,:,3]>.01
    if selected.any():
        distance,indices=cKDTree(np.array(lookup['base_rgb'],float)).query(c[selected]*255,k=8)
        blend=1/np.maximum(distance,1)**2
        exact=distance[:,0]<.01
        blend[exact]=0;blend[exact,0]=1
        blend/=blend.sum(1,keepdims=True)
        target=np.array(lookup['targets'][str(palette)],float)/255
        mapped=(target[indices]*blend[:,:,None]).sum(1)
        warm=w[selected,3,None]
        out[selected]+=warm*(mapped-np.array(vectors[palette][3])[level[selected]])
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8)
    return Image.fromarray(a)
