"""One-channel enhanced wing coverage and native nonlinear palette lighting."""
import numpy as np
from PIL import Image
LUMA=np.array([.2126,.7152,.0722])

def coverage(image):
    from process_family import mask
    weights=np.array(mask(image,{'mask_kind':'blue'})).astype(float)
    hue=np.array(image.convert('RGB').convert('HSV'))[:,:,0].astype(float)*360/255
    # The restored violet fur must remain protected when native wing palettes change.
    blue=np.clip((hue-175)/8,0,1)*np.clip((250-hue)/8,0,1)
    return Image.fromarray(np.round(weights*blue).astype(np.uint8),'L')

def fit(config,inv,repo):
    colors={int(p):np.fromfile(repo/f'assets_dev/worlds/mm6/textures/pal{p}.act',np.uint8)[:768].reshape(256,3)/255 for p in inv['variants']}
    counts=np.zeros(256)
    for n,s in inv['sources'].items():
        if s['referenced']:counts+=np.bincount(np.array(Image.open(repo/s['path'])).ravel(),minlength=256)
    base=colors[667];r,g,b=base.T
    selected=(counts>0)&(b>r+.02)&(b>g+.02)
    y=(base@LUMA)*255;out={}
    for p in [666,668]:
        curve=[]
        for level in range(256):
            d=(y[selected]-level)**2;w=counts[selected]*np.exp(-(d-d.min())/32)
            curve.append((w@colors[p][selected]/w.sum()).tolist())
        out[p]=curve
    return out

def recolor(image,mask,palette,config,vectors):
    if palette==667:return image.copy()
    a=np.array(image);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255
    level=np.clip(np.round((c@LUMA)*255),0,255).astype(int)
    out=c*(1-w[:,:,None])+np.array(vectors[palette])[level]*w[:,:,None]
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8)
    return Image.fromarray(a)
