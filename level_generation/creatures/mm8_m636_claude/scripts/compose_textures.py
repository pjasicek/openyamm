"""Preserve Meshy's UVs, compose one atlas and fit native purple/green/orange palette ramps."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy.spatial import cKDTree
P=Path(__file__).resolve().parents[1];R=P.parents[2]
sys.path[:0]=[str(R/'tools'),str(P.parent/'claude_shared')]
from merge_head_material import read_glb,accessor_array
import region_variants as RV
import tier_textures as TT
from normal_map_convention import measure
T=P/'textures';T.mkdir(exist_ok=True)
raw=P/'meshy/fish_texture_v1'
arrays=[]
for path in [P/'work/fish_neutral_upload.glb',raw/'model_urls_glb.glb']:
    d,b=read_glb(path);pr=d['meshes'][0]['primitives'][0]
    pos=accessor_array(d,b,pr['attributes']['POSITION']);uv=accessor_array(d,b,pr['attributes']['TEXCOORD_0'])
    assert d['accessors'][pr['indices']]['count']==1950
    arrays.append(np.concatenate(((pos-pos.min(0))/(pos.max(0)-pos.min(0)),uv),axis=1))
error=float(cKDTree(arrays[0]).query(arrays[1])[0].max());assert error<1e-5
base=np.asarray(Image.open(raw/'texture_urls_0_base_color.png').convert('RGB'),float)/255
# Retain pale fin rays and markings; only purple body pigment participates in the palette change.
base=TT.linear_to_srgb(RV.srgb_to_linear(base)*.85)
Image.fromarray(np.uint8(np.clip(base,0,1)*255+.5)).save(T/'fish_basecolor.png')
small=RV.load_srgb(T/'fish_basecolor.png',1024)
pigment=np.minimum(small[...,0]-small[...,1],small[...,2]-small[...,1])
weight=np.clip((pigment-.012)/.055,0,1)
weight=np.asarray(Image.fromarray(np.uint8(weight*255)).filter(ImageFilter.GaussianBlur(.55)),float)/255
RV.write_mask([weight],T/'fish_region_mask.png')
core=weight>.5;lum=RV.luminance(small);texlum=lum[core]
order=np.argsort(texlum);rank=np.empty(order.size);rank[order]=(np.arange(order.size)+.5)/order.size
palettes={k:np.frombuffer((R/f'assets_dev/worlds/mm8/textures/Pal{n}.act').read_bytes(),np.uint8)[:768].reshape(256,3)/255
          for k,n in [('m636_a',637),('m636_b',638),('m636_c',636)]}
indices=np.concatenate([np.asarray(Image.open(R/f'assets_dev/engine/sprites/m636Wa{v}.bmp')).ravel() for v in range(5)])
purple=palettes['m636_a'];selected=(purple[:,0]-purple[:,1]>.025)&(purple[:,2]-purple[:,1]>.04)
selected[0]=False;indices=indices[selected[indices]];assert len(indices)>1000
targets={};stats={}
for name,palette in palettes.items():
    colors=RV.srgb_to_linear(palette[indices]);colors=colors[np.argsort(colors@RV.LUMA)]
    mid=colors[int(.15*len(colors)):int(.95*len(colors))]
    chroma=np.array([(part/np.maximum(part@RV.LUMA,1e-4)[:,None]).mean(0) for part in np.array_split(mid,8)])
    interp=np.stack([np.interp(rank,np.linspace(0,1,8),chroma[:,c]) for c in range(3)],axis=1)
    gain=float(np.clip(1.4*(colors@RV.LUMA).mean()/texlum.mean(),.6,1.8))
    target=small.copy();target[core]=TT.linear_to_srgb(np.clip(interp*(texlum*gain)[:,None],0,1));targets[name]=target
    stats[name]={'native_pixels':len(indices),'luminance_gain':gain}
ramps,fit=RV.fit_ramps(small,targets,weight)
config={'variants':list(palettes),'materials':[{'base':'FishMaterial','prefix':'Fish','mask':'fish_region_mask.png',
        'ramps':{k:[r] for k,r in ramps.items()}}]}
(T/'fish_ramps.json').write_text(json.dumps(config,indent=2)+'\n')
normal=np.asarray(Image.open(raw/'texture_urls_0_normal.png').convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS)).copy()
corr=measure(normal)
if corr<=-.15:normal[...,1]=255-normal[...,1]
Image.fromarray(normal).save(T/'fish_normal.png')
# Texture classes follow pigment/neutral fin regions; tiny dark eye pixels keep a restrained wet highlight.
classes=np.where(weight>.15,1,3).astype(np.uint8);classes[small.max(-1)<.08]=6
Image.fromarray(classes).save(T/'fish_material_classes.png')
rough=np.asarray(Image.open(raw/'texture_urls_0_roughness.png').convert('L').resize((1024,1024)),float)/255
rough=np.where(classes==6,.18,np.where(classes==1,.8,.85)+np.clip(rough-.5,-.08,.08))
spec=np.where(classes==6,1,np.where(classes==1,.25,.3))
orm=np.stack((spec,rough,np.zeros_like(rough)),axis=-1)
Image.fromarray(np.uint8(np.clip(orm,0,1)*255+.5)).save(T/'fish_orm.png')
mask=np.stack((weight,np.zeros_like(weight),np.zeros_like(weight),np.zeros_like(weight)),-1)
for name in palettes:
    preview=TT.apply(small,mask,[ramps[name]])
    Image.fromarray(np.uint8(np.clip(preview,0,1)*255+.5)).save(P/f'review/fish_{name}.png')
report={'texture_geometry_uv_max_error':error,'normal_correlation_before':corr,'normal_correlation_after':measure(normal),
        'native_palette_statistics':stats,'ramp_fit':fit,'basecolor_size':list(Image.open(T/'fish_basecolor.png').size),
        'normal_orm_mask_size':[1024,1024],'material_classes':{'1':'skin','3':'fin membrane','6':'eye'},
        'specular_mask':True,'metallic':0,'raw_retexture':str(raw.relative_to(P))}
(T/'texture_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
