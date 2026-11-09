"""Shared 1K body/head sets, native skirt ramps and per-texel materials; detailed axe from the selected design."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';N=1024;sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R

def load(path,mode='RGB',size=(N,N)):
 return np.asarray(Image.open(path).convert(mode).resize(size,Image.Resampling.LANCZOS),float)/255

def save(a,name):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(T/name)
def hsv(a):
 v=np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('HSV'),float)/255;return v[:,:,0]*360,v[:,:,1],v[:,:,2]
def pad(a,cov):
 _,ix=ndimage.distance_transform_edt(~cov,return_indices=True);out=a[tuple(ix)];out[cov]=a[cov];return out
sets={};report={}
for part,job,layer in [('body','retexture_v2','UVMap'),('head','head_retexture_v1','HeadUV')]:
 j=P/'meshy'/job;z=np.load(P/f'work/uvraster_{layer}.npz');piece=z['piece'];pos=z['pos'];cov=piece>=0;base=load(j/'texture_urls_0_base_color.png');normal=load(j/'texture_urls_0_normal.png');metal=load(j/'texture_urls_0_metallic.png','L');h,s,v=hsv(base);cl=np.zeros((N,N),np.uint8);cl[cov]=2
 if part=='body':
  cloth=(piece==1)&(pos[:,:,2]<.995);cl[cloth]=8
  x=np.abs(pos[:,:,0]);height=pos[:,:,2];bands=((x>.28)&(((height>.98)&(height<1.24))|((height>1.29)&(height<1.43))))|((x>.065)&(height>.14)&(height<.52))|((height>.945)&(height<1.045))
  gold=((h>20)&(h<65)&(s>.32)&(v>.30));mt=cov&((bands&((metal>.35)|gold))|np.isin(piece,[11,12,13,14,16]));cl[mt]=9;cl[cov&(height<.14)]=8
  cl[cov&(height<.075)&(s<.25)]=4
  gem=cov&((h>165)&(h<255))&((piece==6)|mt);cl[gem]=11
  # Meshy painted a narrow cloth fringe onto adjoining body triangles; it belongs to the native skirt palette too.
  cloth=cov&(((piece==1)&(height<1.085))|((h>165)&(h<260)&(s>.22)&(height>.55)&(height<1.085)&(piece!=6)))&~gold;cl[cloth]=8
 else:
  horn=cov&(piece==0)&(pos[:,:,2]>1.71)&(s<.38);cl[horn]=4;cl[piece==4]=9;cl[np.isin(piece,[8,9])]=6
  nose=cov&(piece==0)&(pos[:,:,1]<-.15)&(pos[:,:,2]<1.66);cl[nose]=1;cl[nose&(v<.10)]=7;cloth=np.zeros_like(cov)
 ao=load(T/f'min1_{part}_ao.png','L');base*=((.72+.28*ao)[:,:,None]);sets[part]={'base':base,'normal':normal,'cl':cl,'cov':cov,'cloth':cloth,'pos':pos,'piece':piece,'ao':ao};assert cov.sum()>20000
# One limited luminance adjustment across the anatomical neck seam; muzzle, horns, eyes and gold remain protected.
b=sets['body'];h=sets['head'];bm=(b['cl']==2)&(b['pos'][:,:,2]>1.42)&(b['pos'][:,:,2]<1.54);hm=(h['cl']==2)&(h['piece']==0)&(h['pos'][:,:,2]<1.58)
bv=np.median(R.luminance(b['base'][bm]));hv=np.median(R.luminance(h['base'][hm]));gain=float(np.clip((bv/max(hv,1e-5))**(1/2.2),.80,1.15));h['base'][h['cl']==2]*=gain;report['neck_gain']=gain
# Only native palette entries that change to gold/red AND are blue cloth in A participate.
PAL=P.parents[2]/'assets_dev/worlds/mm6/textures';pals={f'min1_{k}':np.frombuffer((PAL/f'pal{n}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for k,n in zip('abc',[771,772,773])};pa=pals['min1_a'];changed=np.any(pa!=pals['min1_b'],axis=1)|np.any(pa!=pals['min1_c'],axis=1);indices=np.where(changed&(pa[:,2]>pa[:,0]+.03)&(pa[:,2]>pa[:,1]+.03)&(pa.max(1)>.075))[0];assert len(indices)>=16
lookup={tuple(np.uint8(c*255+.5)):i for i,c in enumerate(pa)};pixels=[]
for view in range(5):
 im=np.asarray(Image.open(P.parent/f'mm6_min1/native/min1wkc{view}.png').convert('RGBA'));pixels.extend(lookup.get(tuple(c),-1) for c in im[im[:,:,3]>128,:3])
sel=np.array(pixels);sel=sel[np.isin(sel,indices)];assert len(sel)>50
cloth=b['cloth'];L=R.luminance(b['base'][cloth]);lo,hi=np.percentile(L,[2,98]);t=np.clip((L-lo)/max(hi-lo,1e-6),0,1);linear=R.srgb_to_linear(b['base'][cloth]);linear*=((.02+.28*t)/np.maximum(L,1e-5))[:,None];b['base'][cloth]=np.where(linear<=.0031308,linear*12.92,1.055*np.maximum(linear,0)**(1/2.4)-.055)
ramps={}
for tier,pal in pals.items():
 colors=pal[sel];colors=colors[np.argsort(R.luminance(colors))];stops=colors[np.minimum(len(colors)-1,np.round(np.linspace(.03,.97,16)*(len(colors)-1)).astype(int))];stops=np.clip(stops*1.25,0,1);ramps[tier]=[{'range':[.02,.30],'colors':R.srgb_to_linear(stops).round(6).tolist()}]
report['palette_indices']=indices.tolist();report['native_cloth_pixels']=len(sel);report['native_palette_ids']=[771,772,773]
materials=[]
for part,z in sets.items():
 cl=z['cl'];cov=z['cov'];base=pad(z['base'],cov);normal=pad(z['normal'],cov);vec=normal*2-1;vec/=np.maximum(np.linalg.norm(vec,axis=2,keepdims=True),1e-6);normal=(vec+1)/2
 rough=np.full((N,N),.88);spec=np.zeros((N,N));rough[cl==4]=.64;spec[cl==4]=.10;rough[cl==9]=.64;spec[cl==9]=.30;rough[cl==6]=.35;spec[cl==6]=.50;rough[cl==11]=.55;spec[cl==11]=.20;rough[cl==8]=.85
 save(base,f'min1_{part}_basecolor.png');save(normal,f'min1_{part}_normal.png');save(pad(np.stack([spec,rough,np.zeros_like(spec)],-1),cov),f'min1_{part}_metal_rough.png');Image.fromarray(cl).save(T/f'min1_{part}_material_classes.png');mask=ndimage.gaussian_filter(pad(z['cloth'].astype(float),cov),.6);R.write_mask([mask],T/f'min1_{part}_region_mask.png',size=N)
 report[part]={'class_texels':{str(k):int((cl==k).sum()) for k in np.unique(cl)},'covered_texels':int(cov.sum()),'cloth_texels':int(z['cloth'].sum())}
 materials.append({'base':'Minotaur_A' if part=='body' else 'MinotaurHead_A','prefix':'Minotaur' if part=='body' else 'MinotaurHead','mask':f'min1_{part}_region_mask.png','regions':['skirt'],'palettes':dict(zip(pals,[771,772,773])),'ramps':ramps})
(T/'min1_ramps.json').write_text(json.dumps({'variants':list(pals),'materials':materials},indent=2))
# The detailed design is projected onto the hand-modelled prop; the retained steel mask reconstructs the selected grade.
a=np.asarray(Image.open(P/'references_hd/axe_design.png').convert('RGB'),float)[:,:768]/255;mask=np.asarray(Image.open(T/'axe_steel_grade_mask.png').convert('L'))>127;a[mask]*=.76;save(a,'axe_basecolor.png');ha,sa,va=hsv(a);cl=np.full(a.shape[:2],9,np.uint8);yy,xx=np.indices(cl.shape);shaft=(abs(xx-461)<25)&(yy>285);cl[shaft]=10;cl[shaft&(((yy>400)&(yy<620))|((yy>641)&(yy<840)))]=8;cl[(ha>170)&(ha<250)&(sa>.35)]=11
rough=np.full(cl.shape,.66);rough[cl==8]=.87;rough[cl==10]=.84;spec=np.full(cl.shape,.28);spec[np.isin(cl,[8,10])]=.02;spec[cl==11]=.20;save(np.stack([spec,rough,np.zeros_like(spec)],-1),'axe_metal_rough.png');Image.fromarray(cl).save(T/'axe_material_classes.png');lum=a.mean(2);detail=lum-ndimage.gaussian_filter(lum,2);dy,dx=np.gradient(detail);nm=np.stack([-dx*.6,dy*.6,np.ones_like(dx)],-1);nm/=np.linalg.norm(nm,axis=2,keepdims=True);save((nm+1)/2,'axe_normal.png')
report['runtime_specular']='MR red is the current renderer specular mask, with metallicFactor 0. AO is baked into albedo and also retained separately.';report['axe']='Detailed selected side design, retained steel grade mask, wear-derived shallow normal and material-class roughness.'
(P/'review/texture_composition.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
