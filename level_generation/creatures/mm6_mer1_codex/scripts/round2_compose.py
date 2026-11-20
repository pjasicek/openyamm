"""Compose shared 1K maps and native palette ramps; assert native skin luminance survives grading."""
import sys,json,numpy as np
from pathlib import Path
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
T=P/'textures/round2';T.mkdir(exist_ok=True);N=1024
NAT=P.parent/'mm6_mer1/native_variants';pals={'mer1_a':252,'mer1_b':253,'mer1_c':770}
def load(p,mode='RGB'):
 return np.asarray(Image.open(p).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(a,p):Image.fromarray(np.uint8(np.clip(a*255+.5,0,255))).save(p)
def hsv(a):return np.asarray(Image.fromarray(np.uint8(np.clip(a*255,0,255))).convert('HSV'),float)/255
def enc(a):return np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055)
def stats(a):return {'mean':float(a.mean()),'p90':float(np.percentile(a,90)),'p95':float(np.percentile(a,95))}
na=np.asarray(Image.open(NAT/'mer1sta0_252.png').convert('RGB'),float)/255
h=hsv(na);yy,xx=np.indices(na.shape[:2]);face=(xx>=81)&(xx<=107)&(yy>=14)&(yy<=38)&(h[...,0]>.02)&(h[...,0]<.13)&(h[...,1]>.16)&(h[...,1]<.65)&(h[...,2]>.35)
assert face.sum()>100
native=na[face];native_lum=np.sort(R.luminance(native));report={'native_face_pixels':int(face.sum()),'native_skin_linear_luminance':stats(native_lum),'native_box':[81,14,107,38]}
hands=(((xx>=35)&(xx<=46)&(yy>=124)&(yy<=145))|((xx>=145)&(xx<=155)&(yy>=124)&(yy<=145)))&(h[...,0]>.02)&(h[...,0]<.13)&(h[...,1]>.15)&(h[...,1]<.65)&(h[...,2]>.4)
hands_lum=np.sort(R.luminance(na[hands]));report['native_hand_pixels']=int(hands.sum());report['native_hands_linear_luminance']=stats(hands_lum)
cols={k:[]for k in pals}
for view in range(5):
 ims={k:np.asarray(Image.open(NAT/f'mer1sta{view}_{pal}.png').convert('RGBA'),float)/255 for k,pal in pals.items()}
 a=ims['mer1_a'];diff=np.maximum(abs(ims['mer1_b'][...,:3]-a[...,:3]).max(-1),abs(ims['mer1_c'][...,:3]-a[...,:3]).max(-1));mask=(diff>8/255)&(a[...,3]>.5)&(a[...,:3].max(-1)>.06)
 for k in pals:cols[k].append(ims[k][...,:3][mask])
