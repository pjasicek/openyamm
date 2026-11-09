"""Shared native cloth tiers and restrained leather/skin/metal response."""
from pathlib import Path
import json,sys,numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];repo=P.parents[2];sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
T=P/'textures';T.mkdir(exist_ok=True);N=1024
load=lambda p,mode='RGB',n=N:np.asarray(Image.open(p).convert(mode).resize((n,n),Image.Resampling.LANCZOS),float)/255
save=lambda a,p:Image.fromarray(np.round(np.clip(a,0,1)*255).astype('uint8')).save(p)
def pad(a,c):
 _,ix=ndimage.distance_transform_edt(~c,return_indices=True);out=a[tuple(ix)];out[c]=a[c];return out
def softnormal(a,strength):
 v=a*2-1;v[...,:2]*=strength;v/=np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-5);return v*.5+.5
def hsv(a):return np.asarray(Image.fromarray(np.round(a*255).astype('uint8')).convert('HSV'),float)/255
m=P/'meshy/body_retexture_v1';b=load(m/'texture_urls_0_base_color.png');r=np.load(P/'work/uvraster_UVMap.npz');g=r['piece'];cov=g>=0;h,s,v=np.moveaxis(hsv(b),-1,0)
cloth=cov&(np.isin(g,[9,18,20])|((g==0)&(h>.34)&(h<.57)&(s>.17)))
leather=np.isin(g,[3,6,7,11,12]);hair=np.isin(g,[5,10]);sash=np.isin(g,[8,14,15,19]);metal=np.isin(g,[13,21]);trouser=g==2
b*= (.78+.22*np.maximum(load(P/'work/ao_UVMap.png','L'),.4))[...,None]
spec=np.full((N,N),.28);rough=np.full((N,N),.74);classes=np.ones((N,N),np.uint8)
for mask,cl,sp,ro in [(cloth,8,.12,.90),(trouser|sash,8,.16,.87),(leather,8,.28,.74),(hair,8,.24,.78),(metal,9,.8,.38)]:spec[mask]=sp;rough[mask]=ro;classes[mask]=cl
b=np.where(cloth[...,None],ndimage.gaussian_filter(b,(1.0,1.0,0)),b)
save(pad(b,cov),T/'m416_basecolor_1k.png');save(pad(softnormal(load(m/'texture_urls_0_normal.png'),.35),cov),T/'m416_normal_1k.png');save(np.stack([pad(spec,cov),pad(rough,cov),np.zeros_like(spec)],-1),T/'m416_metal_rough_1k.png');classes[~cov]=0;Image.fromarray(classes).save(T/'m416_material_classes.png')
R.write_mask([ndimage.gaussian_filter(pad(cloth.astype(float),cov),.5)],T/'m416_region_mask.png',size=N)
indices=np.concatenate([np.asarray(Image.open(repo/'assets_dev/engine/sprites'/f'm416Sa{i}.bmp')).ravel() for i in range(5)])
pal0=np.frombuffer((repo/'assets_dev/worlds/mm8/textures/pal417.act').read_bytes()[:768],np.uint8).reshape(256,3)/255
teal=(pal0[:,1]>1.2*pal0[:,0])&(pal0[:,1]>1.08*pal0[:,2])&(pal0[:,1]>.05);ix=indices[teal[indices]];assert len(ix)>100
ix=ix[np.argsort(R.luminance(pal0[ix]))];L=R.luminance(b[cloth]);lo,hi=np.percentile(L,[2,98]);order=np.sort(L);ramps={}
for tier,palnum in zip(['m416_a','m416_b','m416_c'],[417,418,419]):
 pal=np.frombuffer((repo/f'assets_dev/worlds/mm8/textures/pal{palnum}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255;cols=[]
 for i in range(16):
  q=np.searchsorted(order,lo+(hi-lo)*i/15)/len(L);k=ix[min(len(ix)-1,round(q*(len(ix)-1)))];cols.append(R.srgb_to_linear(np.clip(pal[k]*1.35,0,1)).tolist())
 ramps[tier]=[{'range':[float(lo),float(hi)],'colors':cols}]
m=P/'meshy/head_retexture_v1';hb=load(m/'texture_urls_0_base_color.png');hr=np.load(P/'work/uvraster_HeadUV.npz');hc=hr['piece']>=0;eyes=np.isin(hr['piece'],[16,17]);uv=np.load(P/'work/head_body_uv.npy');src=load(P/'meshy/body_retexture_v1/texture_urls_0_base_color.png');fallback=src[np.clip(((1-uv[...,1])*N).astype(int),0,N-1),np.clip((uv[...,0]*N).astype(int),0,N-1)];hp=hr['pos']
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
face=smooth((.066-np.abs(hp[...,0]+.007))/.018)*smooth((-.025-hp[...,1])/.025)*smooth((hp[...,2]-1.59)/.035)*smooth((1.722-hp[...,2])/.012);face[eyes]=1
hb=hb*face[...,None]+fallback*(1-face[...,None]);hb*=(.8+.2*np.maximum(load(P/'work/ao_HeadUV.png','L'),.45))[...,None]
save(pad(hb,hc),T/'m416_head_basecolor_1k.png');save(pad(softnormal(load(m/'texture_urls_0_normal.png'),.45),hc),T/'m416_head_normal_1k.png');save(np.stack([pad(np.where(eyes,.75,.28),hc),pad(np.where(eyes,.25,.74),hc),np.zeros_like(hb[...,0])],-1),T/'m416_head_metal_rough_1k.png');Image.fromarray(np.where(hc,np.where(eyes,6,1),0).astype('uint8')).save(T/'m416_head_material_classes.png');Image.new('RGBA',(N,N),(0,0,0,0)).save(T/'m416_head_region_mask.png')
config={'variants':list(ramps),'materials':[{'base':'PirateCrossbowwoman_A','prefix':'PirateCrossbowwoman','mask':'m416_region_mask.png','ramps':ramps},{'base':'PirateCrossbowwomanHead_A','prefix':'PirateCrossbowwomanHead','mask':'m416_head_region_mask.png','ramps':ramps}]};(T/'m416_ramps.json').write_text(json.dumps(config,indent=2))
for name in ['crossbow','quiver']:
 m=P/f'meshy/{name}_v1';base=load(m/'texture_urls_0_base_color.png',n=512);normal=load(m/'texture_urls_0_normal.png',n=512);met=load(m/'texture_urls_0_metallic.png','L',512)>.35;rough=load(m/'texture_urls_0_roughness.png','L',512);rough=np.clip(rough,.38,.9);rough=np.where(met,rough,np.maximum(rough,.68));spec=np.where(met,.75,.25)
 save(base,T/f'm416_{name}_basecolor.png');save(normal,T/f'm416_{name}_normal.png');save(np.stack([spec,rough,np.zeros_like(spec)],-1),T/f'm416_{name}_metal_rough.png')
report={'covered':int(cov.sum()),'cloth':int(cloth.sum()),'head':int(hc.sum()),'eyes':int(eyes.sum()),'native_teal_samples':len(ix)};assert report['cloth']>5000 and report['eyes']>0;(P/'work/texture_classes.json').write_text(json.dumps(report,indent=2));print(report)
