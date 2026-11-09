"""Shared Phoenix PBR atlas and native palette ramps; feather, keratin, eye and oral classes."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';N=2048
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(P.parents[2]/'tools'));from normal_map_convention import measure
W=np.array([.2126,.7152,.0722])
def load(p,mode='RGB'):return np.array(Image.open(p).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255

def save(a,p,size=N):
 im=Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5))
 if size!=N:im=im.resize((size,size),Image.Resampling.LANCZOS)
 im.save(p)
def pad(a):return a[tuple(nearest)]
def encode(a):return np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055)
d=np.load(P/'work/uvraster_body.npz');cov=d['piece']>=0;nearest=ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True)
assert not (d['coverage']>1).any(),'UV interior overlap'
parity=json.loads((P/'work/texture_uv_parity.json').read_text())['body']
def service(kind):
 a=load(P/f'meshy/body_retexture_v1/texture_urls_0_{kind}.png');src=a.copy()
 for repair in parity['repairs']:
  uv=np.array(repair['target_uv'])*N;dest=np.array(repair['source_uv'])*N
  x0,y0=np.maximum(np.floor(uv.min(0)).astype(int)-1,0);x1,y1=np.minimum(np.ceil(uv.max(0)).astype(int)+1,N-1)
  x,y=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5);weights=np.linalg.solve(np.vstack([uv.T,np.ones(3)]),np.stack([x.ravel(),y.ravel(),np.ones(x.size)]));mask=(weights>=-.02).all(0);sx,sy=dest.T@weights[:,mask];iy=(N-1-(y.ravel()[mask]-.5)).astype(int);ix=(x.ravel()[mask]-.5).astype(int)
  for channel in range(3):a[iy,ix,channel]=ndimage.map_coordinates(src[...,channel],[N-.5-sy,sx-.5],order=1,mode='nearest')
 for repair in parity['texel_repairs']:
  ix,iy=repair['pixel'];sx,sy=np.array(repair['source_uv'])*N
  for channel in range(3):a[iy,ix,channel]=ndimage.map_coordinates(src[...,channel],[[N-.5-sy],[sx-.5]],order=1,mode='nearest')[0]
 return a
rgb=service('base_color');x,y,z=np.moveaxis(d['pos'],-1,0);piece=d['piece'];h,s,v=np.moveaxis(np.array(Image.fromarray(np.uint8(rgb*255)).convert('HSV'),float)/255,-1,0)
oral=d['oral'];claw=np.isin(piece,[5,6,7,8,9,10]);beak=(y<-.177)&(z>.14);eye=(abs(x)>.017)&(abs(x)<.038)&(((y+.160)/.010)**2+((z-.174)/.006)**2<1)
classes=np.zeros((N,N),np.uint8);classes[cov]=2;classes[cov&(z<.070)]=1;classes[cov&(claw|beak)]=4;classes[cov&eye]=6;classes[oral]=7
rgb[oral]=(.025,.008,.005)
tail=cov&(y>.125)&(abs(x)<.096)&(z<.12)
wing=cov&(abs(x)>.080)&(z>.108)&(np.isin(piece,np.arange(20,71))|((h<.09)&(s>.28)))&(~tail)
body=cov&(~wing)&(~tail)
for mask in (body,wing,tail):mask[oral|claw|beak|eye]=False
masks=[body,wing,tail]
ao=ndimage.gaussian_filter(pad(load(T/'phoenix_body_ao_1k.png','L')),1.0);rgb*=.82+.18*ao[...,None]
normal=service('normal');correlation=measure(np.uint8(normal*255+.5))
if correlation<-.15:normal[...,1]=1-normal[...,1]
geo=load(T/'phoenix_body_geometry_normal_2k.png','RGBA');valid=geo[...,3]>.5
miss=int((cov&~valid).sum());assert miss<max(32,int(cov.sum()*.02)),('normal bake misses',miss)
n1=geo[...,:3]*2-1;n1[~valid]=(0,0,1);n2=normal*2-1;t=n1+np.array([0,0,1]);u=n2*np.array([-1,-1,1]);n=t*np.sum(t*u,axis=-1)[...,None]/np.maximum(t[...,2:3],1e-5)-u;n/=np.maximum(np.linalg.norm(n,axis=-1,keepdims=True),1e-5);normal=n*.5+.5;normal[oral]=(.5,.5,1)
rough=np.full((N,N),.85);spec=np.full((N,N),.12)
for cls,r,q in [(1,.80,.16),(4,.45,.40),(6,.18,.60),(7,.85,.05)]:rough[classes==cls]=r;spec[classes==cls]=q
spec*=.35+.65*ao
save(pad(rgb),T/'phoenix_basecolor_2k.png');save(pad(normal),T/'phoenix_normal_1k.png',1024);save(np.stack([pad(spec),pad(rough),np.zeros_like(rough)],-1),T/'phoenix_metal_rough_1k.png',1024);save(ao,T/'phoenix_ao_1k.png',1024)
Image.fromarray(pad(classes)).resize((1024,1024),Image.Resampling.NEAREST).save(T/'phoenix_material_classes.png')
R.write_mask([ndimage.gaussian_filter(pad(m.astype(float)),.65) for m in masks],T/'phoenix_region_mask.png',size=1024)
Image.new('RGB',(8,8),(255,0,0)).save(T/'phoenix_flame_mask.png')
palettes={str(i):np.frombuffer((P.parents[2]/f'assets_dev/worlds/mm8/textures/Pal{i}.act').read_bytes(),np.uint8).reshape(256,3)/255 for i in (573,574,575)}
indices=[list(range(96,192)),list(range(192,256)),list(range(1,15)),list(range(44,120))]
lum=R.luminance(rgb);ranges=[]
for m in masks:
 lo,hi=np.percentile(lum[m],[2,98]);assert hi>lo;ranges.append([float(lo),float(hi)])
def ramp(pal,ids,limits,gain):
 colors=R.srgb_to_linear(pal[ids])*gain;colors=colors[np.argsort(colors@W)]
 colors=np.array([np.interp(np.linspace(0,len(colors)-1,16),np.arange(len(colors)),colors[:,i]) for i in range(3)]).T
 return {'range':limits,'colors':np.clip(colors,0,1).tolist()}
variants=['m572_a','m572_b','m572_c'];bodyramps={};fireramps={}
for variant,pal in zip(variants,palettes.values()):
 bodyramps[variant]=[ramp(pal,ids,limits,1.35) for ids,limits in zip(indices,ranges)]
 fireramps[variant]=[ramp(pal,indices[3],[.05,.85],1.)]
materials=[{'base':'Phoenix_A','prefix':'Phoenix','mask':'phoenix_region_mask.png','regions':['body_coverts','orange_flight_feathers','dark_tail'],'ramps':bodyramps}]
for label in ['Flame']:materials.append({'base':'Phoenix_'+label,'prefix':'Phoenix_'+label,'mask':'phoenix_flame_mask.png','regions':['fire'],'ramps':fireramps})
report={'covered_texels':int(cov.sum()),'normal_bake_misses':miss,'normal_source_correlation':correlation,'region_texels':[int(m.sum()) for m in masks],'eye_class_texels':int((cov&eye).sum()),'palette_indices':indices,'body_luminance_ranges':ranges,'classes':{'1':'scaled legs','2':'feathers','4':'beak and talons','6':'eyes','7':'mouth'}}
(T/'phoenix_ramps.json').write_text(json.dumps({'variants':variants,'palettes':dict(zip(variants,[573,574,575])),'materials':materials,'report':report},indent=2)+'\n');(P/'work/texture_compose.json').write_text(json.dumps(report,indent=2)+'\n');print('PHOENIX TEXTURES',report)
