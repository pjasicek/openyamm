"""Wind cylinder bands and hand discharge from the selected restored MM8 frames.
Uses the accepted MM6 Air shell/scroll technique; no paid generation or new design.
"""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
p=Path(__file__).resolve().parents[1]
source=p.parent/'mm8_packed_outline_collection_20261002/families/mm8_m508/aligned_2x'
sys.path.insert(0,str(p.parent/'mm6_aie1_claude/scripts'))
from make_texture import sample,bleed,streaks,unpremultiply
W,H=1024,512
names=['m508sa0','m508sa4']
arrays=[np.asarray(Image.open(source/(n+'.png')).convert('RGBA'),dtype=float)/255 for n in names]
# Native waist at y=122 pixels; last wind fragments at y=248 (2x source canvas).
y=np.linspace(246,496,H);theta=(np.arange(W)+.5)/W*2*np.pi
acc=np.zeros((H,W,3));weights=np.zeros((H,W));alpha=np.zeros((H,W));profiles=[]
for i,im in enumerate(arrays):
 centers=[];radii=[]
 for row in range(246,497):
  xs=np.flatnonzero(im[row,:,3]>.5)
  runs=np.split(xs,np.where(np.diff(xs)>1)[0]+1)
  runs=[run for run in runs if len(run)>=3]
  xs=min(runs,key=lambda run:abs(np.clip(256,run[0],run[-1])-256)) if runs else np.array([254,258])
  lo,hi=np.quantile(xs,[.03,.97]);centers.append((lo+hi)/2);radii.append(max((hi-lo)/2,2))
 centers=gaussian_filter(centers,5);radii=gaussian_filter(radii,5);profiles.append(radii)
 local=(theta-(i+.5)*2*np.pi/len(arrays)+np.pi)%(2*np.pi)-np.pi
 weight=np.where(abs(local)<np.pi/2,np.cos(local)**2,0)[None,:]
 c=np.interp(y,np.arange(246,497),centers);r=np.interp(y,np.arange(246,497),radii)
 rgba=sample(im,c[:,None]+r[:,None]*np.sin(.8*np.clip(local,-np.pi/2,np.pi/2))[None,:],np.broadcast_to(y[:,None],(H,W)))
 weights+=weight*rgba[...,3];acc+=weight[...,None]*rgba[...,:3]*rgba[...,3,None];alpha+=weight*rgba[...,3]
rgb=acc/np.maximum(weights[...,None],1e-6)
luma=rgb@np.array([.2126,.7152,.0722]);density=.26+.48*np.clip((luma-.45)/.5,0,1)
fade=np.minimum(np.clip(np.arange(H)/12,0,1),np.clip((H-1-np.arange(H))/12,0,1))
body=np.dstack((rgb,np.clip(alpha,0,1)*density*fade[:,None]))
outer=unpremultiply(streaks(body,.37,9,threshold=.65),1.25)
# Thin spiralling filaments, without importing MM6's warm dust palette.
fringe=unpremultiply(streaks(body,.71,17,threshold=.72),1.6)
fringe[...,3]*=np.sin(np.linspace(0,np.pi,H))[:,None]**2
atlas=np.concatenate([bleed(body),bleed(outer),bleed(fringe),bleed(fringe)],axis=0)
Image.fromarray(np.uint8(np.clip(atlas,0,1)*255)).save(p/'textures/m508_wind.png')
height=(512-np.linspace(246,496,25))/200;r=np.mean(profiles,axis=0);r=np.interp(np.linspace(0,250,25),np.arange(251),r)/200
profile={'height_m':height.tolist(),'radius_m':r.tolist(),'wind_top':float(height[0]),'wind_bottom':float(height[-1]),'source':str(source),'frames':names}
(p/'textures/profile.json').write_text(json.dumps(profile,indent=2)+'\n')
# Isolate bright electric pixels in the original raised-left-hand region, keeping the authored branching.
im=np.asarray(Image.open(source/'m508ac0.png').convert('RGBA'),dtype=float)/255
# Source left hand is in the right half of this front view.
brightness=im[...,:3].min(2);fxalpha=im[...,3]*np.clip((brightness-.80)/.16,0,1)
mask=np.zeros_like(fxalpha);mask[:125,330:480]=1
mask*=np.clip((125-np.arange(512)[:,None])/15,0,1);fxalpha*=mask
ys,xs=np.where(fxalpha>.05);assert len(xs)>100
pad=8;x0,x1=max(0,xs.min()-pad),min(im.shape[1],xs.max()+pad+1);y0,y1=max(0,ys.min()-pad),min(im.shape[0],ys.max()+pad+1)
fx=np.dstack((im[y0:y1,x0:x1,:3],fxalpha[y0:y1,x0:x1]));fx=bleed(fx)
canvas=Image.new('RGBA',(512,512));imfx=Image.fromarray(np.uint8(np.clip(fx,0,1)*255));imfx=imfx.resize((round(imfx.width*480/max(imfx.size)),round(imfx.height*480/max(imfx.size))),Image.Resampling.LANCZOS);canvas.alpha_composite(imfx,((512-imfx.width)//2,(512-imfx.height)//2));canvas.save(p/'textures/m508_lightning.png')
# The body is a pale cloud material; the bake preserves broad shading and soft turbulent detail.
core=arrays[0][95:245,215:300];pixels=core[core[...,3]>.9,:3];lum=pixels@np.array([.2126,.7152,.0722]);order=np.argsort(lum)
colors=[pixels[order[int((len(order)-1)*q)]].tolist() for q in [.10,.30,.50,.75,.92]]
(p/'textures/body_colors.json').write_text(json.dumps({'colors':colors},indent=2)+'\n')
(p/'textures/provenance.json').write_text(json.dumps({'sources':{n:hashlib.sha256((source/(n+'.png')).read_bytes()).hexdigest() for n in names+['m508ac0']},'method':'Accepted MM6 Air cylinder unwrap, layered blend order and UV scroll; MM8 restored pixels and native geometry measurements.'},indent=2)+'\n')
assert atlas.shape==(2048,1024,4) and np.isfinite(atlas).all() and r.min()>0
print('TEXTURES',profile,'body colors',colors)
