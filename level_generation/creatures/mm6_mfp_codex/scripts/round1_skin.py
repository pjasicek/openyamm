"""Paint native-calibrated skin in surface coordinates, independent of UV seams and bake rays."""
from pathlib import Path
import json,sys,numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
lum=np.array([.2126,.7152,.0722])
def linear(x):return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def srgb(x):return np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055)
def save(x,f):Image.fromarray(np.uint8(np.clip(x,0,1)*255+.5)).save(f)
def raster(m,mi,N,W):
 pos=np.zeros((N,W,3));nor=pos.copy();part=np.full((N,W),-1);cov=np.zeros((N,W),bool)
 for fi in np.flatnonzero(m['mat']==mi):
  ids=m['tri'][fi];uv=m['uv'][fi]*np.array([W,N]);lo=np.maximum(0,np.floor(uv.min(0)).astype(int));hi=np.minimum(np.array([W-1,N-1]),np.ceil(uv.max(0)).astype(int))
  if np.any(hi<lo):continue
  x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);a,b,c=uv;den=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
  if abs(den)<1e-10:continue
  v=((x-a[0])*(c[1]-a[1])-(y-a[1])*(c[0]-a[0]))/den;w=((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]))/den;u=1-v-w;ok=(u>=0)&(v>=0)&(w>=0)
  iy=(N-1-(y[ok]-.5)).astype(int);ix=(x[ok]-.5).astype(int);weights=np.stack([u[ok],v[ok],w[ok]],axis=1)
  pos[iy,ix]=weights@m['co'][ids];nor[iy,ix]=weights@m['normals'][ids];part[iy,ix]=m['piece'][ids][np.argmax(weights,axis=1)];cov[iy,ix]=True
 nor/=np.maximum(np.linalg.norm(nor,axis=2,keepdims=True),1e-9)
 return pos,nor,part,cov
