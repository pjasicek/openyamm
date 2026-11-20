"""Dedicated head maps: preserve facial paint, blend only the lower neck into the body."""
from pathlib import Path
import sys,json
import numpy as np
from scipy import ndimage
from PIL import Image
p=Path(__file__).resolve().parents[1];T=p/'textures';src=p/'meshy/head_geometry_v3';N=2048
sys.path.insert(0,str(p.parents[2]/'tools'));import normal_map_convention as NC
z=np.load(p/'work/uvraster_HeadUV.npz');cov=z['coverage'];pos=z['pos']
source_uv=np.load(p/'work/head_v2_reprojection.npz')['srcuv']
def load(kind):
 raw=np.asarray(Image.open(src/f'texture_urls_0_{kind}.png').convert('RGB'),float)/255;h,w=raw.shape[:2]
 return np.stack([ndimage.map_coordinates(raw[:,:,c],[(1-source_uv[:,:,1])*h-.5,source_uv[:,:,0]*w-.5],order=1,mode='nearest') for c in range(3)],axis=-1)
def save(a,name):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(T/name)
base=load('base_color');normal=load('normal');rough=load('roughness')[:,:,0]
near=tuple(ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True))
hsv=np.asarray(Image.fromarray(np.uint8(base*255)).convert('HSV'))
scalp=cov&(z['piece']==4)
paint=np.load(p/'work/hair_volume_paint.npz')
assert np.array_equal(paint['mask'],scalp)
base[scalp]=paint['base']
normal[scalp]=[.5,.5,1]
skin=cov&~scalp&(((hsv[:,:,2]>92)&(hsv[:,:,0]<32))|(pos[:,:,2]<1.49))
hair=cov&~skin
# Only the neck seam is colour matched; eyelids, lips, stubble and facial shading remain intact.
f=np.clip((1.510-pos[:,:,2])/.04,0,1);f=f*f*(3-2*f);f*=skin&((pos[:,:,2]<1.49)|(pos[:,:,1]>0))
lum=base@np.array([.2126,.7152,.0722]);blur=ndimage.gaussian_filter(np.where(skin,lum,0),9)/np.maximum(ndimage.gaussian_filter(skin.astype(float),9),1e-5)
detail=np.clip(lum/np.maximum(blur,1e-5),.85,1.15)
body=np.load(p/'work/uvraster_UVMap.npz');body_color=np.asarray(Image.open(T/'bedraggled_basecolor_1k.png'),float)/255
body_neck=body['coverage']&(body['piece']==0)&(body['pos'][:,:,2]>1.44)
neck=np.median(body_color[body_neck],axis=0)*(.78+.22*detail[:,:,None])
base=base*(1-f[:,:,None])+neck*f[:,:,None]
base[z['bridge']]=np.median(body_color[body_neck],axis=0)
normal[z['bridge']]=[.5,.5,1]
save(base[near],'bedraggled_head_basecolor_2k.png')
corr=NC.measure(np.uint8(normal*255+.5))
if corr<=-.15:normal[:,:,1]=1-normal[:,:,1]
normal=(normal-[.5,.5,1])*.65+[.5,.5,1]
save(normal[near],'bedraggled_head_normal_2k.png')
spec=np.where(skin,.14,.10);rr=np.where(skin,.82,.88)+.08*(rough-.5)
save(np.stack([spec,np.clip(rr,.5,.98),np.zeros_like(rr)],-1)[near],'bedraggled_head_metal_rough_2k.png')
classes=np.where(skin,1,2).astype(np.uint8);Image.fromarray(classes[near]).save(T/'bedraggled_head_material_classes.png')
Image.fromarray(np.zeros((N,N,4),np.uint8)).save(T/'bedraggled_head_region_mask.png')
r=json.loads((T/'bedraggled_ramps.json').read_text());head=dict(r['materials'][0]);head.update(base='BedraggledHead_A',prefix='BedraggledHead',mask='bedraggled_head_region_mask.png');r['materials'].append(head);(T/'bedraggled_ramps.json').write_text(json.dumps(r,indent=2)+'\n')
report={'resolution':N,'covered_texels':int(cov.sum()),'skin_texels':int(skin.sum()),'normal_correlation':corr,'neck_blend_z':[1.470,1.510],'head_source':'meshy/head_geometry_v3'}
(T/'head_texture_v2_report.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
