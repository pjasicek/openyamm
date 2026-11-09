"""Shared 1K cloth/bone maps, native tier ramps, and measured tangent-normal conversion."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';N=1024;sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(P.parents[2]/'tools'));from normal_map_convention import measure
def save(a,p):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(p,optimize=True)
def pad(a,c):return a[tuple(ndimage.distance_transform_edt(~c,return_distances=False,return_indices=True))]
def load(label,suffix):
 src=np.asarray(Image.open(P/f'meshy/{label}_retexture_v{2 if label=='head' else 1}/texture_urls_0_{suffix}.png').convert('RGB'),float)/255;yy,xx=np.mgrid[:N,:N];uv=np.stack([(xx+.5)/N,1-(yy+.5)/N],-1)
 if label=='body':uv=np.load(P/'work/uvraster_body.npz')['source_uv']
 coords=np.array([(1-uv[...,1])*src.shape[0]-.5,uv[...,0]*src.shape[1]-.5]);return np.stack([ndimage.map_coordinates(src[...,i],coords,order=1,mode='nearest') for i in range(3)],-1)
data={};report={}
for label in ['body','head']:
 a=load(label,'base_color');d=np.load(P/f'work/uvraster_{label}.npz');part,pos=d['piece'],d['pos'];cov=part>=0;r,g,b=np.moveaxis(a,-1,0);eyes=cov&(g>r*1.28)&(g>b*1.3)&(pos[...,1]<0)&(pos[...,2]>2.04)&(pos[...,2]<2.16)
 if label=='head':
  # Cover the full eye surfaces, including the pale holes omitted by colour thresholding.
  left=((pos[...,0]-.01542)/.0135)**2+((pos[...,2]-2.0873)/.0115)**2
  right=((pos[...,0]+.04194)/.0135)**2+((pos[...,2]-2.0877)/.0115)**2
  eyes=cov&(np.minimum(left,right)<1)&(pos[...,1]>-.045)&(pos[...,1]<-.018)
 if label=='body':
  bones=cov&(part>0)&(part<100);br,bg,bb=[ndimage.gaussian_filter(x,1.25) for x in [r,g,b]];cloth=cov&(part==0)&(np.maximum.reduce([br,bg,bb])<.38)&(np.abs(pos[...,0]+.014)<.30)&(pos[...,2]<1.86);cloth=ndimage.binary_fill_holes(ndimage.binary_closing(cloth,iterations=2))&cov&~bones
 else:
  bounds=(np.abs(pos[...,0]+.014)<.108)&(pos[...,1]<.010)&(pos[...,2]>1.98)&(pos[...,2]<2.18);bones=cov&(((r>b*1.055)&(g>b*1.01)&bounds)|(part>100))&~eyes;cloth=np.zeros_like(cov)
 report_eyes={str(sign):pos[eyes&((pos[...,0]+.014)*sign>0)].mean(0).tolist() for sign in [-1,1]} if eyes.any() else {}
 shade=np.load(P/f'work/native_shade_{label}.npy');shade=np.where(bones,.65+.35*shade,shade) if label=='body' else .6+.4*shade;linear=R.srgb_to_linear(a)*shade[...,None];a=np.where(linear<=.0031308,linear*12.92,1.055*np.maximum(linear,0)**(1/2.4)-.055)
 a[eyes]=.70
 data[label]={'base':a,'cov':cov,'pos':pos,'masks':[cloth,bones,eyes]};report[label]={'eye_centers':report_eyes,'covered':int(cov.sum()),'regions':dict(zip(['tabard','bone','eyes'],[int(x.sum()) for x in [cloth,bones,eyes]]))}
assert data['body']['masks'][0].sum()>5000 and data['head']['masks'][1].sum()>5000,report
palettes={'gst_a':742,'gst_b':743,'gst_c':744};pals={k:np.frombuffer((P.parents[2]/f'assets_dev/worlds/mm6/textures/pal{v}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for k,v in palettes.items()};ramps={k:[] for k in pals}
lut={tuple(c):i for i,c in enumerate(np.uint8(pals['gst_a']*255+.5))};used=[]
for view in range(5):
 a=np.asarray(Image.open(P.parent/'mm6_gst/native'/f'gstflya{view}.png').convert('RGBA'));used.extend(lut.get(tuple(c),0) for c in a[a[...,3]>0,:3])
used=np.array(used)
for region in range(3):
 samples=np.concatenate([d['base'][d['masks'][region]] for d in data.values()]);assert len(samples)>(0 if region==2 else 10),(region,len(samples));lum=R.luminance(samples);lo,hi=np.percentile(lum,[.5,99.5]);hi=max(hi,lo+.002);stops=np.linspace(lo,hi,16)
 if region==0:
  ids=used[(used>=76)&(used<=118)];native={k:np.median(R.srgb_to_linear(v[ids]),axis=0) for k,v in pals.items()};den=float(native['gst_a']@R.LUMA)
 elif region==1:
  base=np.median(R.srgb_to_linear(samples),axis=0);base/=max(float(base@R.LUMA),1e-8);ids=used[(used>=62)&(used<=74)];na=np.median(R.srgb_to_linear(pals['gst_a'][ids]),axis=0);nb=np.median(R.srgb_to_linear(pals['gst_b'][ids]),axis=0);native={'gst_a':base,'gst_b':np.ones(3)*float(nb@R.LUMA)/float(na@R.LUMA),'gst_c':base};den=1
 for key in pals:
  colors=stops[:,None]*native[key]/den if region<2 else np.ones((16,1))*R.srgb_to_linear(pals[key][60])
  if region==0 and key in ('gst_b','gst_c'):
   # User v3: retain the fold detail but make blue/crimson legible above near-black.
   highlight=np.array((58,113,175) if key=='gst_b' else (177,60,65))/255
   shade=.08+.92*np.linspace(0,1,16)**.70
   colors=shade[:,None]*R.srgb_to_linear(highlight)
  ramps[key].append({'range':[float(lo),float(hi)],'colors':np.clip(colors,0,1).tolist()})
for label,d in data.items():
 a,cov=d['base'],d['cov'];normal=load(label,'normal');score=measure(np.uint8(normal*255+.5));assert abs(score)>.15,(label,score)
 if score<0:normal[...,1]=1-normal[...,1]
 # Normal resampling must return unit vectors before packing.
 normal=normal*2-1;normal/=np.maximum(np.linalg.norm(normal,axis=-1,keepdims=True),1e-8);normal=(normal+1)/2
 rough=load(label,'roughness')[...,0];spec=np.full((N,N),.12);rough=np.clip(.90+.12*(rough-.5),.82,.97);bones=d['masks'][1];eyes=d['masks'][2];spec[bones]=.24;rough[bones]=.80;spec[eyes]=.38;rough[eyes]=.32
 save(pad(a,cov),T/f'gst_{label}_basecolor_1k.png');save(pad(normal,cov),T/f'gst_{label}_normal_1k.png');save(np.stack([pad(spec,cov),pad(rough,cov),np.zeros((N,N))],-1),T/f'gst_{label}_metal_rough_1k.png');R.write_mask([ndimage.gaussian_filter(pad(m.astype(float),cov),.40) for m in d['masks']],T/f'gst_{label}_region_mask.png',size=N)
 overlay=a*.4
 for m,color in zip(d['masks'],[(.85,.1,.8),(.95,.55,.08),(.1,1,.1)]):overlay[m]=color
 save(overlay,P/'review'/f'gst_{label}_regions.png');report[label]['source_normal_correlation']=score
cfg={'variants':list(pals),'palettes':palettes,'report':report,'materials':[{'base':name+'_A','prefix':name,'mask':f'gst_{label}_region_mask.png','regions':['tabard','bone','eyes'],'ramps':ramps} for label,name in [('body','Ghost'),('head','GhostHead')]]};(T/'gst_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n');print(json.dumps(report))
