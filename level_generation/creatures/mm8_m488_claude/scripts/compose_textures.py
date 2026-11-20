"""Compose matte fur/cloth, native cloth ramps and a dedicated head texture set."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2]
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
T=P/'textures';T.mkdir(exist_ok=True);N=1024

def load(path,mode='RGB'):
 return np.asarray(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255

def save(a,path):
 Image.fromarray(np.uint8(np.clip(a*255+.5,0,255))).save(path,optimize=True)

def pad(a,cov):
 ix=ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True)
 return a[tuple(ix)]

palettes={f'm488_{k}':np.frombuffer((ROOT/f'assets_dev/worlds/mm8/textures/Pal{i}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for k,i in zip('abc',(489,490,491))}
changed=np.maximum(abs(palettes['m488_a']-palettes['m488_b']).max(1),abs(palettes['m488_a']-palettes['m488_c']).max(1))>8/255
# Central cloth pixels exclude palette-dependent antialiasing on the black fur.
im=Image.open(ROOT/'assets_dev/engine/sprites/m488Sa0.bmp');assert im.mode=='P'
ids=np.asarray(im)[160:194,108:148].ravel();rgb=palettes['m488_a'][ids]
ids=ids[(rgb[:,1]>1.25*np.maximum(rgb[:,0],rgb[:,2]))&(rgb[:,1]>.15)];assert len(ids)>300
native={key:np.median(R.srgb_to_linear(pal[ids]),axis=0) for key,pal in palettes.items()}
report={};ramps={};cfg={'variants':list(palettes),'materials':[]}
for head in (False,True):
 tag='m488_head' if head else 'm488';job='head_retexture_v1' if head else 'retexture_v1'
 M=P/'meshy'/job;r=np.load(P/'work'/('uvraster_HeadUV.npz' if head else 'uvraster_UVMap.npz'))
 piece,pos=r['piece'],r['pos'];cov=piece>=0
 base=load(M/'texture_urls_0_base_color.png');rough=load(M/'texture_urls_0_roughness.png','L');normal=load(M/'texture_urls_0_normal.png')
 hsv=np.array(Image.fromarray(np.uint8(base*255)).convert('HSV'),float)/255
 hue,sat,val=hsv[...,0]*360,hsv[...,1],hsv[...,2]
 cloth=cov&((piece==1)|((piece==2)&(hue>65)&(hue<170)&(sat>.2))) if not head else np.zeros_like(cov)
 rope=cov&np.isin(piece,[2,3,4])&~cloth
 hoof=cov&(pos[...,2]<.17)
 horn=cov&(pos[...,2]>1.96)&(abs(pos[...,0])>.10)&(sat>.12)&(hue<65)
 eye=cov&(((abs(pos[...,0])-.10)/.025)**2+((pos[...,2]-1.883)/.018)**2<1)&(pos[...,1]<-.08)&(val<.3) if head else np.zeros_like(cov)
 spec=np.full((N,N),.12);rg=np.full((N,N),.88);labels=np.full((N,N),2,np.uint8)
 for mask,sp,rr,lab in [(cloth,.05,.94,7),(rope,.15,.86,8),(hoof|horn,.42,.55,4),(eye,.65,.25,5)]:
  spec[mask]=sp;rg[mask]=rr;labels[mask]=lab
 rg=np.clip(rg+.2*(rough-ndimage.gaussian_filter(rough,10)),.2,1)
 ao=load(P/'work'/('ao_head.png' if head else 'ao_body.png'),'L')
 base*= (1-.25*(1-np.maximum(ao,.35)))[...,None]
 if head:
  uv=r['other_uv'];xx=np.clip((uv[...,0]*N).astype(int),0,N-1);yy=np.clip(((1-uv[...,1])*N).astype(int),0,N-1)
  full=load(P/'meshy/retexture_v1/texture_urls_0_base_color.png');ao_body=load(P/'work/ao_body.png','L')
  full*=(1-.25*(1-np.maximum(ao_body,.35)))[...,None]
  weight=np.clip(r['seam_distance']/.045,0,1);weight=weight*weight*(3-2*weight)
  base=base*weight[...,None]+full[yy,xx]*(1-weight[...,None])
 # Native rear view has a continuous black back and shoulder mantle.
 def smooth(v):
  v=np.clip(v,0,1);return v*v*(3-2*v)
 mantle=(piece==0)*smooth(pos[...,1]/.06)*smooth((pos[...,2]-1.16)/.08)*smooth((1.82-pos[...,2])/.06)*smooth((.49-abs(pos[...,0]))/.06)
 dark=np.minimum(base,(.07+.045*base.mean(2))[...,None]*np.array([.93,.96,1.]))
 base=base*(1-mantle[...,None])+dark*mantle[...,None]
 base=pad(base,cov);normal=pad(normal,cov)
 vec=normal*2-1;vec/=np.maximum(np.linalg.norm(vec,axis=2,keepdims=True),1e-8);normal=vec*.5+.5
 if not head:
  lum=np.sort(R.luminance(base)[cloth]);lo,hi=np.percentile(lum,[2,98]);assert hi>lo+.001
  median_lum=float(np.median(lum))
  for key in palettes:
   # Preserve Meshy's smooth luminance detail instead of amplifying native palette quantization.
   stops=[np.clip(native[key]*1.35*(lo+i/15*(hi-lo))/median_lum,0,1).round(6).tolist() for i in range(16)]
   ramps[key]=[{'range':[float(lo),float(hi)],'colors':stops}]
 mask=ndimage.gaussian_filter(pad(cloth.astype(float),cov),.6)
 R.write_mask([mask],T/(tag+'_region_mask.png'),size=N)
 save(base,T/(tag+'_basecolor_1k.png'));save(normal,T/(tag+'_normal_1k.png'))
 save(pad(np.stack([spec,rg,np.zeros_like(rg)],-1),cov),T/(tag+'_metal_rough_1k.png'))
 Image.fromarray(pad(labels,cov)).save(T/(tag+'_material_classes.png'))
 prefix='MinotaurHead' if head else 'Minotaur'
 cfg['materials'].append({'base':prefix+'_A','prefix':prefix,'mask':tag+'_region_mask.png','regions':['cloth'],'palettes':{f'm488_{k}':i for k,i in zip('abc',(489,490,491))},'ramps':ramps})
 report[tag]={'covered':int(cov.sum()),'cloth':int(cloth.sum()),'rope':int(rope.sum()),'horn_hoof':int((horn|hoof).sum()),'eyes':int(eye.sum())}
(T/'m488_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n');(T/'composition.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
