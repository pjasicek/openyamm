"""Bake equal-density islands from the original HD-derived texture surface; remove baked skin streaks."""
from pathlib import Path
import json,sys,gc,shutil,numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
P=Path(__file__).resolve().parents[1];W=P/'work/round2';O=W/'textures';O.mkdir(exist_ok=True);R=P/'review/round2';lum=np.array([.2126,.7152,.0722],np.float32)
def lin(x):return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def srgb(x):return np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055)
def load(f,mode='RGB'):return np.asarray(Image.open(f).convert(mode),dtype=np.float32)/255

def raster(m,mi,N,old=False):
 pos=np.zeros((N,N,3),np.float32);part=np.full((N,N),-1,np.int16);oldmap=np.zeros((N,N,2),np.float32) if old else None
 for fi in np.flatnonzero(m['mat']==mi):
  ids=m['tri'][fi];uv=m['uv'][fi]*N;lo=np.maximum(0,np.floor(uv.min(0)).astype(int));hi=np.minimum(N-1,np.ceil(uv.max(0)).astype(int))
  if np.any(hi<lo):continue
  x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);a,b,c=uv;den=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
  if abs(den)<1e-10:continue
  v=((x-a[0])*(c[1]-a[1])-(y-a[1])*(c[0]-a[0]))/den;w=((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]))/den;u=1-v-w;ok=(u>=0)&(v>=0)&(w>=0);iy=(N-1-(y[ok]-.5)).astype(int);ix=(x[ok]-.5).astype(int);weights=np.stack([u[ok],v[ok],w[ok]],axis=1)
  pos[iy,ix]=weights@m['co'][ids];part[iy,ix]=m['piece'][ids][np.argmax(weights,axis=1)]
  if old:oldmap[iy,ix]=weights@m['old_uv'][fi]
 return pos,part,oldmap

def sample(a,uv):
 co=np.array([(1-uv[:,1])*a.shape[0]-.5,uv[:,0]*a.shape[1]-.5]);return np.stack([ndimage.map_coordinates(a[:,:,i],co,order=1,mode='nearest')for i in range(a.shape[2])],axis=1)

native=load(P.parent/'mm6_mfp/native/mfpstaa0.png');nm=np.array(Image.open(P/'textures/native_skin_sample.png'))>0;native_lin=lin(native)[nm];hue=native_lin.mean(0);hue/=hue@lum
baselevel=.1283
hi=np.load(W/'high_surface.npz');hp,hpart,_=raster(hi,0,2048);ha=load(P/'meshy/body_retexture_v2/texture_urls_0_base_color.png');source={}
for part in np.unique(hpart):
 if part<0:continue
 take=hpart==part;source[int(part)]=(cKDTree(hp[take]),ha[take])
