"""One body set and independently measured native cloth ramps; no facial anatomy exists inside the hood."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
p=Path(__file__).resolve().parents[1];t=p/'textures';t.mkdir(exist_ok=True)
sys.path.insert(0,str(p.parent/'claude_shared'));import region_variants as R
N=2048
piece=np.load(p/'work/uvraster_UVMap.npz')['piece'];cov=piece>=0
idx=ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True)
def pad(a):return a[tuple(idx)]
def load(f,mode='RGB'):return np.asarray(Image.open(f).convert(mode).resize((N,N),Image.Resampling.LANCZOS),np.float32)/255
m=p/'meshy/retexture_v1'
base=load(m/'texture_urls_0_base_color.png');ao=load(p/'work/ao_body.png','L')
cloth=np.isin(piece,[0,1,5,6]);skin=np.isin(piece,[2,3]);void=piece==4
# Hand colour follows the geometry mask, so projected robe blue cannot become a skin blemish.
lum=base@np.array([.2126,.7152,.0722]);good=skin&(base[...,2]-base[...,0]<.04)&(lum>.35)
nearest=ndimage.distance_transform_edt(~good,return_distances=False,return_indices=True)
clean=lum.copy();bad=skin&~good;clean[bad]=lum[tuple(nearest)][bad]
padded_skin=clean[tuple(ndimage.distance_transform_edt(~skin,return_distances=False,return_indices=True))]
detail=np.clip(padded_skin/np.maximum(ndimage.gaussian_filter(padded_skin,9),.1),.80,1.15)
base[skin]=(np.array([.67,.605,.54])*detail[...,None])[skin]
# Preserve paint detail; no invented eyes, nose or mouth in the black hood recess.
base[void]=np.array([2,3,4])/255
factor=1-.30*(1-np.maximum(ao,.35));factor[cloth]=1
base=np.clip(base*factor[...,None],0,1);base=pad(base)
def save(a,name,size=N,mode=None):
 im=Image.fromarray(np.clip(a*255+.5,0,255).astype(np.uint8),mode)
 if size!=N:im=im.resize((size,size),Image.Resampling.LANCZOS)
 im.save(t/name,optimize=True)
save(base,'mnk1_basecolor_2k.png')
normal=load(m/'texture_urls_0_normal.png');normal[void]=[.5,.5,1]
save(pad(normal),'mnk1_normal_1k.png',1024)
rough=load(m/'texture_urls_0_roughness.png','L');rough=np.clip(.88+.15*(rough-.5),.75,.98);rough[skin]=.8;rough[void]=1
save(pad(np.stack([ao,rough,np.zeros_like(ao)],-1)),'mnk1_orm_1k.png',1024)
mask=np.zeros((N,N,4),np.float32);mask[...,0]=pad(cloth.astype(np.float32))
# Resize channels separately: alpha is an unused region, not transparency.
channels=[Image.fromarray((mask[...,i]*255).astype(np.uint8)).resize((1024,1024),Image.Resampling.LANCZOS) for i in range(4)]
Image.merge('RGBA',channels).save(t/'mnk1_region_mask.png')
classes=np.where(cov,8,0).astype(np.uint8);classes[skin]=1;classes[void]=11
Image.fromarray(classes).resize((1024,1024),Image.Resampling.NEAREST).save(t/'mnk1_material_classes.png')
# Select saturated cloth in the B palette to exclude hands, belt, face and antialiasing; read each tier independently.
cols={k:[] for k in 'abc'}
for v in range(5):
 images=[np.asarray(Image.open(p.parent/f'mm6_mnk1/native_variants/mnk1sta{v}_{pal}.png').convert('RGBA'),np.float32)/255 for pal in [774,775,776]]
 b=images[1];sel=(b[...,3]>.99)&(b[...,2]>b[...,0]*1.45)&(b[...,2]>.08)&(b[...,2]<.83)
 for k,im in zip('abc',images):cols[k].append(im[...,:3][sel])
# Bright projected cuff/rope texels occupy <5% of cloth; they must not flatten the useful navy shading range.
lo,hi=np.percentile(R.luminance(base)[cloth],[.5,95]);ramps={};stats={}
# Sample the native colour curve on a uniform luminance grid, retaining painted texture contrast.
base_lum=R.luminance(base)[cloth]
for k in 'abc':
 c=np.concatenate(cols[k]);c=c[np.argsort(R.luminance(c))]
 lum=R.luminance(c);lum,first=np.unique(lum,return_index=True);c=c[first]
 grid=np.linspace(lum[0],lum[-1],16)
 colors=np.clip(np.stack([np.interp(grid,lum,c[:,i]) for i in range(3)],-1)*1.15,0,1)
 ramps['mnk1_'+k]=[{'range':[float(lo),float(hi)],'colors':R.srgb_to_linear(colors).tolist()}]
 stats[k]={'samples':len(c),'srgb_stops':(colors*255).round().astype(int).tolist()}
cfg={'variants':['mnk1_a','mnk1_b','mnk1_c'],'materials':[{'base':'Monk_A','prefix':'Monk','mask':'mnk1_region_mask.png','ramps':ramps}]}
(t/'mnk1_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n')
(p/'work/texture_report.json').write_text(json.dumps({'classes':{str(i):int((classes==i).sum()) for i in [0,1,8,11]},'palettes':stats,'albedo_gain':1.15,'ao_range':[float(ao[cov].min()),float(ao[cov].max())]},indent=2))
assert np.isfinite(base).all() and (mask[...,1:]==0).all() and hi>lo
print('TEXTURES',stats)
