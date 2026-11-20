"""Bake the generated painted designs into a shared 2K atlas; keep colour variants mask-driven."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter
P=Path(__file__).resolve().parents[1];T=P/'textures';D=P/'references_hd/round2_equipment';N=2048
axe=Image.open(D/'axe_side.png').convert('RGB');shield=Image.open(D/'shield_front.png').convert('RGB')
assert axe.size==shield.size==(1024,1536)
atlas=Image.new('RGB',(N,N),(55,49,42));atlas.paste(shield,(0,0));atlas.paste(axe,(1024,0))
# Supplemental curved surfaces sample painted materials from the same designs, never solid fills.
sources={'steel':(axe,(460,190,560,440)),'edge':(axe,(147,220,164,330)),
 'wood':(axe,(471,510,550,845)),'leather':(axe,(471,960,551,1312)),
 'brass':(shield,(482,543,538,666))}
tiles={}
for i,(name,(im,box)) in enumerate(sources.items()):
 x=i*384+8;y=1544;tile=im.crop(box).resize((368,480),Image.Resampling.LANCZOS);atlas.paste(tile,(x,y));tiles[name]=[x+4,y+4,x+364,y+476]
base=np.array(atlas,dtype=float)/255;hsv=np.array(atlas.convert('HSV'),dtype=float)/255
h,s,v=hsv.transpose(2,0,1);mask=np.zeros((N,N,4),float)
# Region selection follows the painted materials. Black star, oxide, leather, wood and brass remain untouched.
mask[:1536,:,2]=((s[:1536]<.18)&(v[:1536]>.16)).astype(float)
paint=np.zeros((N,N),bool);paint[:1536,:1024]=(s[:1536,:1024]>.26)&(h[:1536,:1024]>.055)&(h[:1536,:1024]<.16)
mask[paint]=[1,0,0,0]
for kind in ['steel','edge']:
 x0,y0,x1,y1=tiles[kind];mask[y0-4:y1+4,x0-4:x1+4,2]=1
lum=base@np.array([.2126,.7152,.0722]);micro=lum-gaussian_filter(lum,2.3);gy,gx=np.gradient(gaussian_filter(micro,.55))
normal=np.stack([-gx*1.7,gy*1.7,np.ones_like(lum)],-1);normal/=np.linalg.norm(normal,axis=2)[:,:,None]
rough=np.clip(.76-micro*.45,.57,.9);spec=np.where(mask[:,:,2]>.5,.28,.17)
for name,data in [('basecolor',base),('normal',normal*.5+.5),('metal_rough',np.stack([spec,rough,np.zeros_like(lum)],-1))]:Image.fromarray(np.uint8(np.clip(data,0,1)*255+.5)).save(T/f'figc_gear_{name}_2k.png')
Image.fromarray(np.uint8(mask*255)).save(T/'figc_gear_region_mask.png')
(T/'figc_gear_tiles.json').write_text(json.dumps(tiles,indent=2)+'\n')
cfg=json.loads((T/'figc_ramps.json').read_text());template=cfg['materials'][0];ramps={}
lin=lambda a:np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
# Ochre is already painted in A. B/C use the same worn paint luminance, without recolouring exposed iron chips.
for tier,tint in {'figc_a':[1,1,1],'figc_b':[.59,.19,.23],'figc_c':[.91,.41,.25]}.items():
 rr=json.loads(json.dumps(template['ramps'][tier]));rr[0]={'range':[0,1],'colors':[(lin(np.array([.69,.47,.19]))/(lin(np.array([.69,.47,.19]))@np.array([.2126,.7152,.0722]))*j/15*np.array(tint)).clip(0,1).tolist() for j in range(16)]};ramps[tier]=rr
cfg['materials']=[m for m in cfg['materials'] if m['base']!='FighterChainGear_A']
cfg['materials'].append({'base':'FighterChainGear_A','prefix':'FighterChainGear','mask':'figc_gear_region_mask.png','regions':template['regions'],'palettes':template['palettes'],'ramps':ramps})
(T/'figc_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n')
assert np.isfinite(normal).all() and np.max(abs(np.linalg.norm(normal,axis=2)-1))<1e-10
print('Painted 2K atlas from imagegen designs; image-derived surface normal and roughness')
