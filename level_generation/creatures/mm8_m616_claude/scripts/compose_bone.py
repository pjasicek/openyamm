"""Bone and torn membrane materials; all native tiers use palette 616."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];REPO=P.parents[2]
sys.path[:0]=[str(P.parent/'mm6_gob_claude/scripts'),str(P.parent/'claude_shared'),str(REPO/'tools')]
import compose_textures_v2 as C
import region_variants as RV
import normal_map_convention as NM
T=P/'textures';S=P/'meshy/retexture_v1'
part,xyz=C.rasterise(np.load(P/'work/uv3d.npz'),tol=0);valid=part>=0
base=C.load(S/'texture_urls_0_base_color.png')
lum=base@RV.LUMA
membrane=np.isin(part,[1,2])&(ndimage.gaussian_filter(lum,.8)<.34)
ao=np.asarray(Image.open(T/'m616_ao.png').convert('L'),np.float32)/255
base*=.9+.1*ndimage.gaussian_filter(ao,1)[...,None]
base=np.clip(base,0,1)
nearest=ndimage.distance_transform_edt(~valid,return_distances=False,return_indices=True)
base[~valid]=base[tuple(nearest[:,~valid])]
# Thin bone islands amplify generation grain; retain cavities while softening only the ivory surface.
smooth=ndimage.gaussian_filter(base,(.8,.8,0))
weight=(~membrane)*np.clip((lum-.15)/.3,0,1)*.8
base=base*(1-weight[...,None])+np.clip(.75+.6*(smooth-.75),0,1)*weight[...,None]
classes=np.zeros(part.shape,np.uint8);classes[valid]=5;classes[membrane]=3
Image.fromarray(classes).resize((1024,1024),Image.Resampling.NEAREST).save(T/'m616_material_classes.png')
padded=classes.copy();padded[~valid]=padded[tuple(nearest[:,~valid])]
rough=np.where(padded==3,.91,.67);spec=np.where(padded==3,.02,.38)
orm=np.dstack([spec,rough,np.zeros_like(rough)])
Image.fromarray((orm*255+.5).astype(np.uint8)).resize((1024,1024),Image.Resampling.LANCZOS).save(T/'m616_metal_rough.png')
Image.fromarray((base*255+.5).astype(np.uint8)).save(T/'m616_basecolor.png')
normal=np.array(Image.open(S/'texture_urls_0_normal.png').convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS));before=NM.measure(normal)
if before<-.1:normal[...,1]=255-normal[...,1]
bone=np.asarray(Image.fromarray((padded==5).astype(np.uint8)*255).resize((1024,1024),Image.Resampling.NEAREST))>127
vec=normal.astype(np.float32)/127.5-1
vec[bone,:2]*=.35
vec/=np.maximum(np.linalg.norm(vec,axis=2,keepdims=True),1e-6)
normal=np.clip((vec+1)*127.5+.5,0,255).astype(np.uint8)
Image.fromarray(normal).save(T/'m616_normal.png')
# Native tiers differ in size, not colour: zero coverage preserves the shared base exactly.
Image.new('RGBA',(1024,1024),(0,0,0,0)).save(T/'m616_region_mask.png')
variants=['m616_a','m616_b','m616_c']
identity=dict(range=[0,1],colors=[[i/15]*3 for i in range(16)])
config=dict(variants=variants,palettes={k:616 for k in variants},regions=['native shared palette; no recolour'],materials=[dict(base='BoneDragon_A',prefix='BoneDragon',mask='m616_region_mask.png',ramps={k:[identity] for k in variants})])
(T/'m616_ramps.json').write_text(json.dumps(config,indent=2)+'\n')
(P/'review/texture_audit.json').write_text(json.dumps(dict(normal_before=before,normal_after=NM.measure(normal),classes=np.unique(classes).tolist(),bone_roughness=.67,membrane_roughness=.91,metallic=0,orm_red='specular mask; AO retained separately',native_tiers='All three use palette 616; zero region coverage leaves the common base unchanged.'),indent=2)+'\n')
print('COMPOSED',before,NM.measure(normal))