cols={k:np.concatenate(v)for k,v in cols.items()};order=np.argsort(R.luminance(cols['mer1_a']));ramps={k:[]for k in pals}
for prefix,job,uv in [('body','body_round2_texture_v2','UVMap'),('head','head_round2_texture_v2','HeadUV')]:
 src=P/'meshy'/job;base=load(src/'texture_urls_0_base_color.png');normal=load(src/'texture_urls_0_normal.png');normal[...,1]=1-normal[...,1];rough=load(src/'texture_urls_0_roughness.png','L');r=np.load(P/'work/round2'/f'uvraster_{uv}.npz');piece,pos=r['piece'],r['pos'];cov=piece>=0;h=hsv(base);hue=h[...,0]*360;sat=h[...,1];val=h[...,2]
 skin=cov&((np.isin(piece,[3,4]))if prefix=='body'else((piece==0)&(hue>7)&(hue<48)&(sat>.12)&(sat<.72)&(val>.24)))
 leather=cov&np.isin(piece,[6,7,10,12,13,16]) if prefix=='body'else cov&(piece==0)&~skin
 silver=cov&(piece==17)if prefix=='body'else np.zeros_like(cov)
 cloth=cov&~skin&~leather&~silver
 classes=np.zeros((N,N),np.uint8);classes[skin]=1;classes[leather]=8 if prefix=='body'else 2;classes[silver]=9;classes[cloth]=11
 graded=base.copy()
 if prefix=='body':
  skinTone=np.median(native,axis=0); skinTone/=max(float(R.luminance(skinTone)),1e-6)**(1/2.2)
  smooth=ndimage.gaussian_filter(base,(2,2,0)); fine=np.clip(base-smooth,-.018,.018)
  graded[skin]=np.clip(skinTone*.79+fine[skin]*.5,0,1)
 if prefix=='body':
  pass # Fresh Meshy base already contains broad occlusion; old AO belongs to the rejected body.
 # Native skin is pale. Rank-map linear luminance, preserving the source chroma and its high-frequency detail.
 old=R.luminance(graded)[skin];rank=np.argsort(np.argsort(old));targetNative=hands_lum if prefix=='body'else native_lum;target=(np.full(len(rank),.746)+(old-np.mean(old))*.4) if prefix=='body' else np.quantile(targetNative,(rank+.5)/len(rank))*1.025;lin=R.srgb_to_linear(graded[skin]);lin*=np.maximum(target,1e-6)[:,None]/np.maximum(old[:,None],1e-6);gamut=np.minimum(1,(1-target)/np.maximum(lin.max(-1)-target,1e-6));lin=target[:,None]+(lin-target[:,None])*gamut[:,None];graded[skin]=enc(np.clip(lin,0,1));normal[skin]=[.5,.5,1.] if prefix=='body' else normal[skin];final=R.luminance(graded)[skin];report[prefix+'_skin']={'pixels':int(skin.sum()),'before':stats(old),'after':stats(final)}
 assert all(report[prefix+'_skin']['after'][k]>=stats(targetNative)[k] for k in ['mean','p90','p95']),report
 if prefix=='body':
  region=np.isin(piece,[1,2,8,9])&(hue>65)&(hue<185)&(sat>.14);assert region.sum()>150000
  lum=np.sort(R.luminance(graded)[region]);lo,hi=np.percentile(lum,[2,98])
  for k in pals:
   native_lin=R.srgb_to_linear(cols[k])[order];stops=[]
   for i in range(16):
    q=np.clip(np.searchsorted(lum,lo+i/15*(hi-lo))/len(lum),.02,.98);c=int(q*(len(order)-1));w=max(4,len(order)//60);stops.append(np.median(native_lin[max(0,c-w):c+w],0).tolist())
   ramps[k]=[{'range':[float(lo),float(hi)],'colors':stops}]
  ix=ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True);weight=region[tuple(ix)].astype(float);R.write_mask([weight],T/'mer1_region_mask.png');report['cloth_region']={'texels':int(region.sum()),'native_pixels':len(order),'gain':1.0}
  for k in pals:
   rp=ramps[k][0];lumall=R.luminance(graded);x=np.clip((lumall-lo)/(hi-lo),0,1)*15;v=np.array(rp['colors']);i=np.minimum(x.astype(int),14);f=x-i;mapped=enc(v[i]*(1-f[...,None])+v[i+1]*f[...,None]);preview=graded*(1-weight[...,None])+mapped*weight[...,None];save(preview,T/f'{k}_preview.png')
 spec=np.zeros((N,N));rgh=np.ones((N,N))*.9
 for m,sp,rg in [(skin,.3,.65),(leather,.2,.8),(silver,.6,.45),(cloth,.05,.9)]:
  spec[m]=sp;rgh[m]=np.clip(rg+.25*(rough[m]-np.median(rough[m])),.3,1)if m.any()else rg
 ix=ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True)
 for arr,name in [(graded,'basecolor'),(normal,'normal'),(np.stack([spec,rgh,np.zeros_like(spec)],-1),'metal_rough')]:save(arr[tuple(ix)],T/f'mer1_{prefix}_{name}_1k.png')
 Image.fromarray(classes[tuple(ix)]).save(T/f'mer1_{prefix}_material_classes.png')
(T/'mer1_ramps.json').write_text(json.dumps({'variants':list(pals),'materials':[{'base':'Merchant_A','prefix':'Merchant','mask':'mer1_region_mask.png','regions':['tunic'],'palettes':pals,'ramps':ramps}]},indent=2));(P/'review/round2/texture_report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
