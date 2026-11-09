"""Shared body/head PBR and four native palette regions: skin, scales, bronze, hair."""
from pathlib import Path
import json,sys,numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';N=1024;sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(P.parents[2]/'tools'));from normal_map_convention import measure
names=['skin','scales','bronze','hair'];data={};report={}
def encode(a):return np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055)
def save(a,p):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(p,optimize=True)
def pad(a,cov):return a[tuple(ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True))]
def load(label,suffix):
 a=np.asarray(Image.open(P/f'meshy/{label}_retexture_v1/texture_urls_0_{suffix}.png').convert('RGB'),float)/255
 if label=='head':return np.asarray(Image.fromarray(np.uint8(a*255+.5)).resize((N,N),Image.Resampling.LANCZOS),float)/255
 uv=np.load(P/'work/uvraster_body.npz')['source_uv'];coords=np.array([(1-uv[...,1])*a.shape[0]-.5,uv[...,0]*a.shape[1]-.5]);return np.stack([ndimage.map_coordinates(a[...,i],coords,order=1,mode='nearest') for i in range(3)],-1)
for label in ['body','head']:
 a=load(label,'base_color');d=np.load(P/f'work/uvraster_{label}.npz');part,pos=d['piece'],d['pos'];cov=part>=0;r,g,b=np.moveaxis(a,-1,0)
 if label=='body':
  metal=cov&np.isin(part,[8,10,11,13]);fluke=(part==5)&(pos[...,1]>.72)&(pos[...,2]>.35);scales=(part==5)&~fluke;hair=np.zeros_like(cov);skin=cov&~metal&~scales
 else:
  metal=cov&((part==7)|((part==0)&(pos[...,2]>1.96)&(r>g*1.38)&(r>b*1.6)))
  hair=cov&~metal&(np.isin(part,[2,4])|((part==0)&(pos[...,2]>1.99)&(r>g*1.06)&(g>b*1.12)));scales=np.zeros_like(cov);skin=cov&~metal&~hair&~np.isin(part,[12,14])
 data[label]={'base':a,'cov':cov,'masks':[skin,scales,metal,hair],'pos':pos,'part':part};report[label]={'covered':int(cov.sum()),'region_pixels':dict(zip(names,[int(m.sum()) for m in data[label]['masks']]))}
