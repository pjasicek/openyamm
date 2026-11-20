"""Sea serpent scale, crest, belly and foam coverage on enhanced artwork."""
import numpy as np
from PIL import Image
from scipy import ndimage
LUMA=np.array([.2126,.7152,.0722])
REGIONS={'mask_r':'Olive scales','mask_g':'Brown crest','mask_b':'Gray green belly','mask_a':'Turquoise foam'}
def coverage(image):
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    foam=np.clip((np.minimum(g,b)-r-.01)/.04,0,1)
    scales=np.clip(((g-b)/np.maximum(g,.01)-.40)/.16,0,1)*np.clip((g/np.maximum(r,.01)-.62)/.15,0,1)*np.clip((r/np.maximum(g,.01)-.98)/.06,0,1)*(1-foam)
    crest=np.clip(((r-g)/np.maximum(r-b,.01)-.30)/.18,0,1)*np.clip((g/np.maximum(r,.01)-.35)/.18,0,1)*(1-scales-foam)
    # Exclude the red mouth from the crest mask; broad neutral/green belly is separate.
    belly=np.clip((g/np.maximum(r,.01)-.80)/.12,0,1)*(1-scales-crest-foam)
    w=np.stack([scales,crest,belly,foam],2)
    core=ndimage.distance_transform_edt(a[:,:,3]>=250)>3
    if core.any():
        d,ix=ndimage.distance_transform_edt(~core,return_indices=True);edge=(a[:,:,3]>0)&~core&(d<=5);w[edge]=w[ix[0],ix[1]][edge]
    w=np.clip(w,0,1);w/=np.maximum(1,w.sum(2,keepdims=True));out=np.floor(w*255).astype(np.uint8);out[a[:,:,3]==0]=0
    return Image.fromarray(out,'RGBA')
def fit(config,inv,repo):
    colors={int(p):np.fromfile(repo/f'assets_dev/worlds/mm6/textures/pal{p}.act',np.uint8)[:768].reshape(256,3)/255 for p in inv['variants']}
    counts=np.zeros(256)
    for src in inv['sources'].values():counts+=np.bincount(np.array(Image.open(repo/src['path'])).ravel(),minlength=256)
    counts[0]=0;base=colors[813];r,g,b=base.T;i=np.arange(256);blue=colors[814]
    selections=[(r>g*1.03)&(g>b*1.4),(r>g)&(blue[:,1]>blue[:,0]*1.1)&(blue[:,1]>blue[:,2]),(i<217)&((g>=r)|((base.max(1)-base.min(1))<.06)),i>=217]
    y=base@LUMA*255;out={}
    for pal in [814,815]:
        curves=[]
        for sel in selections:
            sel&=counts>0;curve=[]
            for level in range(256):
                d=(y[sel]-level)**2;w=counts[sel]*np.exp(-(d-d.min())/32);curve.append((w@colors[pal][sel]/w.sum()).tolist())
            curves.append(curve)
        out[pal]=curves
    return out
def recolor(image,mask,palette,config,vectors):
    if palette==813:return image.copy()
    a=np.array(image);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255;level=np.clip(np.round(c@LUMA*255),0,255).astype(int)
    out=c*(1-w.sum(2,keepdims=True))
    for i in range(4):out+=w[:,:,i,None]*np.array(vectors[palette][i])[level]
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8);return Image.fromarray(a)
