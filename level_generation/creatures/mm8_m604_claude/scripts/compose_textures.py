"""Native cloth tiers, material response and short-range AO; original Meshy maps stay untouched."""
from pathlib import Path
import json,sys,numpy as np
from PIL import Image
from scipy import ndimage
p=Path(__file__).resolve().parents[1];repo=p.parents[2];sys.path.insert(0,str(p.parent/'claude_shared'));import region_variants as R
T=p/'textures';N=1024
load=lambda path,mode='RGB':np.asarray(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
lin=R.srgb_to_linear
lum=R.luminance
def save(a,path):Image.fromarray(np.round(np.clip(a,0,1)*255).astype('uint8')).save(path)
def pad(a,cov):
 _,inds=ndimage.distance_transform_edt(~cov,return_indices=True);out=a[tuple(inds)];out[cov]=a[cov];return out
def hsv(a):return np.asarray(Image.fromarray((a*255).astype('uint8')).convert('HSV'),float)/255
m=p/'meshy/body_retexture_v1';base=load(m/'texture_urls_0_base_color.png');normal=load(m/'texture_urls_0_normal.png')
r=np.load(p/'work/uvraster_UVMap.npz');g,pos,nrm=r['garment'],r['pos'],r['normal'];cov=g>=0
h0,s0,v0=np.moveaxis(hsv(base),-1,0)
cloth=cov&(np.isin(g,[1,5,6])|((g==2)&(h0>.12)&(h0<.44)&(s0>.25)&(v0>.12)));lining=cloth&(((g==1)&(nrm[...,2]<-.25))|((g==5)&(nrm[...,1]>.25))|((g==6)&(nrm[...,1]<-.25)))
outer=cloth&~lining
# Meshy painted both sides green; native mantle and narrow panels have a dark red lining.
detail=np.clip(lum(base)/np.maximum(ndimage.gaussian_filter(lum(base),5),.005),.5,1.4)
base[lining]=np.clip(np.array([.30,.042,.06])*detail[lining,None],0,1)
base*= (1-.25+.25*np.maximum(load(p/'work/ao_UVMap.png','L'),.4))[...,None]
h,s,v=np.moveaxis(hsv(base),-1,0)
gold=cov&np.isin(g,[7,8,10,11])&~((g==11)&((h<.055)|(h>.92))&(s>.45))
cuirass=cov&(g==0)&(pos[...,2]>.98)&(pos[...,2]<1.49)&(np.abs(pos[...,0])<.22)
classes=np.ones((N,N),np.uint8);spec=np.full((N,N),.28);rough=np.full((N,N),.76)
for mask,c,sp,ro in [(cuirass,9,.7,.50),((g==2)&~cloth,8,.25,.78),(cloth,8,.15,.90),(gold,9,1,.34),((g==11)&~gold,8,.25,.70)]:
 classes[mask]=c;spec[mask]=sp;rough[mask]=ro
save(pad(base,cov),T/'m604_basecolor_1k.png');save(pad(normal,cov),T/'m604_normal_1k.png')
save(np.stack([pad(spec,cov),pad(rough,cov),np.zeros_like(spec)],-1),T/'m604_metal_rough_1k.png')
classes[~cov]=0;Image.fromarray(classes).save(T/'m604_material_classes.png')
R.write_mask([ndimage.gaussian_filter(pad(x.astype(float),cov),.6) for x in (outer,lining)],T/'m604_region_mask.png',size=N)
# Original palette-index frequencies keep rare bright colours from dominating the ramp.
indices=np.concatenate([np.array(Image.open(repo/'assets_dev/engine/sprites'/f'm604Sa{i}.bmp')).ravel() for i in range(5)])
ramps={k:[] for k in ['m604_a','m604_b','m604_c']}
for mask,loi,hii in [(outer,7,64),(lining,64,72)]:
 L=lum(base[mask]);lo,hi=np.percentile(L,[2,98]);sorted_l=np.sort(L);ix=indices[(indices>=loi)&(indices<hii)];assert len(ix)>100 and hi>lo
 pal0=np.frombuffer((repo/'assets_dev/worlds/mm8/textures/Pal605.act').read_bytes()[:768],np.uint8).reshape(256,3)/255
 ix=ix[np.argsort(lum(pal0[ix]))]
 for tier,palnum in zip(ramps,[605,606,607]):
  pal=np.frombuffer((repo/f'assets_dev/worlds/mm8/textures/Pal{palnum}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255
  cols=[]
  for i in range(16):
   q=np.searchsorted(sorted_l,lo+(hi-lo)*i/15)/len(L);idx=ix[min(len(ix)-1,round(q*(len(ix)-1)))]
   cols.append(lin(np.clip(pal[idx]*1.35,0,1)).tolist())
  ramps[tier].append({'range':[float(lo),float(hi)],'colors':cols})
# The face stays shared across tiers and uses its own 1K set.
m=p/'meshy/head_retexture_v1';hb=load(m/'texture_urls_0_base_color.png');hr=np.load(p/'work/uvraster_HeadUV.npz');hc=hr['garment']>=0
hb*= (1-.2+.2*np.maximum(load(p/'work/ao_HeadUV.png','L'),.45))[...,None]
hh,hs,hv=np.moveaxis(hsv(hb),-1,0);hp=hr['pos'];eyes=hc&(np.abs(hp[...,0])>.019)&(np.abs(hp[...,0])<.052)&(hp[...,1]<-.09)&(hp[...,2]>1.685)&(hp[...,2]<1.714)&(hv>.40)&(hs<.23)
hspec=np.where(eyes,.85,.32);hrough=np.where(eyes,.23,.72)
save(pad(hb,hc),T/'m604_head_basecolor_1k.png');save(pad(load(m/'texture_urls_0_normal.png'),hc),T/'m604_head_normal_1k.png')
save(np.stack([pad(hspec,hc),pad(hrough,hc),np.zeros_like(hspec)],-1),T/'m604_head_metal_rough_1k.png')
Image.fromarray(np.where(hc,np.where(eyes,6,1),0).astype('uint8')).save(T/'m604_head_material_classes.png')
Image.new('RGBA',(N,N),(0,0,0,0)).save(T/'m604_head_region_mask.png')
config={'variants':list(ramps),'materials':[{'base':'EtherKnight_A','prefix':'EtherKnight','mask':'m604_region_mask.png','ramps':ramps},{'base':'EtherKnightHead_A','prefix':'EtherKnightHead','mask':'m604_head_region_mask.png','ramps':ramps}]}
(T/'m604_ramps.json').write_text(json.dumps(config,indent=2))
report={'body_covered':int(cov.sum()),'cloth':int(outer.sum()),'lining':int(lining.sum()),'gold':int(gold.sum()),'head_covered':int(hc.sum()),'eye':int(eyes.sum())}
assert report['cloth']>10000 and report['eye']>0
(p/'work/texture_classes.json').write_text(json.dumps(report,indent=2));print(report)

# Original charts keep 75% of the width; the plain lining uses the remaining strip.
inside=np.isin(g,[1,5,6])&cov
liningbase=np.clip(np.array([.30,.042,.06])*detail[...,None],0,1)
for stem,mode,inside_map in [('basecolor_1k','RGB',liningbase),('normal_1k','RGB',np.broadcast_to(np.array([128,128,255])/255,base.shape)),('metal_rough_1k','RGB',np.broadcast_to(np.array([.15,.90,0]),base.shape)),('material_classes','L',np.full((N,N),8/255)),('region_mask','RGBA',np.stack([np.zeros((N,N)),pad(inside.astype(float),cov),np.zeros((N,N)),np.zeros((N,N))],-1))]:
 path=T/('m604_'+stem+'.png');im=Image.open(path).convert(mode);right=Image.fromarray(np.round(np.clip(inside_map,0,1)*255).astype('uint8')).convert(mode)
 atlas=Image.new(mode,(N,N));resize=lambda image,size:Image.merge('RGBA',[c.resize(size,Image.Resampling.LANCZOS) for c in image.split()]) if image.mode=='RGBA' else image.resize(size,Image.Resampling.LANCZOS)
 atlas.paste(resize(im,(768,N)),(0,0));atlas.paste(resize(right,(256,N)),(768,0));atlas.save(path)
L=lum(liningbase[inside]);lo,hi=np.percentile(L,[2,98]);order=np.sort(L);ix=indices[(indices>=64)&(indices<72)];ix=ix[np.argsort(lum(pal0[ix]))]
for tier,palnum in zip(ramps,[605,606,607]):
 pal=np.frombuffer((repo/f'assets_dev/worlds/mm8/textures/Pal{palnum}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255
 cols=[]
 for i in range(16):
  q=np.searchsorted(order,lo+(hi-lo)*i/15)/len(L);idx=ix[min(len(ix)-1,round(q*(len(ix)-1)))];cols.append(lin(np.clip(pal[idx]*1.35,0,1)).tolist())
 ramps[tier][1]={'range':[float(lo),float(hi)],'colors':cols}
(T/'m604_ramps.json').write_text(json.dumps(config,indent=2));report['lining_after_shell']=int(inside.sum()/4)
(p/'work/texture_classes.json').write_text(json.dumps(report,indent=2));print('ATLAS',report)