# Match the shared skin immediately at the neck, avoiding beard/crown texels.
bd,hd=data['body'],data['head'];bm=bd['masks'][0]&(bd['part']==0)&(bd['pos'][...,2]>1.65);hm=hd['masks'][0]&(hd['part']==0)&(hd['pos'][...,2]<1.80)
gain=float(np.clip(np.median(R.luminance(bd['base'][bm]))/np.median(R.luminance(hd['base'][hm])),.75,1.25));a=R.srgb_to_linear(hd['base']);a[hd['masks'][0]]*=gain;hd['base']=encode(a)
palettes={'wel_a':730,'wel_b':731,'wel_c':732};pals={k:np.frombuffer((P.parents[2]/f'assets_dev/worlds/mm6/textures/pal{v}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for k,v in palettes.items()};lut={tuple(c):i for i,c in enumerate(np.uint8(pals['wel_a']*255+.5))};used=[]
for view in range(5):
 a=np.asarray(Image.open(P.parent/'mm6_wel/native'/f'welsta{view}.png').convert('RGBA'));used.extend(lut.get(tuple(c),0) for c in a[a[...,3]>0,:3])
used=np.array(used);ranges=[np.arange(139,246),np.r_[np.arange(102,139),np.arange(246,252)],np.arange(2,61),np.arange(61,102)];ramps={k:[] for k in pals}
for i,name in enumerate(names):
 samples=np.concatenate([d['base'][d['masks'][i]] for d in data.values()]);lin=R.srgb_to_linear(samples);lum=lin@R.LUMA;lo,hi=np.percentile(lum,[.5,99.5]);assert hi>lo and len(samples)>100
 ids=used[np.isin(used,ranges[i])];nl=R.srgb_to_linear(pals['wel_a'][ids])@R.LUMA;ids=ids[np.argsort(nl)];sortedlum=np.sort(lum);colors={k:[] for k in pals}
 for value in np.linspace(lo,hi,16):
  w=np.exp(-.5*((lum-value)/max((hi-lo)/20,.003))**2);base=np.average(lin,axis=0,weights=w);base*=value/max(float(base@R.LUMA),1e-8);rank=np.searchsorted(sortedlum,value)/len(lum);start=int(max(0,rank-.10)*len(ids));end=max(start+1,int(min(1,rank+.10)*len(ids)));chosen=ids[start:end];native={k:np.median(R.srgb_to_linear(pal[chosen]),axis=0) for k,pal in pals.items()}
  for key in pals:
   color=base if key=='wel_a' else base*(native[key]+.003)/(native['wel_a']+.003);colors[key].append(np.clip(color,0,1).tolist())
 for key in pals:ramps[key].append({'range':[float(lo),float(hi)],'colors':colors[key]})
 report[name]={'native_indices':sorted(set(map(int,ids))),'native_samples':len(ids),'linear_range':[float(lo),float(hi)]}
for label,d in data.items():
 a=d['base'];cov=d['cov'];normal=load(label,'normal');score=measure(np.uint8(np.clip(normal,0,1)*255+.5));assert abs(score)>.15,(label,score)
 if score<0:normal[...,1]=1-normal[...,1]
 normal=normal*2-1;normal/=np.maximum(np.linalg.norm(normal,axis=-1,keepdims=True),1e-8);normal=(normal+1)/2;rough=load(label,'roughness')[...,0];skin,scales,metal,hair=d['masks'];spec=np.full((N,N),.30);rg=np.clip(.76+.16*(rough-.5),.66,.87);mt=np.zeros((N,N));spec[scales]=.42;rg[scales]=np.clip(.56+.20*(rough[scales]-.5),.45,.70);spec[metal]=.80;rg[metal]=np.clip(.48+.20*(rough[metal]-.5),.38,.60);mt[metal]=.65;spec[hair]=.20;rg[hair]=.85
 save(pad(a,cov),T/f'wel_{label}_basecolor_1k.png');save(pad(normal,cov),T/f'wel_{label}_normal_1k.png');save(np.stack([pad(spec,cov),pad(rg,cov),pad(mt,cov)],-1),T/f'wel_{label}_metal_rough_1k.png');R.write_mask([ndimage.gaussian_filter(pad(m.astype(float),cov),.35) for m in d['masks']],T/f'wel_{label}_region_mask.png',size=N)
 overlay=a*.25
 for m,color in zip(d['masks'],[(.85,.4,.2),(.1,.8,.2),(.2,.4,1),(.9,.1,.8)]):overlay[m]=color
 save(overlay,P/'review'/f'wel_{label}_regions.png');report[label]['normal_convention_score']=float(score)
# One tiny atlas lets the held bronze prop share exactly the body's per-tier bronze ramp.
save(np.full((128,128,3),.46),T/'wel_trident_basecolor.png');save(np.tile([.80,.48,.65],(128,128,1)),T/'wel_trident_metal_rough.png');R.write_mask([np.zeros((128,128)),np.zeros((128,128)),np.ones((128,128)),np.zeros((128,128))],T/'wel_trident_region_mask.png',size=128)
materials=[{'base':name+'_A','prefix':name,'mask':f'wel_{label}_region_mask.png','regions':names,'ramps':ramps} for label,name in [('body','Water'),('head','WaterHead'),('trident','Trident')]]
(T/'wel_ramps.json').write_text(json.dumps({'variants':list(pals),'palettes':palettes,'materials':materials,'report':report,'head_skin_gain':gain},indent=2));print(json.dumps(report),'head gain',gain)
