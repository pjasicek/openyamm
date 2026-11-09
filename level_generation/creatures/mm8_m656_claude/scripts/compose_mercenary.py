"""Build shared material maps and native 657/658/659 palette ramps.
MERC_BODY_RETEXTURE picks the body Meshy job (default body_retexture_v1) and MERC_TEXTURES the output folder
(default textures); body retexture v2 writes textures_v2. MERC_CHEEKLESS=1 repaints the head texels that the removed
cheek guards covered (helmet rim and cheek skin, never seen before; 2026-10-19)."""
import json,os,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as nd
P=Path(__file__).resolve().parents[1];T=P/os.environ.get('MERC_TEXTURES','textures');T.mkdir(exist_ok=True);N=1024
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
SURFACE={'skin':(.3,.6),'cloth':(.12,.85),'leather':(.35,.68),'steel':(.8,.42),'gold':(.9,.38),'hair':(.15,.76),'other':(.25,.7)}
def load(p,mode='RGB',size=(N,N)):
 im=Image.open(p).convert(mode)
 if size:im=im.resize(size,Image.Resampling.LANCZOS)
 return np.asarray(im,float)/255

def save(a,p):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(p)
sets={}
for part,layer,material in [('body','UVMap','Mercenary_A'),('head','HeadUV','MercenaryHead_A')]:
 src=P/'meshy'/(os.environ.get('MERC_BODY_RETEXTURE','body_retexture_v1') if part=='body' else 'head_retexture_v1');r=np.load(P/'work'/f'uvraster_{layer}.npz');pc,pos=r['piece'],r['pos'];cov=pc>=0
 base=load(src/'texture_urls_0_base_color.png');normal=load(src/'texture_urls_0_normal.png');rough=load(src/'texture_urls_0_roughness.png','L')
 h=np.asarray(Image.fromarray(np.uint8(base*255)).convert('HSV'),float)/255
 green=(h[:,:,0]>.18)&(h[:,:,0]<.48)&(h[:,:,1]>.2)
 cloth=(pc==4)|((pc==0)&green)
 armour=np.isin(pc,[9,10,14,15,16])|((pc>=43)&(pc<=82))|((pc==0)&~cloth)
 leather=np.isin(pc,[2,3,6,7,11,13])
 skin=(pc==1)&(((h[:,:,0]>.025)&(h[:,:,0]<.13)&(h[:,:,2]>.28)&(h[:,:,1]>.16)&(h[:,:,1]<.77))|(pos[:,:,2]<1.465))
 gold=(h[:,:,0]>.08)&(h[:,:,0]<.18)&(h[:,:,1]>.25)&(h[:,:,2]>.35)&~skin&~cloth
 cls={'skin':skin,'cloth':cloth,'leather':leather|armour|(pc==12)|(pc==25)|(pc==26),'steel':np.isin(pc,[5,84,85]),'gold':gold,'hair':np.isin(pc,[8,19])}
 cls['leather']&=~gold;cls['steel']&=~gold
 cls['other']=cov&~np.any(list(cls.values()),axis=0)
 under=np.zeros(pc.shape,bool)
 if part=='head' and os.environ.get('MERC_CHEEKLESS'):
  # Meshy painted the guards' shadow and edges onto the cheeks and the rim behind them; with the guards gone those
  # texels show. The cheek skin under them takes the flat skin colour, the rim's tan smears the nearby steel.
  guard=cov&(np.abs(pos[:,:,0])>0.045)&(pos[:,:,2]>1.475)&(pos[:,:,1]>-0.06)&(pos[:,:,1]<0.12)
  under=guard&(pc==1)&(pos[:,:,2]<1.585);skin|=under
 graded=base.copy();lum=base@np.array([.2126,.7152,.0722]);w=nd.gaussian_filter(skin.astype(float),12)
 smooth=nd.gaussian_filter(lum*skin,12)/np.maximum(w,1e-6)
 detail=np.clip(lum/np.maximum(smooth,.02),.82,1.18);detail[(pc==1)&(pos[:,:,2]<1.465)]=1
 if under.any():
  fade=np.clip(nd.gaussian_filter(under.astype(float),4)*2,0,1);detail=detail*(1-fade)+fade
 graded[skin]=np.array([169,121,84])/255*detail[skin,None]
 # Keep the nape hair brown; projected green collar colour is not hair colour.
 hair=cls['hair']
 if hair.any():
  detail=np.clip(lum/np.maximum(nd.gaussian_filter(lum,5),.02),.55,1.6)
  graded[hair]=np.array([68,45,29])/255*detail[hair,None]
  assert np.all(graded[hair,0]>graded[hair,1]) and np.all(graded[hair,1]>graded[hair,2])
 if part=='head' and os.environ.get('MERC_CHEEKLESS'):
  rim=guard&(pc==5)&(pos[:,:,2]<1.572)
  tan=rim&(h[:,:,0]>.04)&(h[:,:,0]<.16)&(h[:,:,1]>.25)&(h[:,:,2]>.3)
  steel=(pc==5)&~tan&~((h[:,:,0]>.04)&(h[:,:,0]<.16)&(h[:,:,1]>.25)&(h[:,:,2]>.3))
  fill=nd.gaussian_filter(graded*steel[:,:,None],(6,6,0))/np.maximum(nd.gaussian_filter(steel.astype(float),6),1e-6)[:,:,None]
  grow=nd.binary_dilation(tan,iterations=2)&rim;graded[grow]=fill[grow]
  print(part,'cheek skin repainted',int(under.sum()),'rim smear texels',int(grow.sum()))
 # Meshy projected green trouser colour onto a few overlapping armour plates.
 stray=armour&green;graded[stray]=lum[stray,None]*np.array([1.08,1.0,.73])
 idx=nd.distance_transform_edt(~cov,return_distances=False,return_indices=True)
 spec=np.zeros(pc.shape);rgh=np.zeros(pc.shape)
 for k,m in cls.items():
  if m.any():
   a,b=SURFACE[k];spec[m]=a;rgh[m]=np.clip(b+.15*(rough[m]-np.median(rough[m])),.25,1)
 orm=np.stack([spec[tuple(idx)],rgh[tuple(idx)],np.zeros(pc.shape)],-1)
 masks=[nd.gaussian_filter(m.astype(float)[tuple(idx)],.45) for m in [cloth,armour,leather&~gold]]
 graded=graded[tuple(idx)];normal=normal[tuple(idx)]
 save(graded,T/f'{part}_basecolor.png');save(normal,T/f'{part}_normal.png');save(orm,T/f'{part}_orm.png');R.write_mask(masks,T/f'{part}_region_mask.png')
 sets[part]={'base':graded,'regions':[cloth,armour,leather&~gold],'material':material}
 print(part,'neck repaired',int(((pc==1)&(pos[:,:,2]<1.465)).sum()),'stray green',int(stray.sum()))
