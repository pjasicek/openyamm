"""Compose the paid mace maps for the current engine specular contract; preserve its original UV atlas."""
from pathlib import Path
import json,sys,numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array
sets=[]
for path in [p/'texturing/fgt_mace_upload.glb',p/'meshy/mace_retexture_v1/model_urls_glb.glb']:
 d,b=read_glb(path);pcs=[];uvs=[]
 for mesh in d['meshes']:
  for pr in mesh['primitives']:
   pcs.append(accessor_array(d,b,pr['attributes']['POSITION']));uvs.append(accessor_array(d,b,pr['attributes']['TEXCOORD_0']))
 co=np.concatenate(pcs);uv=np.concatenate(uvs);co=(co-(co.min(0)+co.max(0))/2)/np.ptp(co,axis=0).max();sets.append((co,uv))
s,suv=sets[0];t,tuv=sets[1];tree=cKDTree(t);ds,_=tree.query(s);worst=0
for pos,uv in zip(s,suv):
 ids=tree.query_ball_point(pos,.00025);assert ids,'Returned geometry changed'
 worst=max(worst,float(np.linalg.norm(tuv[ids]-uv,axis=1).min()))
assert ds.max()<.00025 and worst<1/1024,'Original mace UVs changed'
N=1024;mask=Image.new('L',(N,N));draw=ImageDraw.Draw(mask)
for f in json.loads((p/'work/mace_uv.json').read_text()):draw.polygon([(u*N,(1-v)*N) for u,v in f['uv']],fill=f['cls'])
cls=np.array(mask);ix=distance_transform_edt(cls==0,return_distances=False,return_indices=True);cls=cls[tuple(ix)]
def load(name,mode='RGB'):
 return np.asarray(Image.open(p/'meshy/mace_retexture_v1'/('texture_urls_0_'+name+'.png')).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
base=load('base_color');normal=load('normal');rough=load('roughness','L')
# Blackened iron stays darker than the satin-steel shaft in both the engine and portable viewer.
base[cls==3]*=.72
spec=np.choose(cls,[.5,.30,.82,.66]);r=np.choose(cls,[.6,.73,.36,.52])+.25*(rough-.5)
mr=np.stack([spec,np.clip(r,.25,.92),np.zeros_like(r)],-1)
for name,pixels in [('basecolor',base),('normal',normal),('metal_rough',mr)]:Image.fromarray(np.uint8(np.clip(pixels,0,1)*255+.5)).save(p/'textures'/('fgt_mace_'+name+'_1k.png'))
(p/'review/revision1/mace_texture_validation.json').write_text(json.dumps({'original_uv_max_error_texels':worst*N,'position_max_error_m':float(ds.max()*.562),'texture_resolution':N,'classes':sorted(set(cls.ravel().tolist())),'credits':10},indent=2))
print('MACE UV',worst*N,'texels, geometry',float(ds.max()*.562)*1000,'mm')
