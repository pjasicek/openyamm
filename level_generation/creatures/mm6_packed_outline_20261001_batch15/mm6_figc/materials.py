"""Chain fighter enhanced material masks and native-used palette interpolation."""
import numpy as np
from PIL import Image
from scipy import ndimage
REGIONS={'mask_r':'Ochre surcoat and shield inset','mask_g':'Dark red surcoat and trim','mask_b':'Steel armor, chainmail and weapon','mask_a':'Olive face and warm armor reflections'}
LUMA=np.array([.2126,.7152,.0722])
def coverage(image):
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    hsv=np.array(image.convert('RGB').convert('HSV')).astype(float);h=hsv[:,:,0]*360/255;s=hsv[:,:,1]/255
    ochre=np.clip((h-20)/10,0,1)*np.clip((76-h)/16,0,1)*np.clip((s-.16)/.20,0,1)
    red=np.clip((r-g-.015)/.055,0,1)*np.clip((29-h)/12,0,1)*np.clip((s-.15)/.20,0,1)
    steel=np.clip((.35-s)/.18,0,1)*(1-ochre)*(1-red)
    olive=np.clip((h-42)/10,0,1)*np.clip((95-h)/20,0,1)*np.clip((s-.14)/.12,0,1)
    bounds=image.getbbox()
    if bounds:
        x0,y0,x1,y1=bounds;yy,xx=np.indices(r.shape);height=y1-y0;width=x1-x0
        head=(yy<y0+height*.23)&(xx>x0+width*.22)&(xx<x0+width*.73)
        face=np.clip((h-22)/10,0,1)*np.clip((80-h)/15,0,1)*np.clip((s-.14)/.12,0,1)*head
        olive=np.maximum(olive,face)
    ochre*=1-olive;steel*=1-olive
    w=np.stack([ochre,red,steel,olive],2)
    core=ndimage.distance_transform_edt(a[:,:,3]>=250)>3
    if core.any():
        d,ix=ndimage.distance_transform_edt(~core,return_indices=True);edge=(a[:,:,3]>0)&~core&(d<=5);w[edge]=w[ix[0],ix[1]][edge]
    w/=np.maximum(1,w.sum(2,keepdims=True));out=np.floor(w*255).astype(np.uint8);out[a[:,:,3]==0]=0
    return Image.fromarray(out,'RGBA')
def fit(config,inv,repo):
    colors={int(p):np.fromfile(repo/f'assets_dev/worlds/mm6/textures/pal{p}.act',np.uint8)[:768].reshape(256,3)/255 for p in inv['variants']}
    counts=np.zeros(256)
    for src in inv['sources'].values():counts+=np.bincount(np.array(Image.open(repo/src['path'])).ravel(),minlength=256)
    counts[0]=0;base=colors[212];r,g,b=base.T
    selections=[(r>g*1.15)&(g>b*1.2),(r>g*1.3)&(g<=b*1.2),np.max(base,axis=1)-np.min(base,axis=1)<.07,(abs(r-g)<.04)&(g>b*1.25)]
    y=base@LUMA*255;out={}
    for pal in [211,210]:
        curves=[]
        for sel in selections:
            sel&=counts>0;curve=[]
            for level in range(256):
                d=(y[sel]-level)**2;w=counts[sel]*np.exp(-(d-d.min())/32);curve.append((w@colors[pal][sel]/w.sum()).tolist())
            curves.append(curve)
        out[pal]=curves
    return out
def recolor(image,mask,palette,config,vectors):
    if palette==212:return image.copy()
    a=np.array(image);c=a[:,:,:3].astype(float)/255;w=np.array(mask).astype(float)/255;level=np.clip(np.round(c@LUMA*255),0,255).astype(int)
    out=c*(1-w.sum(2,keepdims=True))
    for i in range(4):out+=w[:,:,i,None]*np.array(vectors[palette][i])[level]
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8);return Image.fromarray(a)