pals={k:np.frombuffer(Path(f'assets_dev/worlds/mm8/textures/Pal{n}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for k,n in [('mercenary_a',657),('mercenary_b',658),('mercenary_c',659)]}
counts=np.zeros(256,int)
for f in Path('assets_dev/engine/sprites').glob('m656Sa*.bmp'):counts+=np.bincount(np.asarray(Image.open(f)).ravel(),minlength=256)
ramps={k:[] for k in pals}
for region,(start,end) in enumerate([(1,42),(110,167),(78,109)]):
 ids=np.arange(start,end+1);ids=np.repeat(ids,counts[ids]);assert len(ids)>100
 ids=ids[np.argsort(R.luminance(pals['mercenary_a'][ids]))]
 lum=np.sort(np.concatenate([R.luminance(v['base'])[v['regions'][region]] for v in sets.values()]));lo,hi=np.percentile(lum,[.5,99.5])
 for key,pal in pals.items():
  colors=[];lin=R.srgb_to_linear(pal[ids])
  for t in np.linspace(lo,hi,16):
   q=np.clip(np.searchsorted(lum,t)/len(lum),.01,.99);c=int(q*(len(lin)-1));w=max(4,len(lin)//80)
   colors.append(np.clip(np.median(lin[max(0,c-w):c+w],0)*1.35,0,1).round(6).tolist())
  ramps[key].append({'range':[float(lo),float(hi)],'colors':colors})
cfg={'variants':list(pals),'materials':[]}
for part,v in sets.items():cfg['materials'].append({'base':v['material'],'prefix':v['material'][:-2],'mask':f'{part}_region_mask.png','regions':['cloth','studded_armour','dark_leather'],'ramps':ramps})
(T/'mercenary_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n')
(T/'texture_report.json').write_text(json.dumps({'native_palette_ranges':[[1,42],[110,167],[78,109]],'ramp_gain_linear':1.35,'skin_srgb':[169,121,84],'hair_srgb':[68,45,29],'orm':'R specular mask, G roughness, B zero','maps':{'body':1024,'head':1024}},indent=2)+'\n')
# The same prop sheet supplies two broad faces and a padded edge strip; no tier tint is present on either prop.
D=T/'props';D.mkdir(exist_ok=True);raw=Image.open(P/'references_props/sword_scabbard.png').convert('RGBA')
for name,crop in [('sword',(240,0,480,1536)),('scabbard',(578,0,766,1536))]:
 im=raw.crop(crop).resize((256,1024),Image.Resampling.LANCZOS);a=np.asarray(im);rgb=a[:,:,:3]/255;covered=a[:,:,3]>128
 near=nd.distance_transform_edt(~covered,return_distances=False,return_indices=True);rgb=rgb[tuple(near)]
 save(rgb,D/f'{name}_basecolor.png');normal=np.zeros_like(rgb);normal[:]=[.5,.5,1];save(normal,D/f'{name}_normal.png')
 h=np.asarray(Image.fromarray(np.uint8(rgb*255)).convert('HSV'),float)/255;gold=(h[:,:,0]>.07)&(h[:,:,0]<.17)&(h[:,:,1]>.25)
 orm=np.zeros_like(rgb);orm[:,:,0]=.75 if name=='sword' else .35;orm[:,:,1]=.36 if name=='sword' else .68;orm[gold,0]=.9;orm[gold,1]=.38
 save(orm,D/f'{name}_orm.png')
print('TEXTURES written')
