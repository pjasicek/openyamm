"""Bake the actual runtime tier colours for an identical-lighting revision comparison."""
import sys,copy,numpy as np
from pathlib import Path
from PIL import Image
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,image_of,add_image,compact
linear=lambda c:np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
srgb=lambda c:np.where(c<=.0031308,c*12.92,1.055*np.maximum(c,0)**(1/2.4)-.055)
folder=P/'review/round3_skin_models';folder.mkdir(exist_ok=True)
for revision,path in [(1,'work/review_round2_before/export/mm6_natm.glb'),(2,'work/review_round3_before/export/mm6_natm.glb'),(3,'export/mm6_natm.glb')]:
 d,b=read_glb(P/path);node=next(n for n in d['nodes']if n.get('name')=='Natm');d['meshes']=[copy.deepcopy(d['meshes'][node['mesh']])];node['mesh']=0;d['meshes'][0].pop('extras',None);used=set()
 for pr in d['meshes'][0]['primitives']:
  mappings=pr.get('extensions',{}).get('KHR_materials_variants',{}).get('mappings',[]);pr['material']=next(m['material']for m in mappings if 0 in m['variants']);used.add(pr['material']);pr.pop('extensions',None)
 for i in used:
  mat=d['materials'][i];base=mat['pbrMetallicRoughness']['baseColorTexture'];im,_=image_of(d,b,base['index']);rgba=np.asarray(im.convert('RGBA'),float)/255;rgb=linear(rgba[...,:3]);lum=rgb@np.array([.2126,.7152,.0722]);mask,_=image_of(d,b,mat['extras']['openyamm_region_mask']['index']);mask=np.asarray(mask.convert('RGBA'),float)/255;out=rgb.copy()
  for c,reg in enumerate(mat['extras']['openyamm_region_ramps']):
   x=np.clip((lum-reg['range'][0])/(reg['range'][1]-reg['range'][0]),0,1)*15;idx=np.minimum(x.astype(int),14);f=x-idx;colors=np.array(reg['colors']);mapped=colors[idx]*(1-f[...,None])+colors[idx+1]*f[...,None];a=mask[...,c:c+1];out=out*(1-a)+mapped*a
  image=Image.fromarray(np.uint8(np.dstack([np.clip(srgb(out),0,1),rgba[...,3]])*255+.5));base['index']=add_image(d,b,image,f'Round{revision}',d['textures'][base['index']].get('sampler'));mat['extras'].pop('openyamm_region_mask',None);mat['extras'].pop('openyamm_region_ramps',None)
 d.pop('extensions',None);d.pop('extensionsUsed',None);d,b=compact(d,b);write_glb(folder/f'round{revision}.glb',d,b)
