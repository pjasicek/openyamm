"""Enhanced cobra scale materials, with fixed usage-weighted native palette ramps."""
import numpy as np
from scipy import ndimage
from PIL import Image
REGIONS={'mask_r':'Blue-grey body, belly plates and tail spots','mask_g':'Pale front hood-side scales','mask_b':'Pale back-of-hood rings','mask_a':'Unused; not sprite alpha'}

def coverage(im, allow_back_rings=True):
    a=np.array(im);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    alpha=a[:,:,3]>0;ys,xs=np.where(a[:,:,3]>96)
    yrel=(np.indices(alpha.shape)[0]-ys.min())/max(1,ys.max()-ys.min())
    cream=np.clip((np.minimum(r,g)-b-.015)/.055,0,1)
    sat=(c.max(axis=2)-c.min(axis=2))/np.maximum(c.max(axis=2),.001)
    white=np.clip((.28-sat)/.12,0,1)*np.clip((c.mean(axis=2)-.23)/.15,0,1)
    white*=yrel<.80
    if not allow_back_rings:white[:]=0
    cream*=1-white
    # Tiny warm eyes and pale fangs retain their identity; body/markings are broad regions.
    protection=(r>g*1.12)&(g>b*1.15)&(yrel<.25)
    total=np.clip((c.max(axis=2)-.015)/.03,0,1)*alpha*(~protection)
    out=np.zeros((*alpha.shape,4))
    out[:,:,1]=cream*total;out[:,:,2]=white*total
    out[:,:,0]=(1-cream-white)*total
    return Image.fromarray(np.floor(np.clip(out,0,1)*255).astype(np.uint8),'RGBA')

def fit(config,inv,repo):
    cs={int(p):np.fromfile(repo/f'assets_dev/worlds/mm6/textures/pal{p}.act',np.uint8)[:768].reshape(256,3)/255 for p in inv['variants']}
    counts=np.zeros(256)
    for n in inv['sources']:counts+=np.bincount(np.array(Image.open(repo/f'assets_dev/engine/sprites/{n}.bmp')).ravel(),minlength=256)
    y=cs[677]@np.array([.2126,.7152,.0722]);ids=np.arange(256);res={}
    for p in [678,679]:
        vectors=[]
        for sel in [(ids>=104)&(ids<216),(ids>=1)&(ids<80),(ids>=86)&(ids<102)]:
            w=counts*sel;vectors.append((((w*y)[:,None]*cs[p]).sum(axis=0)/(w*y*y).sum()).tolist())
        res[p]=vectors+[[0,0,0]]
    return res

def recolor(im,mask,palette,config,vectors):
    if palette==config['base_palette']:return im.copy()
    a=np.array(im);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255
    y=c@np.array([.2126,.7152,.0722]);target=np.einsum('hwk,kc->hwc',w,np.array(vectors[palette]))*y[:,:,None]
    a[:,:,:3]=np.round(np.clip(c*(1-w.sum(axis=2,keepdims=True))+target,0,1)*255).astype(np.uint8)
    return Image.fromarray(a)
