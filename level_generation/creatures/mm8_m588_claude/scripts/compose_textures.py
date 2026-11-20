"""Native grey-violet stone, matte PBR, padded atlas and identical palette-588 tier ramps."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
P=Path(__file__).resolve().parents[1];R=P.parents[2];T=P/'textures';N=1024
sys.path[:0]=[str(P.parent/'claude_shared'),str(R/'tools')]
import region_variants as rv,normal_map_convention as nc
from merge_head_material import read_glb,accessor_array
def load(path,mode='RGB',size=N):return np.asarray(Image.open(path).convert(mode).resize((size,size),Image.Resampling.LANCZOS),float)/255
def save(a,path):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path,optimize=True)
def srgb(a):return np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055)
arrays=[]
for path in [P/'work/boulder_texture_upload_v2.glb',P/'meshy/texture_v2/model_urls_glb.glb']:
 d,b=read_glb(path);pr=d['meshes'][0]['primitives'][0];at=pr['attributes'];arrays.append((accessor_array(d,b,at['POSITION']),accessor_array(d,b,at['TEXCOORD_0'])))
(a,auv),(b,buv)=arrays;scale=np.ptp(a,axis=0)/np.ptp(b,axis=0);offset=(a.min(0)+a.max(0))/2-scale*(b.min(0)+b.max(0))/2
dist,ix=cKDTree(np.c_[a,auv]).query(np.c_[b*scale+offset,buv]);assert dist.max()<1e-5
assert np.max(abs(auv[ix]-buv))<1e-6
surface=np.load(P/'work/uv_surface.npz');coverage=surface['piece']>=0
_,(iy,ix)=ndimage.distance_transform_edt(~coverage,return_indices=True)
def pad(a):return a[iy,ix]
job=P/'meshy/texture_v2';base=load(job/'texture_urls_0_base_color.png');ao=load(P/'work/ao.png','L')
palette=np.frombuffer((R/'assets_dev/worlds/mm8/textures/pal588.act').read_bytes()[:768],np.uint8).reshape(256,3)/255
native=np.asarray(Image.open(R/'assets_dev/engine/sprites/m588Sa0.bmp'));colors=palette[native[native!=0]]
lin=rv.srgb_to_linear(colors);lum=lin@rv.LUMA
band=(lum>np.quantile(lum,.35))&(lum<np.quantile(lum,.85))
chroma=np.median(lin[band]/np.maximum(lum[band,None],1e-6),axis=0)
target=float(np.quantile(lum,.6))*1.5
src_lum=rv.luminance(base);ratio=target/float(np.median(src_lum[coverage]))
shade=src_lum*ratio*(.60+.40*np.maximum(ao,.15))
base=srgb(np.clip(shade[...,None]*chroma,0,.8));base=pad(base)
# Keep the 2K diffuse detail; use the same low-frequency native grade measured on the 1K atlas.
raw2=load(job/'texture_urls_0_base_color.png',size=2048);lum2=rv.luminance(raw2)
ao2=load(P/'work/ao.png','L',2048);base2=srgb(np.clip((lum2*ratio*(.60+.40*np.maximum(ao2,.15)))[...,None]*chroma,0,.8))
cov2=np.repeat(np.repeat(coverage,2,axis=0),2,axis=1);_,(y2,x2)=ndimage.distance_transform_edt(~cov2,return_indices=True)
base2=base2[y2,x2];save(base2,T/'boulder_basecolor_2k.png')
normal=pad(load(job/'texture_urls_0_normal.png'));correlation=nc.measure(np.uint8(normal*255+.5))
if correlation<=-.15:normal[...,1]=1-normal[...,1]
save(normal,T/'boulder_normal_1k.png')
rough=np.clip(.86+.12*pad(load(job/'texture_urls_0_roughness.png','L')),.86,.98)
save(np.stack([np.full_like(rough,.12),rough,np.zeros_like(rough)],-1),T/'boulder_metal_rough_1k.png')
rv.write_mask([np.ones((N,N))],T/'boulder_region_mask.png',N)
ramps,error=rv.fit_ramps(base,{'boulder_a':base},coverage.astype(float))
config={'variants':['boulder_a','boulder_b','boulder_c'],'materials':[{'base':'Boulder','prefix':'Boulder','mask':'boulder_region_mask.png','regions':['stone'],'ramps':{f'boulder_{t}':[ramps['boulder_a']] for t in 'abc'}}]}
(T/'boulder_ramps.json').write_text(json.dumps(config,indent=2)+'\n')
report={'texture_geometry_max_error_m':float(dist.max()),'texture_normalization_scale':scale.tolist(),'texture_normalization_offset':offset.tolist(),'UV_preserved':True,'native_palette':588,'same_palette_all_tiers':True,'native_chroma':chroma.tolist(),'native_target_linear_luminance':target,'diffuse_grade_ratio':ratio,'coverage':float(coverage.mean()),'normal_correlation':correlation,'normal_green_flipped':bool(correlation<=-.15),'ramp_fit':error,'metallic':0,'roughness':[.86,.98],'specular':.12}
(T/'composition.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
