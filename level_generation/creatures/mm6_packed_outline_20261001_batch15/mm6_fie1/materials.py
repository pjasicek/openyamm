"""One-channel enhanced fire-core coverage and native nonlinear palette lighting."""
import numpy as np
from PIL import Image
LUMA=np.array([.2126,.7152,.0722])
# Representative native/restored core medians: 54.4 versus 46.4 sRGB luma levels.
# Fixed across the family; baked into LUTs, never normalized per animation frame.
CORE_LUMINANCE_GAIN=1.17

def coverage(image):
    from scipy import ndimage
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    w=np.clip((r-g-.15)/.15,0,1)*np.clip((.50-g)/.15,0,1)
    # Orange flame edges also have r>g. Their near-saturated red channel
    # distinguishes them from the darker enhanced inner core after 0.96 tone.
    w*=np.clip((.95-r)/.045,0,1)
    core=ndimage.distance_transform_edt(a[:,:,3]>=250)>3
    if core.any():
        d,ix=ndimage.distance_transform_edt(~core,return_indices=True);edge=(a[:,:,3]>0)&~core&(d<=5);w[edge]=w[ix[0],ix[1]][edge]
    w[a[:,:,3]==0]=0
    return Image.fromarray(np.round(w*255).astype(np.uint8),'L')

def fit(config,inv,repo):
    colors={int(p):np.fromfile(repo/f'assets_dev/worlds/mm6/textures/pal{p}.act',np.uint8)[:768].reshape(256,3)/255 for p in inv['variants']}
    counts=np.zeros(256)
    for n,s in inv['sources'].items():
        if s['referenced']:counts+=np.bincount(np.array(Image.open(repo/s['path'])).ravel(),minlength=256)
    base=colors[204];r,g,b=base.T
    changed=np.maximum(np.abs(colors[728]-base).max(axis=1),np.abs(colors[729]-base).max(axis=1))>.15
    selected=(counts>0)&(np.arange(256)>0)&(r>g+.2)&(g<.45)&changed
    y=(base@LUMA)*255;out={}
    for p in [728,729]:
        curve=[]
        for level in range(256):
            sample=level*CORE_LUMINANCE_GAIN
            d=(y[selected]-sample)**2;w=counts[selected]*np.exp(-(d-d.min())/32)
            target=w@colors[p][selected]/w.sum()
            # Preserve detail below the darkest native palette sample instead
            # of flattening all darker generated pixels to one constant color.
            if sample<y[selected].min():target*=sample/(w@y[selected]/w.sum())
            curve.append(target.tolist())
        out[p]=curve
    return out

def recolor(image,mask,palette,config,vectors):
    if palette==204:return image.copy()
    a=np.array(image);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255
    level=np.clip(np.round((c@LUMA)*255),0,255).astype(int)
    out=c*(1-w[:,:,None])+np.array(vectors[palette])[level]*w[:,:,None]
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8)
    return Image.fromarray(a)
