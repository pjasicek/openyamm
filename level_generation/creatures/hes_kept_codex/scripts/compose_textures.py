"""Rasterize retained face labels; compose 1K PBR, seam-safe skin and tier cloth ramps."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
N=1024;T=P/'textures';T.mkdir(exist_ok=True);report={}
def load(p,mode='RGB'):return np.asarray(Image.open(p).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(a,p):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(p)
def pad(a,cov):
 _,idx=ndimage.distance_transform_edt(~cov,return_indices=True);o=a[tuple(idx)];o[cov]=a[cov];return o
def srgb(x):return np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055)
def raster(d,key,head):
 uv=d[key];verts=d['vertices'][d['faces']];which=np.where(d['head']==head)[0];pc=np.full((N,N),-1,np.int16);pos=np.zeros((N,N,3),np.float32);face=np.full((N,N),-1,np.int32);overlap=0
 def cross(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]
 for fi in which:
  t=uv[fi]*N;a,b,c=t;lo=np.maximum(np.floor(t.min(0)).astype(int),0);hi=np.minimum(np.ceil(t.max(0)).astype(int),N-1)
  xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);p=np.stack((xx,yy),-1);den=cross(b-a,c-a)
  if abs(den)<1e-12:continue
  v=cross(p-a,c-a)/den;w=cross(b-a,p-a)/den;inside=(v>1e-6)&(w>1e-6)&(v+w<1-1e-6);ys,xs=np.where(inside);y=N-1-(ys+lo[1]);x=xs+lo[0]
  overlap+=int((pc[y,x]>=0).sum());pc[y,x]=d['piece'][fi];pos[y,x]=(1-v[inside]-w[inside])[:,None]*verts[fi,0]+v[inside,None]*verts[fi,1]+w[inside,None]*verts[fi,2];face[y,x]=fi
 return pc,pos,face,overlap
allsets={}
for code,style,key in [('m','ragged','RaggedUV'),('m','freed','FreedUV'),('f','freed','FreedUV'),('m','head','HeadUV'),('f','head','HeadUV')]:
 d=np.load(P/'texturing'/f'kept_{code}_uv.npz');pc,pos,face,overlap=raster(d,key,style=='head');cov=pc>=0;stem=f'kept_{code}_{style}';job=P/'meshy'/f'{stem}_v1'
 b=load(job/'texture_urls_0_base_color.png');normal=load(job/'texture_urls_0_normal.png');rough=load(job/'texture_urls_0_roughness.png','L')
 hsv=np.asarray(Image.fromarray(np.uint8(b*255)).convert('HSV'),float)/255;h,s,v=hsv.transpose(2,0,1)
 cls=np.zeros((N,N),np.uint8);cls[cov]=8
 skin=np.isin(pc,[1,3,4,17]);hair=np.zeros_like(cov)
 if style=='head':
  # Keep painted eyebrows/lips/scalp hair; classify by position as well as chroma.
  hair=((pc==1)&(v<.30)&(pos[...,2]>1.54))|np.isin(pc,[6,8] if code=='f' else [])
  hair |= (pc==1)&(pos[...,2]>1.615)&(v<.65) if code=='m' else False
  skin &= ~hair;cls[np.isin(pc,[9,10] if code=='f' else [10,11])]=6
  cls[np.isin(pc,[13,14] if code=='f' else [])]=7
 cls[skin]=1;cls[hair]=2
 cls[pc==(7 if code=='m' else 12)]=9
 # Common albedo × retained fine detail; no per-channel seam gains. Face features keep their original paint.
 target=np.array([169,130,103] if code=='m' else [185,145,119])/255
 lum=R.luminance(b);den=ndimage.gaussian_filter(skin.astype(float),6);blur=ndimage.gaussian_filter(lum*skin,6)/np.maximum(den,1e-5)
 detail=np.clip(lum/np.maximum(blur,1e-4),.58,1.5)
 graded=b.copy();repaint=srgb(R.srgb_to_linear(target)*detail[...,None]);strength=.82
 if style=='head':
  # Eye sockets, eyebrows, lips and hairline are features, not skin stains.
  feature=((v<.35)&(pos[...,2]>1.49))|((code=='m')&(pos[...,2]>1.435)&(pos[...,2]<1.49)&(s>.35)&(h<.06))
  graded[skin&~feature]=b[skin&~feature]*(1-strength)+repaint[skin&~feature]*strength
 else:graded[skin]=b[skin]*(1-strength)+repaint[skin]*strength
 ao=load(P/'texturing'/f'{stem}_ao.png','L');surface=cov&~skin
 graded[surface]*=(.82+.18*np.maximum(ao[surface],.45))[:,None]
 # A continuous, shared neck strip across the actual head split removes the different jobs' baked neck shadows.
 cut=json.loads((P/'texturing'/f'kept_{code}_export.json').read_text())['head_neck_cut_z_m']
 blend=np.clip(1-np.abs(pos[...,2]-cut)/.045,0,1);blend=blend*blend*(3-2*blend);blend*=skin
 graded=graded*(1-blend[...,None])+target*blend[...,None]
 spec=np.zeros((N,N));rgh=np.ones((N,N))*.85
 for label,sp,rg in [(1,.35,.65),(2,.15,.88),(6,.75,.30),(7,.3,.66),(8,.16,.88),(9,.50,.68)]:
  m=cls==label
  if m.any():spec[m]=sp;rgh[m]=np.clip(rg+.25*(rough[m]-np.median(rough[m])),.2,1)
 # Suppress unrelated tangent detail right at the shared seam; all files retain Meshy's DirectX convention until prepare_actor_glb.
 normal=normal*(1-blend[...,None])+np.array([.5,.5,1])*blend[...,None]
 rgh=rgh*(1-blend)+.65*blend
 save(pad(np.clip(graded,30/255,243/255),cov),T/f'{stem}_basecolor_1k.png');save(pad(normal,cov),T/f'{stem}_normal_1k.png');save(np.stack([pad(spec,cov),pad(rgh,cov),np.zeros((N,N))],-1),T/f'{stem}_metal_rough_1k.png');Image.fromarray(cls).save(T/f'{stem}_material_classes.png')
 np.savez_compressed(P/'texturing'/f'{stem}_raster.npz',piece=pc,pos=pos,face=face)
 allsets[stem]=(graded,cov,pc,pos)
 report[stem]={'covered_texels':int(cov.sum()),'overlap_pixels':overlap,'classes':{int(c):int((cls==c).sum()) for c in np.unique(cls)},'neck_strip_half_width_m':.045,'skin_albedo_srgb8':(target*255).tolist()}
# Concept: labourer dusty flax, miner blue-grey, enforcer red-brown shirt; same patched ragged geometry/maps.
base,cov,pc,pos=allsets['kept_m_ragged'];mask=pc==0
weight=ndimage.gaussian_filter(pad(mask.astype(float),cov),.7)
colours={'kept_a':(161,145,121),'kept_b':(86,100,108),'kept_c':(151,84,60)}
med=np.median(base[mask],axis=0);targets={k:np.clip(base*np.array(rgb)/255/med,0,1) for k,rgb in colours.items()}
ramps,fit=R.fit_ramps(base,targets,mask.astype(float));R.write_mask([weight],T/'kept_ragged_region_mask.png');R.write_mask([np.zeros((N,N))],T/'kept_head_region_mask.png')
cfg={'variants':list(colours),'materials':[{'base':'KeptBody_A','prefix':'KeptBody','mask':'kept_ragged_region_mask.png','regions':['shirt'],'ramps':{k:[v] for k,v in ramps.items()}},{'base':'KeptHead_A','prefix':'KeptHead','mask':'kept_head_region_mask.png','regions':['shirt'],'ramps':{k:[v] for k,v in ramps.items()}}]}
(T/'kept_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n');report['ramps']={'authority':'approved fam_kept.png: dusty flax / blue-grey / red-brown shirt','target_medians_srgb8':colours,'fit':fit}
# Compare bilinear texture values along the exact shared neck edges, both male styles and female.
def sample(img,uv):
 coords=np.array([(1-uv[:,1])*N-.5,uv[:,0]*N-.5]);return np.stack([ndimage.map_coordinates(img[...,c],coords,order=1,mode='nearest') for c in range(3)],-1)
for code,style,key in [('m','ragged','RaggedUV'),('m','freed','FreedUV'),('f','freed','FreedUV')]:
 d=np.load(P/'texturing'/f'kept_{code}_uv.npz');edges={}
 for fi,tri in enumerate(d['faces']):
  for j in range(3):edges.setdefault(tuple(sorted((int(tri[j]),int(tri[(j+1)%3])))),[]).append(fi)
 a=[];b=[]
 for edge,fs in edges.items():
  if len(fs)!=2 or d['head'][fs[0]]==d['head'][fs[1]]:continue
  for fi in fs:
   bary=np.array([.5 if v in edge else 0 for v in d['faces'][fi]]);uv=d['HeadUV' if d['head'][fi] else key][fi];(b if d['head'][fi] else a).append(bary@uv)
 body=load(T/f'kept_{code}_{style}_basecolor_1k.png');head=load(T/f'kept_{code}_head_basecolor_1k.png');err=np.abs(sample(body,np.array(a))-sample(head,np.array(b)))*255
 report[f'{code}_{style}_seam']={'edge_count':len(a),'mean_rgb8_error':float(err.mean()),'max_rgb8_error':float(err.max())};assert err.mean()<4,(code,style,err.mean())
(P/'review'/'texture_composition.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=1))
