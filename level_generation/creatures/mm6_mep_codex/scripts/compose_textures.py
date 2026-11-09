import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as nd
p=Path(__file__).resolve().parents[1];repo=p.parents[2];sys.path.insert(0,str(p.parent/'mm6_peasants'));from mep_materials import weights
sys.path.insert(0,str(p.parent/'claude_shared'));import region_variants as R
T=p/'textures';T.mkdir(exist_ok=True);L=np.array([.2126,.7152,.0722]);lin=R.srgb_to_linear
enc=lambda x:np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055)
def save(a,name,mode=None):Image.fromarray(np.clip(a*255+.5,0,255).astype(np.uint8),mode).save(T/name)
def image(path,size=1024,mode='RGB'):return np.array(Image.open(path).convert(mode).resize((size,size),Image.Resampling.LANCZOS))/255.
pals={k:np.frombuffer((repo/f'assets_dev/worlds/mm6/textures/pal{804+i}.act').read_bytes()[:768],np.uint8).reshape(256,3) for i,k in enumerate('abc')}
# Native-used entries and their frequency provide the luminance distribution, not arbitrary palette ratios.
frequency=np.zeros(256);skin_frequency=np.zeros(256)
for view in range(5):
 im=np.array(Image.open(p.parent/f'mm6_mep/native/mepsta{view}.png'));rgb=im[:,:,:3];ok=im[:,:,3]>0;dist=((rgb[ok,None].astype(float)-pals['a'][None])**2).sum(2);idx=dist.argmin(1);frequency+=np.bincount(idx,minlength=256)
 if view==0:
  y,x=np.indices(ok.shape);skin=ok & (weights(rgb)[:,:,3]>.65) & (((x>=119)&(x<=145)&(y>=20)&(y<=45))|((x>=172)&(x<=186)&(y>=108)&(y<=147))|((x>=95)&(x<=120)&(y>=216)&(y<=249))|((x>=141)&(x<=160)&(y>=216)&(y<=249)))
  si=((rgb[skin,None].astype(float)-pals['a'][None])**2).sum(2).argmin(1);skin_frequency=np.bincount(si,minlength=256)
frequency[0]=0;pw=weights(pals['a'][None])[0];config={'variants':['mep_'+k for k in 'abc'],'materials':[]};stats={}
def target(region,tier,quantiles,skin=False):
 w=(skin_frequency if skin else frequency)*pw[:,region];ids=np.where(w>.01)[0];colors=lin(pals[tier]/255);order=np.argsort(colors[ids]@L);ids=ids[order];cdf=(np.cumsum(w[ids])-.5*w[ids])/w[ids].sum();out=np.column_stack([np.interp(quantiles,cdf,colors[ids,c]) for c in range(3)]);return np.clip(out*1.35,0,1)