del hp,hpart,ha;gc.collect()
m=np.load(W/'mesh0.npz');report={'body_resolution':4096,'head_resolution':1024,'padding_px':16,'source_body':'meshy/body_retexture_v2/texture_urls_0_base_color.png','head_source':'HD-head-reference-derived head_retexture_v1; 2 mm surface bilateral cleanup, clean native pigment blend, preserved dark facial features and gold jewelry','skin':'Native hue and current mean retained; removed baked directional bands so lighting comes from the smooth mesh. Albedo highlight percentiles are not forced to reproduce already-lit sprite pixels.','sari_source':'references_hd/round2_sari_tile.png','sari_mapping':'Physical-scale repeat; 12 cm skirt, 11.5 cm diagonal sash','regions':{}}
for mi,stem,N in [(0,'mfp',4096),(1,'mfp_head',1024)]:
 pos,part,old=raster(m,mi,N,True);cov=part>=0;ys,xs=np.nonzero(cov);uv=old[ys,xs];points=pos[ys,xs];parts=part[ys,xs]
 olddir=P/'work/round1/textures/lod0';oldbase=load(olddir/f'{stem}_basecolor.png');a=sample(oldbase,uv);oldskin=load(olddir/f'{stem}_skin_mask.png');oldcov=np.load(olddir/f'{stem}_surface.npz')['cov'];_,padix=ndimage.distance_transform_edt(~oldcov,return_indices=True);oldskin[~oldcov]=oldskin[tuple(padix[:,~oldcov])];skin=sample(oldskin,uv)[:,0]>.5;mask=sample(load(olddir/f'{stem}_region_mask.png'),uv)[:,0]
 if mi==0:skin|=np.isin(parts,[4,5])|((parts==0)&(points[:,2]<.92))
 if mi==0:
  for piece,(tree,colors) in source.items():
   ids=np.flatnonzero(parts==piece)
   for chunk in np.array_split(ids,max(1,int(np.ceil(len(ids)/200000)))):
    if not len(chunk):continue
    d,ix=tree.query(points[chunk],k=4,workers=4);weights=1/np.maximum(d,.00015)**2;weights/=weights.sum(1)[:,None];a[chunk]=(colors[ix]*weights[:,:,None]).sum(1)
  # Repair the warm projected collar strip as skin, not a second skin colour.
  skin|=(parts==0)&(points[:,2]>1.30)&(mask<.5)&(a[:,0]>a[:,1]*1.12)&(a[:,2]>a[:,1]*.40)
  # Physical-scale, isotropic pigment variation; no axis-aligned baked lighting on the skin.
  noise=(np.sin(points@np.array([317,523,211]))*np.sin(points@np.array([419,-173,359])))*.006
  a[skin]=srgb((baselevel*(1+noise[skin]))[:,None]*hue)
  blouse=(mask>.5)|((parts==0)&(~skin)&(points[:,2]>1.15)&(points[:,2]<1.36))
  mask[blouse]=1
  # Keep native blouse ramps, but feed a quiet fabric luminance rather than amplified bake noise.
  weave=np.sin(points[:,0]*3800+points[:,1]*1700)*np.sin(points[:,2]*3800-points[:,1]*1600)
  brocade=np.cos(points[:,0]*170+points[:,1]*90)*np.cos(points[:,2]*185)
  pigment=.1435+.0015*brocade+.0007*weave
  a[blouse]=srgb(pigment[blouse,None]*np.ones((1,3)))
  tile=load(P/'references_hd/round2_sari_tile.png')
  theta=np.linspace(-np.pi,np.pi,4097);ds=np.sqrt((.185*np.cos(theta))**2+(.13*np.sin(theta))**2);arc=np.r_[0,np.cumsum((ds[1:]+ds[:-1])*.5*np.diff(theta))];arc/=arc[-1]
  skirt=parts==1;angle=np.arctan2(points[:,0]/.185,-(points[:,1]+.025)/.13);u=np.interp(angle,theta,arc)*8+.5;v=(points[:,2]-.24)/.12+.5
  a[skirt]=sample(tile,np.stack([u[skirt]%1,v[skirt]%1],axis=1))
  sash=parts==6;u=(points@np.array([.85,0,-.526])+.62)/.115+.5;v=(points@np.array([.526,0,.85]))/.115
  a[sash]=sample(tile,np.stack([u[sash]%1,v[sash]%1],axis=1))

 else:
  # Surface bilateral cleanup respects feature colour boundaries and UV seams.
  gold=(a[:,1]>a[:,0]*.76)&(a[:,1]>.45)
  skin&=~gold
  ids=np.flatnonzero(skin);tree=cKDTree(points[ids]);src=a[ids].copy()
  for chunk in np.array_split(ids,max(1,int(np.ceil(len(ids)/12000)))):
   distance,index=tree.query(points[chunk],k=96,workers=4)
   colour_distance=((src[index]-a[chunk,None,:])**2).sum(2)
   weight=np.exp(-.5*(distance/.0020)**2-.5*colour_distance/.15**2)
   weight/=weight.sum(1)[:,None];a[chunk]=(src[index]*weight[:,:,None]).sum(1)
  # The original face includes coarse baked mottling. Restore clean pigment on the
  # cheeks/forehead while leaving dark brows, eyelids and lips in the source colour.
  light=lin(a)@lum;clean_weight=.72*np.clip((light-.035)/.055,0,1)
  a[skin]=srgb(lin(a[skin])*(1-clean_weight[skin,None])+baselevel*hue*clean_weight[skin,None])
  z=points[:,2];blend=np.clip((1.48-z)/.035,0,1)
  a[skin]=a[skin]*(1-blend[skin,None])+srgb(baselevel*hue)*blend[skin,None]

 # Normal maps for exposed skin and cloth are neutral: avoid rebaking the old projected streaks/noise.
 normal=np.tile(np.array([.5,.5,1],np.float32),(len(ys),1));orm=sample(load(olddir/f'{stem}_metal_rough.png'),uv);orm[skin]=[.05,.9,0];orm[mask>.5]=[.04,.92,0]
 region=np.zeros((len(ys),4),np.float32);region[:,0]=mask;region[:,3]=1
 report['regions'][stem]={'skin_mean_linear':float((lin(a[skin])@lum).mean()),'skin_rgb_linear_mean':lin(a[skin]).mean(0).tolist(),'covered_pixels':len(ys),'skin_pixels':int(skin.sum())}
 del old,oldbase,pos,part;gc.collect()
 # Bake occupied texels first, then extend islands through their 16 px gutters and fill remaining atlas voids by nearest surface.
 dist,indices=ndimage.distance_transform_edt(~cov,return_indices=True);fill=(~cov)
 for kind,values in [('basecolor',a),('normal',normal),('metal_rough',orm),('region_mask',region)]:
  arr=np.zeros((N,N,values.shape[1]),np.uint8);arr[ys,xs]=np.uint8(np.clip(values,0,1)*255+.5);arr[fill]=arr[tuple(indices[:,fill])];Image.fromarray(arr).save(O/f'{stem}_{kind}.png')
 sm=np.zeros((N,N),np.uint8);sm[ys,xs]=skin*255;Image.fromarray(sm).save(O/f'{stem}_skin_mask.png')
 print('BAKED',stem,report['regions'][stem],flush=True)
 del a,normal,orm,region,dist,indices,fill,cov,points,uv,parts,skin,mask;gc.collect()
for f in (P/'work/round1/textures/lod0').glob('knife_*.png'):shutil.copy2(f,O/f.name)
(R/'texture_production.json').write_text(json.dumps(report,indent=2))
