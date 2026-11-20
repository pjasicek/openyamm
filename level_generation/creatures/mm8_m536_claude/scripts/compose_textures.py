"""Separate skin, silver cuffs and native palette gems; matching 1K body/head maps."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';N=1024
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(P.parents[2]/'tools'));from normal_map_convention import measure
W=np.array([.2126,.7152,.0722])
def save(a,path):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path,optimize=True)
def load(label,suffix):return np.asarray(Image.open(P/f'meshy/{label}_retexture_v1/texture_urls_0_{suffix}.png').convert('RGB').resize((N,N),Image.Resampling.LANCZOS),float)/255
def pad(a,cov):return a[tuple(ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True))]
def hsv(a):return np.moveaxis(np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('HSV'),float)/255,-1,0)
images={k:load(k,'base_color') for k in ['body','head']};rasters={k:np.load(P/f'work/uvraster_{k}.npz') for k in images};masks={};skins={}
for label,img in images.items():
 d=rasters[label];cov=d['piece']>=0;pos=d['pos'];h,s,v=hsv(img);skins[label]=cov&(h>.035)&(h<.18)&(s>.28)
 masks[label]=cov&(h>.22)&(h<.47)&(s>.42)&(v>.18)&(np.abs(pos[...,0])>.38)&(pos[...,2]<1.95) if label=='body' else np.zeros_like(cov)
b=rasters['body']['pos'];hpos=rasters['head']['pos'];bm=skins['body']&(b[...,2]>2.43)&(b[...,2]<2.52);hm=skins['head']&(hpos[...,2]<2.61)
assert bm.sum()>50 and hm.sum()>50 and masks['body'].sum()>100
seam_gain=float(np.clip(np.median(R.luminance(images['body'][bm]))/np.median(R.luminance(images['head'][hm])),.6,1.6))
x=R.srgb_to_linear(images['head']);x[skins['head']]*=seam_gain;images['head']=np.where(x<=.0031308,12.92*x,1.055*np.maximum(x,0)**(1/2.4)-.055)
# Only native palette entries 2..23 change. Golden skin, flames and green eyes remain fixed.
ids=[]
for view in range(5):
 a=np.asarray(Image.open(P.parents[2]/f'assets_dev/engine/sprites/m536Wa{view}.bmp'));ids.extend(a[(a>=2)&(a<=23)].tolist())
ids=np.array(ids);assert len(ids)>100
lum=R.luminance(images['body'][masks['body']]);lo,hi=np.percentile(lum,[1,99]);ramps={};pals={'m536_a':537,'m536_b':538,'m536_c':539}
for name,index in pals.items():
 pal=np.frombuffer((P.parents[2]/f'assets_dev/worlds/mm8/textures/Pal{index}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255;col=R.srgb_to_linear(pal[ids]);col=col[np.argsort(col@W)];native=np.median(col[len(col)//4:3*len(col)//4],axis=0);chroma=native/max(native@W,1e-7);gain=(native@W)/np.median(lum)
 ramps[name]=[{'range':[float(lo),float(hi)],'colors':[np.clip(chroma*(lo+j/15*(hi-lo))*gain,0,1).tolist() for j in range(16)]}]
report={}
for label,img in images.items():
 d=rasters[label];cov=d['piece']>=0;pos=d['pos'];h,s,v=hsv(img);gem=masks[label];metal=cov&(np.abs(pos[...,0])>.39)&(pos[...,2]>1.70)&(pos[...,2]<1.94)&~gem if label=='body' else np.zeros_like(cov)
 eye=cov&(h>.22)&(h<.48)&(s>.4)&(v>.24) if label=='head' else np.zeros_like(cov)
 normal=load(label,'normal');score=measure(np.uint8(normal*255+.5));assert score<-.15,(label,score);normal[...,1]=1-normal[...,1]
 rough=load(label,'roughness')[...,0];spec=np.full((N,N),.16);rg=np.clip(.84+.2*(rough-.5),.70,.94);met=np.zeros((N,N));spec[metal]=.85;rg[metal]=np.clip(.38+.2*(rough[metal]-.5),.25,.5);met[metal]=.65;spec[gem|eye]=.6;rg[gem|eye]=.23
 # A narrow neutral normal band avoids a tangent seam between independently painted sets.
 seam=np.clip(1-np.abs(pos[...,2]-2.52)/.012,0,1);normal=normal*(1-seam[...,None])+np.array([.5,.5,1.])*seam[...,None]
 save(pad(img,cov),T/f'm536_{label}_basecolor_1k.png');save(pad(normal,cov),T/f'm536_{label}_normal_1k.png');save(np.stack([pad(spec,cov),pad(rg,cov),pad(met,cov)],-1),T/f'm536_{label}_metal_rough_1k.png');R.write_mask([ndimage.gaussian_filter(pad(gem.astype(float),cov),.5)],T/f'm536_{label}_region_mask.png',size=N)
 classes=np.zeros((N,N),np.uint8);classes[cov]=1;classes[metal]=9;classes[eye]=6;classes[gem]=11;Image.fromarray(classes).save(T/f'm536_{label}_material_classes.png');overlay=img*.4;overlay[gem]=(.1,1,.2);overlay[metal]=(.2,.6,1);save(overlay,P/'review'/f'{label}_regions.png');report[label]={'gem_texels':int(gem.sum()),'metal_texels':int(metal.sum()),'normal_integrability_before':score}
cfg={'variants':list(pals),'palettes':pals,'head_skin_linear_gain':seam_gain,'report':report,'materials':[{'base':name+'_A','prefix':name,'mask':f'm536_{label}_region_mask.png','regions':['gems'],'ramps':ramps} for label,name in [('body','Efreeti'),('head','EfreetiHead')]]};(T/'m536_ramps.json').write_text(json.dumps(cfg,indent=2));print('COMPOSE',report,'head gain',seam_gain)
