"""Bound enhanced iris selection using a coarse native eye location, clean non-eye key spill."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy import ndimage
import cv2
from materials import coverage
ROOT=Path(__file__).resolve().parent

def refine():
    sources=json.loads((ROOT/'sources.json').read_text())['sources']
    reg=json.loads((ROOT/'registration.json').read_text())
    pal=np.fromfile(ROOT.parents[2]/'assets_dev/worlds/mm6/textures/pal670.act',np.uint8)[:768].reshape(256,3).astype(float)
    eye_ids=(np.minimum(pal[:,0],pal[:,2])-pal[:,1]>8)
    for n,s in sources.items():
        p=ROOT/'aligned_2x'/f'{n}.png';im=Image.open(p).convert('RGBA');a=np.array(im);c=a[:,:,:3].astype(float)
        native=np.array(Image.open(ROOT.parents[2]/s['path']));yy,xx=np.where(eye_ids[native])
        roi=np.zeros(a.shape[:2],bool)
        if len(xx):
            offset=np.array(s['native_offset'][:2])*2-np.array(reg[n]['canvas_origin_px'])
            x0=max(0,round(xx.min()*2+offset[0]-16));x1=min(im.width,round(xx.max()*2+offset[0]+18))
            y0=max(0,round(yy.min()*2+offset[1]-16));y1=min(im.height,round(yy.max()*2+offset[1]+18))
            roi[y0:y1,x0:x1]=True
        if n.startswith('bhwlk') and n[-1]=='2':
            # Reviewed profile: visible iris is a thin sliver at the right front, not the horn loop.
            ya,xa=np.where(a[:,:,3]>128)
            roi[:]=False
            roi[int(ya.min()+.23*(ya.max()-ya.min())):int(ya.min()+.51*(ya.max()-ya.min())),int(xa.min()+.76*(xa.max()-xa.min())):xa.max()+1]=True
        if n.startswith('bhwlk') and n[-1] in '34':roi[:]=False
        # Outside the eye there is no purple material in this family.
        spill=np.maximum(0,np.minimum(c[:,:,0],c[:,:,2])-c[:,:,1]-3)*(~roi)
        c[:,:,0]-=spill;c[:,:,2]-=spill;a[:,:,:3]=np.round(np.clip(c,0,255)).astype(np.uint8)
        im=Image.fromarray(a);im.save(p)
        weights=np.array(coverage(im)).astype(float)/255
        r,g,b=c.transpose(2,0,1)
        seed=roi&(np.minimum(r,b)>g+10)&(a[:,:,3]>128)
        labels,_=ndimage.label(seed);sizes=np.bincount(labels.ravel());keep=sizes>=max(8,sizes[1:].max()*.08) if len(sizes)>1 else np.array([False]);keep[0]=False;seed=keep[labels]
        eye=np.zeros(a.shape[:2],np.uint8)
        pts=np.column_stack(np.where(seed)[::-1]).astype(np.int32)
        if len(pts)>=3:cv2.fillConvexPoly(eye,cv2.convexHull(pts),1)
        # Include the blue outer iris rim, but not distant blue skull skin.
        eye=ndimage.binary_dilation(eye,iterations=3)&roi
        iris=eye*np.clip((b-g-3)/12,0,1)
        skin=np.clip((b-r-3)/10,0,1)*np.clip((b-g-2)/8,0,1)*(1-iris)
        neutral=(1-skin-iris)*np.clip((c.max(axis=2)-6)/14,0,1)
        # Preserve the entire neutral white catchlight in the enhanced eye hull.
        protected=eye*np.clip((c.min(axis=2)-100)/35,0,1)
        flare=eye*np.clip((np.minimum(g,b)-r-10)/20,0,1)
        # Native flash is a pale catchlight; reduce exaggerated generated cyan.
        if n in ['bhatkc0','bhatkd0','bhdthc0']:
            c=c*(1-.85*flare[:,:,None])+c.max(axis=2,keepdims=True)*.85*flare[:,:,None]
            a[:,:,:3]=np.round(np.clip(c,0,255)).astype(np.uint8);Image.fromarray(a).save(p)
        protected=np.maximum(protected,flare)
        weights=np.stack([skin,neutral,iris,iris*0],axis=2)*(1-protected[:,:,None])
        weights/=np.maximum(1,weights.sum(axis=2,keepdims=True))
        out=np.floor(np.clip(weights,0,1)*255).astype(np.uint8);out[a[:,:,3]==0]=0
        Image.fromarray(out,'RGBA').save(ROOT/'masks_2x'/f'{n}.png')

if __name__=='__main__':refine()
