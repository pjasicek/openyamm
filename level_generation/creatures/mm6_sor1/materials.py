"""Native robe and staff-cap ramps; enhanced-art coverage with reviewed landmark guides."""
import numpy as np
from PIL import Image
REGIONS={'mask_r':'Purple outer robe; blue-grey chest insert protected','mask_g':'Small orange staff foot-cap, blue for A/B','mask_b':'Unused','mask_a':'Unused, not sprite alpha'}

def coverage(im):
    a=np.array(im);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    strength=np.maximum(0,b-np.maximum(r,g))
    w=np.clip((strength-.003)/.018,0,1)*np.clip((b-g-.015)/.04,0,1)
    w[a[:,:,3]==0]=0
    out=np.zeros((*w.shape,4),np.uint8);out[:,:,0]=np.round(w*255)
    return Image.fromarray(out,'RGBA')

def fit(config,inv,repo):
    cs={int(p):np.fromfile(repo/f'assets_dev/worlds/mm6/textures/pal{p}.act',np.uint8)[:768].reshape(256,3)/255 for p in inv['variants']}
    counts=np.zeros(256)
    for n in inv['sources']:counts+=np.bincount(np.array(Image.open(repo/f'assets_dev/engine/sprites/{n}.bmp')).ravel(),minlength=256)
    y=cs[821]@np.array([.2126,.7152,.0722]);ids=np.arange(256)
    result={}
    for p in [819,820]:
        vectors=[]
        for sel in [(ids>=24)&(ids<=97),(ids>=3)&(ids<=9)|(ids==12)]:
            w=counts*sel;vectors.append((((w*y)[:,None]*cs[p]).sum(axis=0)/(w*y*y).sum()).tolist())
        result[p]=vectors+[[0,0,0],[0,0,0]]
    return result

def recolor(im,mask,palette,config,vectors):
    if palette==config['base_palette']:return im.copy()
    a=np.array(im);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255
    y=c@np.array([.2126,.7152,.0722]);target=np.einsum('hwk,kc->hwc',w,np.array(vectors[palette]))*y[:,:,None]
    a[:,:,:3]=np.round(np.clip(c*(1-w.sum(axis=2,keepdims=True))+target,0,1)*255).astype(np.uint8)
    return Image.fromarray(a)
