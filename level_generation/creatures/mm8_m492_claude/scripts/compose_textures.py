"""Padded dragon PBR maps and shared palette-492 region ramps; original service returns stay untouched."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';N=2048
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(P.parents[2]/'tools'));from normal_map_convention import measure
from merge_head_material import Atlas
W=np.array([.2126,.7152,.0722])
def load(path,mode='RGB'):return np.array(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255

def save(a,path):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path)
def pad(a,cov):return a[tuple(ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True))]
def hsv(rgb):return np.moveaxis(np.array(Image.fromarray(np.uint8(np.clip(rgb,0,1)*255)).convert('HSV'),float)/255,-1,0)
def encode(a):return np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055)
def regions(rgb):
 h,s,v=hsv(rgb);gold=(h>.065)&(h<.20)&(s>.27)&(v>.12);red=((h<.06)|(h>.96))&(s>.38)&(v>.12);ivory=(s<.28)&(v>.58)
 return [~(gold|red|ivory),red,gold,ivory]

def service_map(label,kind):
 a=load(P/'meshy'/f'{label}_retexture_v1'/f'texture_urls_0_{kind}.png');source=a.copy()
 for repair in json.loads((P/'work/texture_uv_parity.json').read_text())[label]['repairs']:
  uv=np.array(repair['target_uv'])*N;dest=np.array(repair['source_uv'])*N
  x0,y0=np.maximum(np.floor(uv.min(0)).astype(int)-1,0);x1,y1=np.minimum(np.ceil(uv.max(0)).astype(int)+1,N-1)
  x,y=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
  matrix=np.vstack([uv.T,np.ones(3)]);weights=np.linalg.solve(matrix,np.stack([x.ravel(),y.ravel(),np.ones(x.size)]))
  mask=(weights>=-.02).all(0);sx,sy=dest.T@weights[:,mask];iy=(N-1-(y.ravel()[mask]-.5)).astype(int);ix=(x.ravel()[mask]-.5).astype(int)
  for channel in range(3):a[iy,ix,channel]=ndimage.map_coordinates(source[...,channel],[N-.5-sy,sx-.5],order=1,mode='nearest')
 return a

D={};report={}
for label in ['body','head','wings']:
 d=np.load(P/'work'/f'uvraster_{label}.npz');cov=d['piece']>=0;rgb=service_map(label,'base_color');m=[cov&x for x in regions(rgb)]
 classes=np.zeros((N,N),np.uint8);classes[cov]=1
 if label=='wings':classes[cov&m[2]]=3
 classes[cov&m[3]]=4
 if label=='head':
  horn=cov&(d['piece']>0)&(d['piece']!=57);classes[horn]=4
  for w in m:w[horn]=False
  m[3][horn]=True
  x,y,z=np.moveaxis(d['pos'],-1,0);teeth=(d['piece']==57)|(m[3]&(y<-.35)&(z<.29));classes[teeth]=5
  eye=cov&(d['piece']==0)&(abs(x)>.012)&(abs(x)<.03)&(((y+.3516)/.0028)**2+((z-.3118)/.0016)**2<1)&m[2]
  assert eye.sum()>20;classes[eye]=6
  # Recover the native red iris while retaining the generated pupil and small highlights.
  rgb[eye]=rgb[eye].max(1)[:,None]*np.array([1.,.075,.04])
  for w in m:w[eye]=False
  m[1][eye]=True
 oral=d['oral'];classes[oral]=7;rgb[oral]=(.025,.005,.008)
 for w in m:w[oral]=False
 ao=ndimage.gaussian_filter(pad(load(T/f'dragon_{label}_ao_1k.png','L'),cov),1.0);rgb*=.82+.18*ao[...,None]
 normal=service_map(label,'normal');correlation=measure(np.uint8(normal*255+.5))
 if correlation<-.15:normal[...,1]=1-normal[...,1]
 geo=load(T/f'dragon_{label}_geometry_normal_2k.png','RGBA');valid=geo[...,3]>.5
 assert int((cov&~valid).sum())<max(32,int(cov.sum()*.015)),(label,'normal bake misses')
 n1=geo[...,:3]*2-1;n1[~valid]=(0,0,1);n2=normal*2-1
 t=n1+np.array([0,0,1]);u=n2*np.array([-1,-1,1]);n=t*np.sum(t*u,axis=-1)[...,None]/np.maximum(t[...,2:3],1e-5)-u
 n/=np.maximum(np.linalg.norm(n,axis=-1,keepdims=True),1e-5);normal=n*.5+.5
 normal[oral]=(.5,.5,1)
 D[label]={'rgb':rgb,'masks':m,'classes':classes,'ao':ao,'normal':normal,'cov':cov,'pos':d['pos']}
 report[label]={'covered_texels':int(cov.sum()),'overlapping_texels':int((d['coverage']>1).sum()),'normal_source_correlation':correlation}
# Head and neck use the same paint luminance at their continuous skin boundary.
b,h=D['body'],D['head'];bm=b['masks'][0]&(b['pos'][...,2]>.255);hm=h['masks'][0]&(h['pos'][...,2]<.30)
gain=1.
if bm.sum()>30 and hm.sum()>30:
 gain=float(np.clip(np.median(R.luminance(b['rgb'])[bm])/max(np.median(R.luminance(h['rgb'])[hm]),1e-6),.7,1.4))
 w=ndimage.gaussian_filter(pad(h['masks'][0].astype(float),h['cov']),1);h['rgb']=encode(R.srgb_to_linear(h['rgb'])*(1+w[...,None]*(gain-1)))
report['head_neck_linear_gain']=gain
# Measured native chromaticity keeps the generated surface shading while preserving the actual palette identity.
pixels=[]
for view in (0,2):
 for name in [f'm492sa{view}']+[f'm492w{c}{view}' for c in 'abcdefghij']:
  a=np.array(Image.open(P/f'references/native/{name}.png'));pixels.append(a[a[...,3]>127,:3]/255)
native=np.concatenate(pixels);native=native.reshape(-1,1,3);masks=regions(native);ramps=[]
for mask in masks:
 c=R.srgb_to_linear(native[mask]);lum=c@W;assert len(c)>20
 c=c[np.argsort(lum)];tone=np.mean(c[len(c)//3:len(c)*4//5],0);chroma=tone/max(float(tone@W),1e-6)
 ramps.append({'range':[0.,1.],'colors':np.clip(np.linspace(0,1,16)[:,None]*chroma,0,1).tolist()})
for label,d in D.items():
 cov=d['cov'];classes=d['classes'];rough=np.full((N,N),.82);spec=np.full((N,N),.18)
 for cls,r,s in [(3,.86,.10),(4,.45,.35),(5,.35,.45),(6,.15,.55),(7,.75,.08)]:rough[classes==cls]=r;spec[classes==cls]=s
 spec*=.35+.65*d['ao'];maps={'basecolor':pad(d['rgb'],cov),'normal':pad(d['normal'],cov),'metal_rough':np.stack([pad(spec,cov),pad(rough,cov),np.zeros_like(rough)],-1),'ao':pad(d['ao'],cov)}
 for name,a in maps.items():save(a,T/f'dragon_{label}_{name}_2k.png')
 Image.fromarray(pad(classes,cov)).save(T/f'dragon_{label}_material_classes.png')
 weights=[ndimage.gaussian_filter(pad(w.astype(float),cov),.65) for w in d['masks']];R.write_mask(weights,T/f'dragon_{label}_region_mask.png',size=N)
# Three equal-density domains share one runtime material, with padded gutters and no resampling.
a=Atlas((N,N),(N,N));ab=Atlas((a.width,N),(N,N))
for name in ['basecolor_2k','normal_2k','metal_rough_2k','ao_2k','material_classes','region_mask']:
 images=[Image.open(T/f'dragon_{label}_{name}.png') for label in ['body','head','wings']]
 ab.compose(a.compose(images[0],images[1]),images[2]).save(T/f'dragon_{name}.png')
cfg={'variants':['m492'],'palettes':{'m492':492},'materials':[{'base':'Dragon_A','prefix':'Dragon','mask':'dragon_region_mask.png','regions':['charcoal_scales','red_seams','gold_scutes_membranes','ivory_horns'],'ramps':{'m492':ramps}}],'report':report}
(T/'dragon_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n');(P/'work/atlas_layout.json').write_text(json.dumps({'width':ab.width,'height':N,'domain_width':N,'offsets':[0,N+32,2*N+64]},indent=2)+'\n');print('COMPOSE',report)