native=np.array(Image.open(P.parent/'mm6_mfp/native/mfpstaa0.png').convert('RGB'))/255;mask=np.array(Image.open(P/'textures/native_skin_sample.png'))>0;native_rgb=linear(native)[mask];reference=np.sort(native_rgb@lum);hue=native_rgb.mean(0);hue/=hue@lum
REGIONS=[(1,'face'),(2,'neck'),(3,'midriff'),(4,'arms'),(5,'legs'),(6,'hands'),(7,'feet')]
report={'sampling':'front-facing surface texels; native front sprite, linear luminance','native':{'mean':float(reference.mean()),'p90':float(np.percentile(reference,90)),'p95':float(np.percentile(reference,95))},'levels':{}}
for level in range(1):
 m=np.load(P/f'work/round1/mesh{level}.npz');old=P/f'work/final_textures/lod{level}';out=P/f'work/round1/textures/lod{level}';out.mkdir(parents=True,exist_ok=True);stats={}
 for mi,stem in enumerate(['mfp','mfp_head']):
  a=np.array(Image.open(old/f'{stem}_basecolor.png').convert('RGB'))/255;N=len(a);W=N+64 if mi==0 else N;a=np.pad(a,((0,0),(0,W-N),(0,0)));pos,nor,part,cov=raster(m,mi,N,W);x,y,z=np.moveaxis(pos,2,0);rgb8=Image.fromarray(np.uint8(a*255));hsv=np.array(rgb8.convert('HSV'))/255;h,s,v=np.moveaxis(hsv,2,0)
  neck=(part==0)&(z>1.335+2.5*x*x+.5*(y+.11)**2)&(z<1.455)
  mid=(part==0)&(z>.92)&((z<1.152)|((z<1.29)&(h<.15)&(s>.1)))
  legs=(part==0)&(z<=.92)
  arms=np.isin(part,[4,5])
  face=(part==0)&(z>=1.43)&(h<.13)&(s>.18)&(v>.16)
  skin=(neck|mid|legs|arms|face)&cov
  region=np.zeros((N,W),np.uint8);region[legs]=5;region[mid]=3;region[neck]=2;region[arms]=4;region[face]=1;region[arms&(z<.91)]=6;region[legs&(z<.075)]=7
  # Use one smooth world-space lighting field on all islands; never quantile-map the failed patchy bake.
  field=np.clip(nor@np.array([-.32,-.62,.72]),-1,1)
  smoothnor=nor.copy()
  for side in ['L','R']:
   bones=json.loads((P/'review/round1/inspect.json').read_text())['bones'];el=np.array(bones[f'B_{side}_Forearm']['head']);wr=np.array(bones[f'B_{side}_Hand']['head']);axis=wr-el;t=(pos-el)@axis/(axis@axis);rad=pos-(el+t[:,:,None]*axis);rad/=np.maximum(np.linalg.norm(rad,axis=2,keepdims=True),1e-8);take=arms&((x>0)if side=='L'else(x<0));smoothnor[take]=rad[take]
  take=neck;rad=np.stack([x,(y+.02)*1.3,np.zeros_like(x)],axis=2);rad/=np.maximum(np.linalg.norm(rad,axis=2,keepdims=True),1e-8);smoothnor[take]=rad[take]
  torso=np.stack([x,(y+.035)*1.35,np.zeros_like(x)],axis=2);torso/=np.maximum(np.linalg.norm(torso,axis=2,keepdims=True),1e-8);smoothnor[mid]=torso[mid]
  field=np.clip(smoothnor@np.array([-.32,-.62,.72]),-1,1)
  # Keep facial features but discard the broad baked illumination at the material seam.
  den=ndimage.gaussian_filter(face.astype(float),8);oldL=linear(a)@lum;smooth=ndimage.gaussian_filter(oldL*face,8)/np.maximum(den,1e-8);detail=np.clip(oldL/np.maximum(smooth,.01),.6,1.35)
  front=(smoothnor[:,:,1]<-.1);field[face]=ndimage.gaussian_filter(oldL,1)[face]
  target=np.zeros((N,W));reference_q=np.linspace(0,1,len(reference))
  for ident,label in REGIONS:
   take=(region==ident)&skin
   if not take.any():continue
   f=field[take];reference_values=field[take&front];order=np.sort(reference_values if len(reference_values)>2 else f);q=np.interp(f,order,np.linspace(0,1,len(order)));target[take]=np.interp(q,reference_q,reference)
  # Use a single curve on both sides of the neck seam, with a soft jaw transition.
  radial=np.stack([x,(y+.02)*1.3,np.zeros_like(x)],axis=2);radial/=np.maximum(np.linalg.norm(radial,axis=2,keepdims=True),1e-8);nf=radial@np.array([-.32,-.62,0]);pool=[]
  for nstem in ['mfp','mfp_head']:
   previous=np.load(out/f'{nstem}_surface.npz');pp=previous['pos'];rr=np.stack([pp[:,:,0],(pp[:,:,1]+.02)*1.3,np.zeros(pp.shape[:2])],axis=2);rr/=np.maximum(np.linalg.norm(rr,axis=2,keepdims=True),1e-8);values=rr@np.array([-.32,-.62,0]);pool.extend(values[(previous['region']==2)&(rr[:,:,1]<-.1)].tolist())
  ordered=np.sort(pool);q=np.interp(nf,ordered,np.linspace(0,1,len(ordered)));necklight=np.interp(q,reference_q,reference);blend=np.clip((1.475-z)/.025,0,1);take=(neck|face)&skin;target[take]=target[take]*(1-blend[take])+necklight[take]*blend[take]
  clean=srgb(np.maximum(target,.035)[:,:,None]*hue)
  # Keep the original face's local colour/detail; harmonize its broad tone with a gentle monotone curve.
  oldlin=linear(a);ol=oldlin@lum;fl=np.interp(ol,[0,.02,.05,.12,.20,.249,.322,1],[0,.02,.04,.086,.176,.237,.324,1]);frgb=oldlin* (fl/np.maximum(ol,1e-8))[:,:,None];faceBlend=np.clip((z-1.455)/.025,0,1);clean[face]=srgb(frgb[face])*faceBlend[face,None]+clean[face]*(1-faceBlend[face,None]);a[skin]=clean[skin]
  # Replace all skin normals, including the visible triangle islands, by the smoothly shaded mesh normal.
  normal=np.array(Image.open(old/f'{stem}_normal.png').convert('RGB'))/255;normal=np.pad(normal,((0,0),(0,W-N),(0,0)));normal[skin]=[.5,.5,1]
  orm=np.array(Image.open(old/f'{stem}_metal_rough.png').convert('RGB'))/255;orm=np.pad(orm,((0,0),(0,W-N),(0,0)));orm[skin]=[.07,.85,0]
  reg=np.array(Image.open(old/f'{stem}_region_mask.png').convert('RGBA'))/255;reg=np.pad(reg,((0,0),(0,W-N),(0,0)));reg[skin]=[0,0,0,1]
  # Extend each surface edge sixteen pixels into its gutter, preserving occupied non-skin islands.
  dist,ix=ndimage.distance_transform_edt(~cov,return_indices=True);fill=(~cov)&(dist<=16)
  for arr in [a,normal,orm,reg]:arr[fill]=arr[tuple(ix[:,fill])]
  for kind,arr in [('basecolor',a),('normal',normal),('metal_rough',orm),('region_mask',reg)]:save(arr,out/f'{stem}_{kind}.png')
  save(skin,out/f'{stem}_skin_mask.png');np.savez_compressed(out/f'{stem}_surface.npz',region=region,skin=skin,cov=cov,pos=pos,front=front)
  quant=linear(np.round(np.clip(a,0,1)*255)/255)@lum
  for ident,label in REGIONS:
   take=(region==ident)&skin&front
   if take.any():stats[stem+'_'+label]={'pixels':int(take.sum()),'mean':float(quant[take].mean()),'p90':float(np.percentile(quant[take],90)),'p95':float(np.percentile(quant[take],95))}
 # Props remain byte-for-byte the original textures.
 import shutil
 for f in old.glob('knife_*.png'):shutil.copy2(f,out/f.name)
 report['levels'][str(level)]=stats
 print('SKIN',level,stats,flush=True)
(P/'review/round1/skin_luminance.json').write_text(json.dumps(report,indent=2))
