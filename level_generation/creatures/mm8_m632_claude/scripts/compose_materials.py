"""Compose native-colour material sets and three measured palette-ramp regions."""
import sys,json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared'))
import region_variants as R
from material_classes_to_orm import TABLE
sys.path.insert(0,str(P.parents[2]/'tools'));from normal_map_convention import measure
T=P/'textures';T.mkdir(exist_ok=True)
SKIN=np.array([125,68,41])/255
PAL={'m632_a':633,'m632_b':634,'m632_c':635}
def load(path,n,mode='RGB'):
 return np.asarray(Image.open(path).convert(mode).resize((n,n),Image.Resampling.LANCZOS),float)/255
def save(a,path):Image.fromarray(np.clip(a*255+.5,0,255).astype(np.uint8)).save(path)
def hsv(a):
 return np.asarray(Image.fromarray(np.clip(a*255,0,255).astype(np.uint8)).convert('HSV'),float)/255
def pad(a,cov):
 idx=ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True);return a[tuple(idx)]
def srgb(x):return np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055)
def skin_grade(a,m,albedo=SKIN,mix=.85):
 l=R.luminance(a);den=ndimage.gaussian_filter(m.astype(float),6);mean=ndimage.gaussian_filter(l*m,6)/np.maximum(den,1e-5)
 detail=np.clip(l/np.maximum(mean,1e-5),.5,1.5);b=a.copy();b[m]=(1-mix)*a[m]+mix*srgb(R.srgb_to_linear(albedo)*detail[m,None]);return b
sets={}
for part,n in [('body',1024),('head',1024),('crossbow',512)]:
 job=P/'meshy'/f'{part}_texture_v1';b=load(job/'texture_urls_0_base_color.png',n);normal=load(job/'texture_urls_0_normal.png',n);rough=load(job/'texture_urls_0_roughness.png',n,'L')
 rz=np.load(P/'work'/('uvraster_Crossbow_UVMap.npz' if part=='crossbow' else 'uvraster_Body_'+('HeadUV' if part=='head' else 'UVMap')+'.npz'))
 piece,pos=rz['piece'],rz['pos'];cov=piece>=0;h,s,v=np.moveaxis(hsv(b),-1,0);h*=360
 cls=np.zeros((n,n),np.uint8);cls[cov]=11;regions=[np.zeros((n,n),bool) for _ in range(3)]
 if part=='crossbow':
  cls[cov&(piece==0)]=10;cls[cov&(piece==1)]=9;cls[cov&(piece==2)]=8
 else:
  hair=cov&np.isin(piece,[1,2,3,6,10,13]);eyes=cov&np.isin(piece,[24,25])
  metal=cov&np.isin(piece,[9,11,15,16,19,20,21,22,23,28,29,30,33,*range(36,70)])
  cloth=cov&np.isin(piece,[4,17,18,26,27,31,32]);boots=cov&np.isin(piece,[12,14])
  skin=cov&np.isin(piece,[0,5,7,8,34,35])
  bracer=skin&(np.abs(pos[...,0])>.33)&(pos[...,2]>.60)&(pos[...,2]<.84)
  painted=bracer&(h>60)&(h<180)&(s>.25)
  rim=bracer&~painted&(s<.25)
  skin&=~(painted|rim)
  mail=cloth&(s<.28)&(v>.14)
  purple=cloth&~mail
  metal|=mail|rim
  for mask,label in [(skin,1),(hair,2),(eyes,6),(cloth,8),(boots,8),(metal,9),(painted,11)]:cls[mask]=label
  regions=[painted,mail|rim|(cov&np.isin(piece,[28,29])),purple]
  b=skin_grade(b,skin)
  b=skin_grade(b,hair,np.array([195,197,201])/255,.98)
 # Preserve fine roughness without allowing Meshy's broad metallic patches to override ownership.
 orm=np.zeros((n,n,3))
 for label,(met,base,band,spec) in TABLE.items():
  m=cls==label
  if not m.any():continue
  den=ndimage.gaussian_filter(m.astype(float),4);mean=ndimage.gaussian_filter(rough*m,4)/np.maximum(den,1e-5)
  orm[m,0]=spec;orm[m,1]=np.clip(base+np.clip(rough[m]-mean[m],-.12,.12),*band);orm[m,2]=met
 b=pad(b,cov);normal=pad(normal,cov);orm=pad(orm,cov)
 corr=measure(np.clip(normal*255+.5,0,255).astype(np.uint8))
 if corr<=-.15:normal[...,1]=1-normal[...,1]
 print('NORMAL CONVENTION',part,corr,'flipped' if corr<=-.15 else 'kept')
 save(b,T/f'm632_{part}_basecolor.png');save(normal,T/f'm632_{part}_normal.png');save(orm,T/f'm632_{part}_orm.png')
 Image.fromarray(cls).save(T/f'm632_{part}_material_classes.png')
 if part!='crossbow':R.write_mask([ndimage.gaussian_filter(pad(m.astype(float),cov),.7) for m in regions],T/f'm632_{part}_region_mask.png',size=n)
 sets[part]={'base':b,'regions':regions,'coverage':int(cov.sum()),'normal_correlation_before':corr,'normal_flipped':corr<=-.15,'classes':{str(k):int((cls==k).sum()) for k in np.unique(cls)}}
# Use the original indexed BMP pixels to retain each native ramp's relative frequency.
src=json.loads((P/'references_native/inventory.json').read_text());root=P.parents[2]
idx=np.concatenate([np.asarray(Image.open(root/info['path'])).ravel() for key,info in src['sources'].items() if key.startswith(('m632s','m632w','m632a'))])
pal={k:np.frombuffer((root/f'assets_dev/worlds/mm8/textures/Pal{v}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for k,v in PAL.items()}
ramps={k:[] for k in PAL}
for ri,(lo,hi) in enumerate([(94,118),(18,63),(63,83)]):
 native_indices=idx[(idx>=lo)&(idx<hi)];assert len(native_indices)
 lum=np.concatenate([R.luminance(d['base'][d['regions'][ri]]) for part,d in sets.items() if part!='crossbow' and d['regions'][ri].any()]);assert len(lum)
 low,high=np.percentile(lum,[2,98]);sorted_lum=np.sort(lum)
 for variant in PAL:
  cols=pal[variant][native_indices];order=np.argsort(R.luminance(cols));cols=cols[order]
  colors=[]
  for i in range(16):
   q=np.searchsorted(sorted_lum,low+(high-low)*i/15)/len(sorted_lum)
   col=cols[min(len(cols)-1,int(q*(len(cols)-1)))];colors.append(R.srgb_to_linear(np.clip(col*1.20,0,1)).round(6).tolist())
  ramps[variant].append({'range':[round(float(low),6),round(float(high),6)],'colors':colors})
config={'variants':list(PAL),'materials':[{'base':name,'prefix':prefix,'mask':f'm632_{part}_region_mask.png','regions':['bracer','mail','cloth'],'palettes':PAL,'ramps':ramps} for part,name,prefix in [('body','Dwarf_A','Dwarf'),('head','DwarfHead_A','DwarfHead')]]}
(T/'m632_ramps.json').write_text(json.dumps(config,indent=1)+'\n')
(T/'composition_report.json').write_text(json.dumps({k:{'coverage':v['coverage'],'normal_correlation_before':v['normal_correlation_before'],'normal_flipped':v['normal_flipped'],'classes':v['classes'],'regions':[int(m.sum()) for m in v['regions']]} for k,v in sets.items()},indent=2))
print('COMPOSED',[(p,d['coverage'],d['classes']) for p,d in sets.items()])
