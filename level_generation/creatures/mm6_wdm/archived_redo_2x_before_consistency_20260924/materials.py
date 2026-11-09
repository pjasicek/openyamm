"""Enhanced-art material masks and native-used luminance palette curves."""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
REGIONS={'mask_r':'Purple skin','mask_g':'Dark wing membrane','mask_b':'Ivory horns/spikes/claws','mask_a':'Blue eyes/disintegration; not alpha'}
LUMA=np.array([.2126,.7152,.0722])

def coverage(image, neutral_torso_polygon=None):
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    body=np.clip((np.minimum(r,b)-g-.005)/.035,0,1)
    blue=np.clip((b-r-.03)/.10,0,1)*np.clip((b-g-.005)/.03,0,1)*(1-body)
    ivory=np.clip((np.minimum(r,g)-b-.015)/.04,0,1)*np.clip((np.maximum(r,g)-.21)/.15,0,1)*(1-body)*(1-blue)
    wing=np.clip((r-g+.006)/.015,0,1)*np.clip((r-b+.012)/.025,0,1)*(1-body)*(1-blue)*(1-ivory)
    w=np.stack([body,wing,ivory,blue],axis=2)
    if neutral_torso_polygon:
        stencil = Image.new("L", image.size)
        ImageDraw.Draw(stencil).polygon([tuple(p) for p in neutral_torso_polygon], fill=255)
        neutral = (1-body)*(1-blue)*np.clip((g-b+.02)/.035,0,1)
        w *= (1-neutral*(np.array(stencil)/255))[:,:,None]
    core=ndimage.distance_transform_edt(a[:,:,3]>=250)>3
    if core.any():
        d,ix=ndimage.distance_transform_edt(~core,return_indices=True);edge=(a[:,:,3]>0)&~core&(d<=5);w[edge]=w[ix[0],ix[1]][edge]
    w/=np.maximum(1,w.sum(axis=2,keepdims=True));o=np.floor(w*255).astype(np.uint8);o[a[:,:,3]==0]=0
    return Image.fromarray(o,'RGBA')

def fit(config,inv,repo):
    colors={int(p):np.fromfile(repo/f'assets_dev/worlds/mm6/textures/pal{p}.act',np.uint8)[:768].reshape(256,3)/255 for p in inv['variants']}
    counts=np.zeros(256)
    for n,s in inv['sources'].items():
        if s.get('fixed_palette') is not None:continue
        counts+=np.bincount(np.array(Image.open(repo/s['path'])).ravel(),minlength=256)
    base=colors[684];r,g,b=base.T
    body=np.minimum(r,b)>g+.015
    blue=((b>r+.07)|((np.minimum(r,g)>.7)&(b>r-.025)))&~body
    ivory=(np.minimum(r,g)>.22)&(np.abs(r-g)<.05)&(b<r+.09)&~body&~blue
    wing=(np.arange(256)<178)&~body&~blue&~ivory
    y=(base@LUMA)*255;out={}
    for p in [685,683]:
        curves=[]
        for region in [body,wing,ivory,blue]:
            selected=region&(counts>0)&(np.arange(256)>0);assert selected.sum()>3;curve=[]
            for level in range(256):
                d=(y[selected]-level)**2;w=counts[selected]*np.exp(-(d-d.min())/32)
                curve.append((w@colors[p][selected]/w.sum()).tolist())
            curves.append(curve)
        out[p]=curves
    return out

def recolor(image,mask,palette,config,vectors):
    if palette==684:return image.copy()
    a=np.array(image);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255
    level=np.clip(np.round((c@LUMA)*255),0,255).astype(int);out=c*(1-w.sum(axis=2,keepdims=True))
    for i in range(4):out+=w[:,:,i,None]*np.array(vectors[palette][i])[level]
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8)
    return Image.fromarray(a)
