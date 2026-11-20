"""Native blue/green fish palettes, matched neck paint and wet nonmetal response."""
from pathlib import Path
import sys,json,numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';N=1024
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(P.parents[2]/'tools'));from normal_map_convention import measure
def load(p,mode='RGB'):return np.asarray(Image.open(p).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(a,p):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(p,optimize=True)
def pad(a,cov):return a[tuple(ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True))]
def hsv(img):
 v=np.asarray(Image.fromarray(np.uint8(np.clip(img,0,1)*255)).convert('HSV'),float)/255
 return v[...,0]*360,v[...,1],v[...,2]
images={k:load(P/'meshy'/f'{k}_retexture_v1/texture_urls_0_base_color.png') for k in ['body','head']}
data={k:np.load(P/'work'/f'uvraster_{k}.npz') for k in images};hd=data['head'];uv=hd['body_uv'];pos=hd['pos']
sample=ndimage.map_coordinates(images['body'],[np.broadcast_to(((1-uv[...,1])*N-.5)[...,None],(N,N,3)),np.broadcast_to((uv[...,0]*N-.5)[...,None],(N,N,3)),np.broadcast_to(np.arange(3),(N,N,3))],order=1,mode='nearest')
# Both paints use the same surface; crossfade only across the neck, below the gills and eyes.
f=np.clip((pos[...,2]-1.54)/.12,0,1);f=f*f*(3-2*f);images['head']=sample*(1-f[...,None])+images['head']*f[...,None]
regions={};reports={}
for label,img in images.items():
 d=data[label];cov=d['piece']>=0;pos=d['pos'];h,s,v=hsv(img)
 eye=cov&(h>32)&(h<72)&(s>.5)&(pos[...,2]>1.64)&(abs(pos[...,0])>.035) if label=='head' else np.zeros_like(cov)
 fin=cov&((h>285)|(h<25))&(s>.16)&(v>.25)
 pale=cov&(s<.28)&(v>.25)&~eye&~fin
 scale=cov&~pale&~fin&~eye&(h>125)&(h<290)
 regions[label]=[scale,pale,fin];cl=np.zeros((N,N),np.uint8);cl[cov]=1;cl[fin]=3;cl[eye]=6
 ao=ndimage.gaussian_filter(pad(load(T/f'm500_{label}_ao.png','L'),cov),1)
 img*= (.85+.15*np.maximum(ao,.4))[...,None];images[label]=img
 normal_path=P/'meshy'/f'{label}_retexture_v1/texture_urls_0_normal.png'
 raw=np.asarray(Image.open(normal_path).convert('RGB')).copy();corr=measure(raw)
 if corr<=-.15:raw[...,1]=255-raw[...,1]
 normal=np.asarray(Image.fromarray(raw).resize((N,N),Image.Resampling.LANCZOS),float)/255
 normal=normal*2-1;normal/=np.maximum(np.linalg.norm(normal,axis=-1,keepdims=True),1e-6);normal=normal*.5+.5
 # Flatten the fine normal at the paint transition, avoiding an artificial neck seam.
 u=np.clip(abs(pos[...,2]-1.54)/.015,0,1);normal=normal*u[...,None]+np.array([.5,.5,1])*(1-u[...,None])
 rough=load(P/'meshy'/f'{label}_retexture_v1/texture_urls_0_roughness.png','L')
 rg=np.clip(.49+.16*(rough-.5),.40,.60);rg[pale]=.52;rg[fin]=.53;rg[eye]=.22
 spec=np.full((N,N),.33);spec[pale]=.28;spec[fin]=.22;spec[eye]=.85
 save(pad(img,cov),T/f'm500_{label}_basecolor_1k.png');save(pad(normal,cov),T/f'm500_{label}_normal_1k.png');save(np.stack([pad(spec,cov),pad(rg,cov),np.zeros((N,N))],-1),T/f'm500_{label}_metal_rough_1k.png')
 R.write_mask([ndimage.gaussian_filter(pad(m.astype(float),cov),.5) for m in regions[label]],T/f'm500_{label}_region_mask.png',size=N)
 Image.fromarray(cl).save(T/f'm500_{label}_material_classes.png')
 reports[label]={'region_texels':[int(m.sum()) for m in regions[label]],'eye_texels':int(eye.sum()),'normal_correlation':float(corr),'flipped_green':bool(corr<=-.15),'specular_range':[float(spec[cov].min()),float(spec[cov].max())]}
 assert all(m.sum()>100 for m in regions[label])
root=P.parents[2];pals={n:np.frombuffer((root/f'assets_dev/worlds/mm8/textures/pal{n}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for n in [501,502]}
ids=np.concatenate([np.asarray(Image.open(root/f'assets_dev/engine/sprites/m500sa{v}.bmp')).ravel() for v in range(5)]);ids=ids[ids!=0];native=pals[501][ids];h,s,v=hsv(native[:,None]);h,s,v=h[:,0],s[:,0],v[:,0]
select=[(h>155)&(h<285)&(s>.2),(s<.25)&(v>.25),((h>285)|(h<20))&(s>.15)&(v>.2)]
ramps={};native_report={}
for variant,palette in [('water_a',501),('water_b',502),('water_c',501)]:
 ramps[variant]=[];native_report[variant]=[]
 for c in range(3):
  cols=pals[palette][ids[select[c]]];assert len(cols)>100
  gain=[1.65,1.14,1.12][c];target=np.clip(np.median(cols,axis=0)*gain,0,1)
  L=np.concatenate([R.luminance(images[k][regions[k][c]]) for k in images]);lo,hi=np.percentile(L,[1,99]);mid=float(np.median(L))
  ramps[variant].append({'range':[float(lo),float(hi)],'colors':[np.clip(R.srgb_to_linear(target)*((lo+i/15*(hi-lo))/mid),0,1).tolist() for i in range(16)]})
  native_report[variant].append({'native_samples':len(cols),'target_srgb':target.tolist(),'gain':gain})
assert ramps['water_a']==ramps['water_c'] and ramps['water_a']!=ramps['water_b']
cfg={'variants':list(ramps),'palettes':dict(zip(ramps,[501,502,501])),'materials':[{'base':name+'_A','prefix':name,'mask':f'm500_{label}_region_mask.png','regions':['scales','ventral','fins'],'ramps':ramps} for label,name in [('body','WaterElemental'),('head','WaterElementalHead')]]}
(T/'m500_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n');reports.update(native=native_report,contract='MR.R specular mask; MR.G roughness; MR.B zero metallic; subtle AO in base colour')
(T/'composition_report.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports))

import runpy
runpy.run_path(str(P/'scripts/project_brow_texture.py'),run_name='__main__')
