"""One native-palette texture set for all Salamander tiers, with material-specific PBR."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';N=1024;W=np.array([.2126,.7152,.0722])
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
from material_classes_to_orm import TABLE
sys.path.insert(0,str(P.parents[2]/'tools'));from normal_map_convention import measure
palettes={'m568_a':569,'m568_b':570,'m568_c':571};pals={k:np.frombuffer((P.parents[2]/f'assets_dev/worlds/mm8/textures/Pal{v}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for k,v in palettes.items()}
def load(path,mode='RGB',size=N):return np.asarray(Image.open(path).convert(mode).resize((size,size),Image.Resampling.LANCZOS),float)/255
def save(a,path):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path,optimize=True)
def pad(a,cov):return a[tuple(ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True))]
def hsv(a):return np.moveaxis(np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('HSV'),float)/255,-1,0)
sets={}
for label,job in [('body','body_retexture_v2'),('head','head_retexture_v1')]:
 data=np.load(P/'work'/f'uvraster_{label}.npz');part,pos=data['piece'],data['pos'];cov=part>=0;img=load(P/'meshy'/job/'texture_urls_0_base_color.png');ao=load(P/'texturing'/f'{label}_ao.png','L');ao=ndimage.gaussian_filter(pad(ao,cov&(ao>.003)),1.0);ao=np.clip(ao,.25,1)
 lum=img@W;smooth=ndimage.gaussian_filter(lum,.7);img*=((smooth+.75*(lum-smooth))/np.maximum(lum,.001))[...,None];img*= (1-.55*(1-ao))[...,None]
 classes=np.zeros((N,N),np.uint8);classes[cov]=1;skin=cov.copy();eyes=np.zeros_like(cov)
 if label=='body':
  claws=cov&(part!=1);classes[claws]=4;skin[claws]=False
 else:
  classes[cov&(part==6)]=3;classes[cov&(part!=1)&(part!=6)]=4
  h,s,v=hsv(img);x,y,z=np.moveaxis(pos,-1,0);eyes=cov&(np.abs(np.abs(x)-.10)<.05)&(z>2.075)&(z<2.17)&(y<-.09)&(y>-.27)&(h>.115)&(h<.21)&(s>.4)&(v>.28);classes[eyes]=6;skin[eyes]=False
 sets[label]={'img':img,'cov':cov,'part':part,'pos':pos,'skin':skin,'classes':classes,'ao':ao,'job':job,'eyes':eyes}
# Match only the exposed neck surfaces across the two texture sets.
seams=[]
for label in ['body','head']:
 d=sets[label];seam=d['cov']&(d['part']==1)&(np.abs(d['pos'][...,2]-1.925)<.025);lum=R.luminance(d['img']);seam&=lum>.02;seams.append(float(np.median(lum[seam])))
gain=float(np.clip(seams[0]/seams[1],.55,1.8));linear=R.srgb_to_linear(sets['head']['img'])*gain;sets['head']['img']=np.clip(np.where(linear<=.0031308,12.92*linear,1.055*np.maximum(linear,0)**(1/2.4)-.055),0,1)
# Use the same body paint at the neck boundary, blending into the dedicated head detail.
hd=sets['head']; hmap=np.load(P/'work/uvraster_head.npz'); uv=hmap['body_uv']; source=load(P/'meshy/body_retexture_v2/texture_urls_0_base_color.png'); lum=source@W; smooth=ndimage.gaussian_filter(lum,.7);source*=((smooth+.75*(lum-smooth))/np.maximum(lum,.001))[...,None]
coords=[(1-uv[...,1])*N-.5,uv[...,0]*N-.5];sample=np.stack([ndimage.map_coordinates(source[...,i],coords,order=1,mode='nearest') for i in range(3)],-1);sample*=(1-.55*(1-hd['ao']))[...,None]
blend=np.clip((hd['pos'][...,2]-1.95)/.09,0,1);blend=blend*blend*(3-2*blend);blend=np.where(hd['part']==1,blend,1)
hd['img']=sample*(1-blend[...,None])+hd['img']*blend[...,None]
counts=np.zeros(256,int)
for f in (P.parents[2]/'assets_dev/engine/sprites').glob('m568*'):
 if f.suffix.lower()=='.bmp':counts+=np.bincount(np.asarray(Image.open(f)).ravel(),minlength=256)
r,g,b=pals['m568_a'].T;skinidx=np.where((r>g*1.12)&(g>b*1.12)&(r>60/255)&(counts>0))[0];wrapidx=np.where((g>r*1.5)&(g>b*1.4)&(g>.25)&(counts>0))[0]
assert len(skinidx)>10 and len(wrapidx)>2
skinlum=np.concatenate([R.luminance(d['img'])[d['skin']] for d in sets.values()]);lo,hi=np.percentile(skinlum,[.5,99.5]);mid=float(np.median(skinlum[skinlum>.025]));ramps={};report={}
for key,pal in pals.items():
 sample=np.repeat(R.srgb_to_linear(pal[skinidx]),counts[skinidx],axis=0);native=np.median(sample,axis=0)*1.6;chroma=native/max(float(native@W),1e-8);factor=float(native@W)/mid
 ramps[key]=[{'range':[float(lo),float(hi)],'colors':[np.clip(chroma*(lo+j/15*(hi-lo))*factor,0,1).tolist() for j in range(16)]}]
for label,d in sets.items():
 covered=d['cov'];classes=d['classes'];normal=load(P/'meshy'/d['job']/'texture_urls_0_normal.png');rough=load(P/'meshy'/d['job']/'texture_urls_0_roughness.png','L');assert measure(np.uint8(normal*255+.5))<-.15;normal[...,1]=1-normal[...,1];v=normal*2-1;v/=np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),.001);normal=(v+1)/2
 spec=np.zeros((N,N));rg=np.ones((N,N));metal=np.zeros((N,N));detail=np.clip(rough-ndimage.gaussian_filter(rough,4),-.12,.12)
 for cls in np.unique(classes[covered]):
  m=classes==cls;metallic,base,band,sp=TABLE[int(cls)];spec[m]=sp*d['ao'][m];rg[m]=np.clip(base+detail[m],*band);metal[m]=metallic
 save(pad(d['img'],covered),T/f'm568_{label}_basecolor_1k.png');save(pad(normal,covered),T/f'm568_{label}_normal_1k.png');save(pad(np.stack([spec,rg,metal],-1),covered),T/f'm568_{label}_metal_rough_1k.png');mask=ndimage.gaussian_filter(pad(d['skin'].astype(float),covered),.6);R.write_mask([mask],T/f'm568_{label}_region_mask.png',size=N);Image.fromarray(classes).save(T/f'm568_{label}_material_classes.png')
 overlay=d['img']*.3;overlay[d['skin']]=(.2,.8,.25);overlay[d['eyes']]=(0,.7,1);save(overlay,P/'review'/f'{label}_regions.png');report[label]={'covered':int(covered.sum()),'skin':int(d['skin'].sum()),'eye':int(d['eyes'].sum()),'classes':{int(k):int((classes==k).sum()) for k in np.unique(classes)},'normal_y_flipped':True,'ao_strength':.55}
# Compact atlas for the locally modelled black shaft, steel fork and coloured cloth grips.
n=256;y,x=np.mgrid[:n,:n];u=x/(n-1);v=y/(n-1);col=np.zeros((n,n,3));cls=np.where(u<1/3,10,np.where(u<2/3,9,8)).astype(np.uint8);grain=.92+.08*np.sin(53*u+8*np.sin(4*v));steel=.76+ .05*np.sin(34*v+3*u);cloth=.85+.15*np.sin(2*np.pi*(v*22+u*3))
col[cls==10]=np.stack([.07*grain,.055*grain,.04*grain],-1)[cls==10];col[cls==9]=np.stack([steel*.98,steel,steel*1.01],-1)[cls==9];col[cls==8]=np.stack([.13*cloth,.65*cloth,.16*cloth],-1)[cls==8]
spec=np.zeros((n,n));rough=np.zeros((n,n));metal=np.zeros((n,n))
for k in [8,9,10]:
 m=cls==k;mt,rr,band,sp=TABLE[k];spec[m]=sp;rough[m]=rr;metal[m]=mt
save(col,T/'m568_weapon_basecolor_1k.png');save(np.stack([spec,rough,metal],-1),T/'m568_weapon_metal_rough_1k.png');save(np.broadcast_to([.5,.5,1.],(n,n,3)),T/'m568_weapon_normal_1k.png');Image.fromarray(cls).save(T/'m568_weapon_material_classes.png');R.write_mask([(cls==8).astype(float)],T/'m568_weapon_region_mask.png',size=n)
wl=R.luminance(col)[cls==8];wlo,whi=float(wl.min()),float(wl.max());wr={}
for key,pal in pals.items():
 native=np.median(R.srgb_to_linear(pal[wrapidx]),axis=0);native*=1.35;chroma=native/max(float(native@W),1e-8);factor=float(native@W)/float(np.median(wl));wr[key]=[{'range':[wlo,whi],'colors':[np.clip(chroma*(wlo+j/15*(whi-wlo))*factor,0,1).tolist() for j in range(16)]}]
cfg={'variants':list(pals),'palettes':palettes,'head_seam_linear_gain':gain,'native_skin_palette_indices':skinidx.tolist(),'native_wrap_palette_indices':wrapidx.tolist(),'report':report,'materials':[{'base':name+'_A','prefix':name,'mask':f'm568_{label}_region_mask.png','regions':['scales'],'ramps':ramps} for label,name in [('body','Salamander'),('head','SalamanderHead')]]};cfg['materials'].append({'base':'SalamanderPolearm_A','prefix':'SalamanderPolearm','mask':'m568_weapon_region_mask.png','regions':['grips'],'ramps':wr});(T/'m568_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n');print(json.dumps({'report':report,'head_gain':gain,'skin_mid':mid,'native_indices':len(skinidx)},indent=2))
