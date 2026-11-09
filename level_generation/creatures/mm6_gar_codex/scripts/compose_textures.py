"""Compose shared stone maps, padded anatomy masks and native 736/737/738 palette ramps."""
from pathlib import Path
import importlib.util,json,sys
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';SIZE=1024
sys.path[:0]=[str(Path('level_generation/creatures/claude_shared').resolve()),str(Path('tools').resolve())]
import tier_textures as tier
from normal_map_convention import measure
spec=importlib.util.spec_from_file_location('raster',P.parent/'mm6_gob_claude/scripts/compose_textures_v2.py');raster=importlib.util.module_from_spec(spec);spec.loader.exec_module(raster);raster.SIZE=SIZE
def load(path,mode='RGB'):return np.array(Image.open(path).convert(mode).resize((SIZE,SIZE),Image.Resampling.LANCZOS),np.float32)/255
def save(a,path):Image.fromarray(np.clip(a*255+.5,0,255).astype(np.uint8)).save(path)
pals=[np.frombuffer(Path(f'assets_dev/worlds/mm6/textures/pal{pid}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for pid in [736,737,738]]
sel=(np.arange(256)<172)&(np.ptp(pals[0],axis=1)<15/255)&(pals[0].mean(1)>15/255);ids=np.where(sel)[0];lum=pals[0][ids]@tier.LUMA;order=np.argsort(lum);ids=ids[order];lum=lum[order]
unique=np.unique(lum);mapped=[np.array([pal[ids][lum==v].mean(0) for v in unique]) for pal in pals]
xs=np.linspace(0,.75,16);native=tier.linear_to_srgb(xs)/1.35;ramps={}
for n,v in enumerate(['gar_a','gar_b','gar_c']):
 colors=np.stack([np.interp(native,unique,mapped[n][:,c],left=0,right=mapped[n][-1,c]) for c in range(3)],-1)*1.35
 if n==0:colors=tier.linear_to_srgb(xs)[:,None]*np.ones((1,3))
 eye=np.array([[250,0,0],[170,226,0],[255,0,0]][n])/255
 ramps[v]=[{'range':[0,.75],'colors':tier.srgb_to_linear(np.clip(colors,0,1)).round(7).tolist()},{'range':[0,1],'colors':np.tile(tier.srgb_to_linear(eye),(16,1)).round(7).tolist()}]
config={'variants':list(ramps),'materials':[]};report={'source_palettes':[736,737,738],'stone_indices':ids.tolist(),'albedo_lift':1.35,'materials':{}}
for part,job in [('body','body_texture_v2'),('head','head_texture_v1')]:
 src=P/'meshy'/job;data=np.load(P/f'work/{part}_uv3d.npz');regions,xyz=raster.rasterise(data,tol=0);valid=regions>=0;interior=ndimage.binary_erosion(valid,iterations=1);_,ind=ndimage.distance_transform_edt(~interior,return_indices=True)
 def pad(a):return a[tuple(ind)]
 raw=load(src/'texture_urls_0_base_color.png');h,s,v=raster.hsv(raw);x,y,z=xyz.transpose(2,0,1)
 eye=np.zeros(valid.shape,bool);mouth=eye.copy();teeth=eye.copy();horn=eye.copy()
 if part=='head':
  eye=valid&(z>1.64)&(z<1.76)&(y<-.065)&(s>.42)&((h<28)|(h>340))&(v>.20)
  mouth=valid&(z<1.645)&(y<-.10)&((v<.22)|((s>.35)&(h<35)))
  teeth=valid&(z<1.65)&(y<-.10)&(v>.61)&(s<.4)
  horn=valid&(z>1.76)
  assert eye.sum()>10,('eyes',eye.sum())
 stone=valid&~(eye|mouth|teeth);mask=np.stack([pad(stone.astype(float)),pad(eye.astype(float)),np.zeros(valid.shape),np.zeros(valid.shape)],-1)
 # Padding precedes feathering: all UV margins inherit their island's region.
 mask[:,:,:2]=ndimage.gaussian_filter(mask[:,:,:2],sigma=(.5,.5,0));base=pad(raw);gray=base@tier.LUMA;base=np.where(pad(stone)[...,None],gray[...,None],base)
 ao=load(T/f'{part}_ao.png','L');base*=((1-.12)+.12*pad(ao))[...,None]
 classes=np.where(regions==3,3,1).astype(np.uint8);classes[horn]=4;classes[teeth]=5;classes[eye]=6;classes[mouth]=7;classes=pad(classes)
 Image.fromarray(classes).save(T/f'{part}_classes.png');save(mask,T/f'{part}_regions.png');save(base,T/f'{part}_basecolor.png')
 normal_image=np.array(Image.open(src/'texture_urls_0_normal.png').convert('RGB').resize((2048,2048),Image.Resampling.LANCZOS));correlation=measure(normal_image);flip=correlation<-.1
 detail=load(src/'texture_urls_0_normal.png')*2-1
 if flip:detail[...,1]*=-1
 detail=pad(detail);geometry=load(T/f'{part}_geometry_normal.png')*2-1;geometry=pad(geometry)
 if part=='body':
  # Thin wing bake rays caught the opposite surface, producing false cracks; the body retains its silhouette.
  geometry[:]=[0,0,1]
 # Whiteout blend of geometric loss and the independently generated stone microdetail.
 out=np.dstack([geometry[...,0]+detail[...,0]*.55,geometry[...,1]+detail[...,1]*.55,geometry[...,2]*detail[...,2]]);out/=np.maximum(np.linalg.norm(out,axis=-1,keepdims=True),1e-8);save(out*.5+.5,T/f'{part}_normal.png')
 rough=np.clip(pad(load(src/'texture_urls_0_roughness.png','L')),.78,.97);rough=np.where(classes==6,.48,rough);metal=np.zeros_like(rough);specular=np.where(classes==6,.32,.045);save(np.stack([specular,rough,metal],-1),T/f'{part}_metal_rough.png')
 config['materials'].append({'base':'Gargoyle'+part.title(),'prefix':'Gargoyle'+part.title(),'mask':f'{part}_regions.png','ramps':ramps})
 for variant in ramps:save(tier.apply(base,mask,ramps[variant]),T/f'{part}_{variant}.png')
 report['materials'][part]={'runtime_resolution':SIZE,'uv_texels':int(valid.sum()),'eye_texels':int(eye.sum()),'normal_source_correlation':correlation,'normal_green_flipped':bool(flip),'classes':{str(k):int((classes==k).sum()) for k in np.unique(classes)},'raw_job':job,'geometry_normal_used':part=='head'}
 assert np.isfinite(base).all() and np.isfinite(out).all() and (mask.sum(-1)<=1.001).all()
(T/'gar_ramps.json').write_text(json.dumps(config,indent=2));(T/'composition.json').write_text(json.dumps(report,indent=2));print(json.dumps(report['materials'],indent=2))