def process(kind):
 head=kind=='head';job=p/'meshy'/('head_retexture_v2' if head else 'body_retexture_v1');base=image(job/'texture_urls_0_base_color.png');a=np.load(p/'work'/('uvraster_HeadUV.npz' if head else 'uvraster_UVMap.npz'));piece=a['piece'];pos=a['pos'];occupied=piece>=0;classes=np.full(piece.shape,8,np.uint8);mask=np.zeros((*piece.shape,4));mask[:,:,2]=1
 if head:
  warm=weights((base*255).astype(np.uint8))[:,:,3];skin=(warm>.25)&(piece==0)&(pos[:,:,2]>1.43);hair=(piece==0)&~skin;classes[skin]=1;classes[hair]=2;classes[np.isin(piece,[12,13])]=6;mask[skin]=[0,0,0,1];mask[piece==4]=[0,1,0,0];mask[np.isin(piece,[12,13])]=0
 else:
  mask[piece==1]=[0,1,0,0];mask[np.isin(piece,[7,8])|(piece>=14)]=[1,0,0,0];skin=np.isin(piece,[2,3,5,6]);classes[skin]=1;mask[skin|np.isin(piece,[10,11])]=[0,0,0,1]
 # Fill gutters from the nearest real island before softening; no unrecoloured seams on tiers B/C.
 _,near=nd.distance_transform_edt(~occupied,return_indices=True);mask=mask[near[0],near[1]];classes=classes[near[0],near[1]]
 for c in range(4):mask[:,:,c]=nd.gaussian_filter(mask[:,:,c],.65)
 mask/=np.maximum(mask.sum(2,keepdims=True),1)
 ao=image(p/f'work/ao_{kind}.png',mode='L');linear=lin(base)*(.84+.16*ao[:,:,None])
 if not head:
  for part in [7,8,*range(14,26)]:
   core=(piece==part);v=linear@L;gain=.18/max(.02,float(np.median(v[core])));linear[core]*=gain
  linear=np.clip(linear,0,1)
 base=np.clip(enc(linear),0,1);lum=linear@L;prefix='mep_head' if head else 'mep';material='MepHead_A' if head else 'Mep_A';entry={'base':material,'prefix':'MepHead' if head else 'Mep','mask':prefix+'_region_mask.png','regions':['red accents','cool cloth','pale cloth and hair','skin wood leather'],'palettes':{'mep_a':804,'mep_b':805,'mep_c':806},'ramps':{}}
 regs=[]
 for c in range(4):
  core=(mask[:,:,c]>.9)&occupied;values=np.sort(lum[core]);lo,hi=np.percentile(values,[1,99]) if len(values)>30 else [0,1];hi=max(hi,lo+.001);ts=np.linspace(lo,hi,16);quant=np.searchsorted(values,ts)/max(1,len(values));regs.append((float(lo),float(hi),quant))
 for tier in 'abc':
  entry['ramps']['mep_'+tier]=[{'range':[lo,hi],'colors':target(c,tier,q,skin=(c==3)).tolist()} for c,(lo,hi,q) in enumerate(regs)]
 # Cloth detail keeps its painted contrast. A full histogram stretch would turn weave into pepper noise.
 for tier in 'abc':
  for c,gain,q in [(0,.72,.65),(1,1.15 if head else .60,.90 if head else .50),(2,1.10 if head else .85,.92 if head else .75)]:
   color=target(c,tier,np.array([q]))[0];hue=color/max(.001,color@L);entry['ramps']['mep_'+tier][c]={'range':[0.,1.],'colors':np.clip(np.linspace(0,1,16)[:,None]*hue*gain,0,1).tolist()}
 config['materials'].append(entry);save(base,prefix+'_basecolor_1k.png');save(mask,prefix+'_region_mask.png','RGBA');Image.fromarray(classes,'L').save(T/(prefix+'_material_classes.png'))
 save(image(job/'texture_urls_0_normal.png'),prefix+'_normal_1k.png');rough=image(job/'texture_urls_0_roughness.png',mode='L');rough=np.maximum(rough,np.where(classes==6,.2,np.where(classes==1,.8,.86)));save(np.stack([ao,rough,np.zeros_like(rough)],-1),prefix+'_orm_1k.png')
 # Review-only tier samples also prove numerical skin luminance; runtime remains one shared set.
 for tier in 'abc':
  out=linear.copy()
  for c,reg in enumerate(entry['ramps']['mep_'+tier]):
   lo,hi=reg['range'];xx=np.clip((lum-lo)/(hi-lo),0,1)*15;ii=np.minimum(xx.astype(int),14);t=(xx-ii)[...,None];cc=np.array(reg['colors']);mapped=cc[ii]*(1-t)+cc[ii+1]*t;out=out*(1-mask[:,:,c:c+1])+mapped*mask[:,:,c:c+1]
  m=(classes==1)&occupied;vals=(out@L)[m];native=np.repeat((lin(pals[tier]/255)@L),skin_frequency.astype(int));stats[kind+'_'+tier]={'skin_linear_mean':float(vals.mean()),'skin_linear_p90':float(np.percentile(vals,90)),'native_skin_mean':float(native.mean()),'native_skin_p90':float(np.percentile(native,90)),'albedo_gain':1.35};save(np.clip(enc(out),0,1),prefix+'_review_'+tier+'.png')
 return entry
process('body');process('head')
# Unwrap the two generated staff views around its modelled shaft. Knots and wear remain image-derived.
source=np.array(Image.open(p/'references_hd/staff_design.png').convert('RGB'))/255;H,W=1024,512;yy=np.linspace(38,1491,H);tt=np.linspace(0,1,H);cent=np.interp(tt,[0,.2,.4,.55,.66,.8,1],[299,299,321,328,349,338,342]);radius=np.interp(tt,[0,.2,.45,.65,1],[20,22,15,12,5]);xx=np.linspace(-1,1,W//2);texture=np.empty((H,W,3))
for row in range(H):
 for side in range(2):
  cx=cent[row]+(430 if side else 0);coords=np.clip((cx+radius[row]*xx).round().astype(int),0,source.shape[1]-1);texture[row,side*(W//2):(side+1)*(W//2)]=source[int(yy[row]),coords]
texture=np.asarray(Image.fromarray((texture*255).astype(np.uint8)).resize((1024,1024),Image.Resampling.LANCZOS))/255;save(texture,'mep_staff_basecolor_1k.png');normal=np.zeros((1024,1024,3));normal[:]=[.5,.5,1];grain=lin(texture)@L;gy,gx=np.gradient(nd.gaussian_filter(grain,.6));normal[:,:,0]-=gx*1.8;normal[:,:,1]-=gy*.7;save(normal,'mep_staff_normal_1k.png');save(np.stack([np.ones_like(grain),np.full_like(grain,.9),np.zeros_like(grain)],-1),'mep_staff_orm_1k.png');Image.new('L',(1024,1024),10).save(T/'mep_staff_material_classes.png');mask=np.zeros((1024,1024,4));mask[:,:,3]=1;save(mask,'mep_staff_region_mask.png','RGBA');entry={'base':'MepStaff_A','prefix':'MepStaff','mask':'mep_staff_region_mask.png','ramps':{}}
vals=np.sort((lin(texture)@L).ravel());lo,hi=np.percentile(vals,[1,99]);q=np.searchsorted(vals,np.linspace(lo,hi,16))/len(vals)
for tier in 'abc':entry['ramps']['mep_'+tier]=[{'range':[0.,1.],'colors':np.tile([.5,.5,.5],(16,1)).tolist()} for _ in range(3)]+[{'range':[float(lo),float(hi)],'colors':target(3,tier,q).tolist()}]
config['materials'].append(entry);(T/'mep_ramps.json').write_text(json.dumps(config,indent=2));(p/'review/skin_luminance.json').write_text(json.dumps(stats,indent=2));print('TEXTURES',json.dumps(stats))
