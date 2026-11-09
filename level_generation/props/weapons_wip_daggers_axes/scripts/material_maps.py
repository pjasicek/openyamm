"""Derive padded UV swatches and technical PBR data from the retained imagegen atlas."""
import hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];src=P/'references/material_atlas_v1.png'
im=Image.open(src).convert('RGB');assert im.width==im.height
out=P/'textures';out.mkdir(exist_ok=True)
base=np.empty((1024,1024,3),dtype=np.uint8);mr=np.empty_like(base);normal=np.empty_like(base)
metals={0,1,2,3,12,13,14,15};rough=[.36,.48,.56,.43,.71,.72,.68,.67,.62,.69,.48,.28,.39,.42,.38,.4]
for index in range(16):
 x=index%4;y=index//4;size=im.width/4
 cell=im.crop((round(x*size)+4,round(y*size)+4,round((x+1)*size)-4,round((y+1)*size)-4)).resize((256,256),Image.Resampling.LANCZOS)
 rgb=np.clip(np.array(cell),30,243).astype(np.uint8);base[y*256:(y+1)*256,x*256:(x+1)*256]=rgb
 metallic=np.full((256,256),255 if index in metals else 0,dtype=np.uint8)
 if index==14:metallic=np.where(rgb[...,1].astype(float)>rgb[...,0]*.55,255,0).astype(np.uint8)
 mr[y*256:(y+1)*256,x*256:(x+1)*256]=np.stack([np.full((256,256),255),np.full((256,256),round(rough[index]*255)),metallic],axis=-1)
 # Only high-frequency surface marks affect the tangent normal; broad albedo variation never changes roughness.
 lum=rgb.astype(float).mean(-1)/255;blur=lum.copy()
 for _ in range(3):blur=(blur+np.roll(blur,1,0)+np.roll(blur,-1,0)+np.roll(blur,1,1)+np.roll(blur,-1,1))/5
 detail=(lum-blur)*.25;dx=np.gradient(detail,axis=1);dy=-np.gradient(detail,axis=0)
 n=np.stack([-dx,-dy,np.ones_like(lum)],-1);n/=np.linalg.norm(n,axis=-1,keepdims=True)
 normal[y*256:(y+1)*256,x*256:(x+1)*256]=np.round((n*.5+.5)*255).astype(np.uint8)
for name,array in [('basecolor',base),('mr',mr),('normal',normal)]:Image.fromarray(array).save(out/f'materials_{name}.png')
assert set(np.unique(mr[...,2]))=={0,255};assert base.min()>=30 and base.max()<=243
receipt={'tool':'built-in imagegen','raw':str(src),'raw_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'prompt':str(P/'references/material_atlas_prompt.txt'),'selected':True,'derivation':'Crop four-pixel source gutters; resize exact cells to 256; technical base-colour clamp; explicit per-cell metallic/roughness; OpenGL +Y micro-normal.','texture_size':[1024,1024],'roughness':'constant per material, independent of albedo brightness','metallic':'binary material classification; red enamel/gold cell classified by its known palette'}
runs=json.loads((P/'generation_runs.json').read_text()) if (P/'generation_runs.json').exists() else {};runs['material_atlas']=receipt;runs.setdefault('meshy',{});(P/'generation_runs.json').write_text(json.dumps(runs,indent=2)+'\n')
print('Atlas PBR maps verified: binary metallic, 30–243 sRGB base, fixed material roughness.')
