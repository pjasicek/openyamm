"""Fire maps sampled from restored m496; MM6 fire supplies the shell/fringe construction method."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
P=Path(__file__).resolve().parents[1]
source=P.parent/'mm8_packed_outline_collection_20261002/families/mm8_m496/aligned_2x'
sys.path.insert(0,str(P.parent/'mm6_fie1_claude/scripts'))
from make_texture import bleed,sample,tile
names=['m496wa0','m496wb4','m496wc0','m496wd4','m496we0','m496wf4']
images=[np.asarray(Image.open(source/(name+'.png')).convert('RGBA'),float)/255 for name in names]
# Separate yellow/orange flame from the native dark red figure, retaining soft flame edges.
def flame(im):
 rgb=im[...,:3];return im[...,3]*np.clip((rgb[...,1]-.20)/.28,0,1)*np.clip((rgb[...,0]-.35)/.25,0,1)
# Reuse the direct MM6 Fire effect tile, recoloured toward MM8's orange-red flame.
# Its core-mask holes retain visibility through both shell faces.
reference=P.parent/'mm6_fie1_claude/textures/fie1_flame.png'
rgba=np.asarray(Image.open(reference).convert('RGBA'),float)/255
rgba[...,:3]*=np.array([1.0,.88,.70])
coverage=rgba[...,3]
Image.fromarray(np.uint8(np.clip(rgba,0,1)*255)).save(P/'textures/m496_flame.png')
# A crown/palm tongue taken from the long attack plume; no generated pixels or paid assets.
im=np.asarray(Image.open(source/'m496ad0.png').convert('RGBA'),float)/255
im[...,3]=flame(im)
fx=im[42:246,180:330].copy();fx[...,3]*=np.minimum(np.clip(np.arange(fx.shape[0])/12,0,1),np.clip((fx.shape[0]-1-np.arange(fx.shape[0]))/12,0,1))[:,None]
fx=bleed(fx);out=Image.new('RGBA',(512,512));part=Image.fromarray(np.uint8(np.clip(fx,0,1)*255));part=part.resize((round(part.width*480/max(part.size)),round(part.height*480/max(part.size))),Image.Resampling.LANCZOS);out.alpha_composite(part,((512-part.width)//2,512-part.height));# Separate the native looping crown from the tall attack plume.
crown=np.asarray(Image.open(source/'m496aa0.png').convert('RGBA'),float)/255
crown[...,3]=flame(crown)
y,x=np.indices(crown.shape[:2]);gap=np.sqrt(((x-254)/28)**2+((y-220)/40)**2);crown[...,3]*=np.clip((gap-.65)/.5,0,1)
crown=Image.fromarray(np.uint8(np.clip(bleed(crown[100:285,165:350]),0,1)*255)).resize((480,480),Image.Resampling.LANCZOS)
atlas=Image.new('RGBA',(1024,512));atlas.alpha_composite(out,(0,0));atlas.alpha_composite(crown,(528,16));atlas.save(P/'textures/m496_burst.png')

pixels=np.concatenate([im[...,:3][(im[...,3]>.9)&(im[...,0]>.18)&(im[...,1]<.23)&(im[...,0]>im[...,1]*2)] for im in images])
order=np.argsort(pixels@np.array([.2126,.7152,.0722]));colors=[np.median(pixels[order[max(0,int(len(order)*q)-100):int(len(order)*q)+100]],axis=0).tolist() for q in [.1,.3,.5,.75,.92]]
(P/'textures/body_colors.json').write_text(json.dumps({'colors':colors},indent=2)+'\n')
# Native ash mound is a persistent corpse, unlike MM6 Fire's empty corpse.
ash=Image.open(source/'m496xa0.png').convert('RGBA');ash.crop(ash.getbbox()).resize((512,256),Image.Resampling.LANCZOS).save(P/'textures/m496_ash.png')
paths=[source/(name+'.png') for name in names+['m496ad0','m496aa0','m496xa0']]+[reference]
(P/'textures/provenance.json').write_text(json.dumps({'sources':{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},'method':'MM6 Fire flame tile tinted to MM8 orange-red; MM8 plume isolated by warm colour and applied on radial fins. Native core colours and ash corpse retained.'},indent=2)+'\n')
assert np.isfinite(rgba).all() and coverage.max()>.5 and len(pixels)>1000
print('Fire maps ready; core colours',colors)
