"""Compose the source PBR maps and six native coat/hair palette variants."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as nd
P=Path(__file__).resolve().parents[1];T=P/'textures';T.mkdir(exist_ok=True);N=1024
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
SURFACE={'skin':(.3,.6),'cloth':(.12,.85),'leather':(.35,.68),'gold':(.9,.38),'hair':(.15,.76),'wood':(.25,.7)}
def load(p,mode='RGB',n=N):return np.asarray(Image.open(p).convert(mode).resize((n,n),Image.Resampling.LANCZOS),float)/255
def save(a,p):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(p)
sets={};report={}
for part,layer,material in [('body','UVMap','PirateMage_A'),('head','HeadUV','PirateMageHead_A')]:
 src=P/'meshy'/f'{part}_retexture_v1';r=np.load(P/'work'/f'uvraster_{layer}.npz');pc,pos=r['piece'],r['pos'];cov=pc>=0
 base=load(src/'texture_urls_0_base_color.png');normal=load(src/'texture_urls_0_normal.png');rough=load(src/'texture_urls_0_roughness.png','L')
 hsv=np.asarray(Image.fromarray(np.uint8(base*255)).convert('HSV'),float)/255;h,s,v=hsv.transpose(2,0,1)
 green=(h>.19)&(h<.49)&(s>.18);coat=np.isin(pc,[0,13,14])&green
 hair=np.isin(pc,[2,7,8,17,19,20,21,22])|((pc==1)&(pos[:,:,2]>1.455)&(v<.36)&(h>.025)&(h<.12)&(s>.25))
 skin=np.isin(pc,[1,3,5])&~hair
 gold=(h>.08)&(h<.18)&(s>.35)&(v>.27)&~skin&~hair&~np.isin(pc,[12,6])
 gold|=pc==18
 cloth=np.isin(pc,[0,4,9,10,11,13,14])&~gold
 leather=(pc==6)&(pos[:,:,2]<.15)&~gold;stocking=(pc==6)&(pos[:,:,2]>=.15)&(pos[:,:,2]<.30);skin|=(pc==6)&(pos[:,:,2]>=.30)
 cloth|=stocking
 graded=base.copy();lum=base@np.array([.2126,.7152,.0722])
 neck=(pc==1)&(pos[:,:,2]<1.455)
 # The head reference projects collar colour onto bare neck and white shirt onto thin beard pieces.
 graded[neck]=np.array([174,119,80])/255*np.clip(lum[neck,None]/.45,.85,1.12)
 beard=np.isin(pc,[7,8,17,19,20,21,22]);detail=np.clip(lum/np.maximum(nd.gaussian_filter(lum,5),.02),.65,1.45)
 graded[beard]=np.array([75,48,30])/255*detail[beard,None]
 cls={'cloth':cloth,'skin':skin,'hair':hair,'wood':pc==12,'leather':leather,'gold':gold}
 spec=np.full(pc.shape,.25);rgh=np.full(pc.shape,.7)
 for k,m in cls.items():
  if m.any():
   a,b=SURFACE[k];spec[m]=a;rgh[m]=np.clip(b+.15*(rough[m]-np.median(rough[m])),.25,1)
 idx=nd.distance_transform_edt(~cov,return_distances=False,return_indices=True)
 orm=np.stack([spec[tuple(idx)],rgh[tuple(idx)],np.zeros(pc.shape)],-1)
 masks=[nd.gaussian_filter(m.astype(float)[tuple(idx)],.45) for m in [coat,hair]]
 graded=graded[tuple(idx)];normal=normal[tuple(idx)]
 save(graded,T/f'{part}_basecolor.png');save(normal,T/f'{part}_normal.png');save(orm,T/f'{part}_orm.png');R.write_mask(masks,T/f'{part}_region_mask.png')
 sets[part]={'base':graded,'regions':[coat,hair],'material':material};report[part]={'neck_repaired_texels':int(neck.sum()),'coat_texels':int(coat.sum()),'hair_texels':int(hair.sum())}
pals={k:np.frombuffer(Path(f'assets_dev/worlds/mm8/textures/pal{n}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for k,n in [('pirate_mage_a',421),('pirate_mage_b',422),('pirate_mage_c',423),('pirate_seer_a',649),('pirate_seer_b',650),('pirate_seer_c',651)]}
counts=np.zeros(256,int)
for f in Path('assets_dev/engine/sprites').glob('m420Sa*.bmp'):counts+=np.bincount(np.asarray(Image.open(f)).ravel(),minlength=256)
changed=np.any(np.stack([np.max(abs(p-pals['pirate_mage_a']),axis=1)>.01 for p in pals.values()]),axis=0)
ramps={k:[] for k in pals}
for region,(start,end) in enumerate([(158,245),(115,140)]):
 ids=np.arange(start,end+1);ids=ids[changed[ids]];report[['coat_indices','hair_indices'][region]]=ids.tolist();ids=np.repeat(ids,counts[ids]);assert len(ids)>100
 ids=ids[np.argsort(R.luminance(pals['pirate_mage_a'][ids]))]
 lum=np.sort(np.concatenate([R.luminance(x['base'])[x['regions'][region]] for x in sets.values()]));lo,hi=np.percentile(lum,[.5,99.5]);assert hi>lo
 for key,pal in pals.items():
  colors=[];lin=R.srgb_to_linear(pal[ids])
  for t in np.linspace(lo,hi,16):
   q=np.clip(np.searchsorted(lum,t)/len(lum),.01,.99);c=int(q*(len(lin)-1));w=max(4,len(lin)//80)
   colors.append(np.clip(np.median(lin[max(0,c-w):c+w],0)*1.35,0,1).round(6).tolist())
  ramps[key].append({'range':[float(lo),float(hi)],'colors':colors})
cfg={'variants':list(pals),'materials':[]}
for part,v in sets.items():cfg['materials'].append({'base':v['material'],'prefix':v['material'][:-2],'mask':f'{part}_region_mask.png','regions':['coat','hair'],'ramps':ramps})
(T/'pirate_mage_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n')
report.update(ramp_gain_linear=1.35,orm='R specular mask, G roughness, B zero',maps={'body':1024,'head':1024,'staff':1024})
(T/'texture_report.json').write_text(json.dumps(report,indent=2)+'\n')
src=P/'meshy/staff_retexture_v1';save(load(src/'texture_urls_0_base_color.png'),T/'staff_basecolor.png');save(load(src/'texture_urls_0_normal.png'),T/'staff_normal.png')
r=load(src/'texture_urls_0_roughness.png','L');orm=np.zeros((N,N,3));orm[:,:,0]=.9;orm[:,:,1]=np.clip(.38+.15*(r-np.median(r)),.25,.55);save(orm,T/'staff_orm.png')
print('TEXTURES',report)
