"""Shared Couatl textures and native palette ramps; anatomy protects eyes, teeth and the mouth."""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

P = Path(__file__).resolve().parents[1]
REPO = P.parents[2]
sys.path[:0] = [str(P.parent/'mm6_gob_claude/scripts'),str(P.parent/'claude_shared'),str(REPO/'tools')]
import compose_textures_v2 as C
import region_variants as RV
import normal_map_convention as NM
T = P/'textures'
S = P/'meshy/retexture_v1'
part, xyz = C.rasterise(np.load(P/'work/uv3d.npz'),tol=0)
valid = part >= 0
base = C.load(S/'texture_urls_0_base_color.png')
h,s,v = C.hsv(base)
eye = np.isin(part,[9,10])
fang = np.isin(part,[29,32])
mouth = part == 35
# The multiview projection put a pale eye-shaped patch on the lower body; repair only those measured texels.
body = np.isin(part,[0,34])
spill = body & (xyz[...,2] < .48) & (s < .32) & (v > .52)
good = body & ~spill & (s > .4)
nearest = ndimage.distance_transform_edt(~good,return_distances=False,return_indices=True)
base[spill] = base[tuple(nearest[:,spill])]
base[mouth] = (.16,.025,.045)
base[fang] = (.78,.72,.54)
ao = np.asarray(Image.open(T/'m408_ao.png').convert('L'),np.float32)/255
base *= (.8+.2*ao[...,None])
base = np.clip(base,0,1)
h,s,v = C.hsv(base)
region = np.zeros(part.shape,np.int32)
region[(h<30)|(h>=300)] = 1
region[(h>=30)&(h<85)] = 2
region[(h>=85)&(h<190)] = 3
region[(s<.18)&~eye] = 0
protected = eye|fang|mouth
nearest_valid = ndimage.distance_transform_edt(~valid,return_distances=False,return_indices=True)
weights = []
for index in range(4):
    mask = ((region==index)&valid&~protected).astype(np.float32)
    mask[~valid] = mask[tuple(nearest_valid[:,~valid])]
    mask = ndimage.gaussian_filter(mask,.65)
    weights.append(mask)
RV.write_mask(weights,T/'m408_region_mask.png')
classes = np.zeros(part.shape,np.uint8)
classes[valid] = 1
classes[np.isin(part,[4,5,6,7,8])] = 3
classes[valid & ~body & ~np.isin(part,[4,5,6,7,8,9,10,29,32,33,35])] = 11
classes[eye] = 6
classes[fang] = 5
classes[mouth] = 7
Image.fromarray(classes).resize((1024,1024),Image.Resampling.NEAREST).save(T/'m408_material_classes.png')
padded = classes.copy()
padded[~valid] = padded[tuple(nearest_valid[:,~valid])]
rough = np.array([.8,.82,.85,.87,.48,.38,.18,.72,.8,.3,.8,.9],np.float32)[padded]
spec = np.array([0,.04,.02,.02,.55,.65,.9,.12,.04,1,.02,.025],np.float32)[padded]
orm = np.dstack([spec,rough,np.zeros_like(rough)])
Image.fromarray((orm*255+.5).astype(np.uint8)).resize((1024,1024),Image.Resampling.LANCZOS).save(T/'m408_metal_rough.png')
Image.fromarray((base*255+.5).astype(np.uint8)).save(T/'m408_basecolor.png')
normal = np.array(Image.open(S/'texture_urls_0_normal.png').convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS))
before = NM.measure(normal)
if before < -.1:
    normal[...,1] = 255-normal[...,1]
Image.fromarray(normal).save(T/'m408_normal.png')

# Native palette entries are sampled from all genuine standing directions, keeping each tier's own colours.
source = json.loads((P.parent/'mm8_m408/sources.json').read_text())
palettes = {int(pid):np.frombuffer((REPO/entry['path']).read_bytes()[:768],np.uint8).reshape(256,3)/255
            for pid,entry in source['palette_sources'].items()}
indices = np.concatenate([np.asarray(Image.open(REPO/source['sources'][f'm408sa{view}']['path'])).ravel()
                          for view in range(5)])
indices = indices[indices!=0]
ph,ps,pv = C.hsv(palettes[408])
pg = np.zeros(256,np.int32)
pg[(ph<30)|(ph>=300)] = 1
pg[(ph>=30)&(ph<85)] = 2
pg[(ph>=85)&(ph<190)] = 3
graded = RV.load_srgb(T/'m408_basecolor.png',1024)
lum = RV.luminance(graded)
mask = np.stack([np.asarray(ch,np.float32)/255 for ch in Image.open(T/'m408_region_mask.png').split()],axis=-1)
variants = {'m408_a':408,'m408_b':410,'m408_c':411}
ramps = {name:[] for name in variants}
reports = []
encode = lambda x:np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055)
for channel in range(4):
    core = mask[...,channel] >= .9
    assert core.sum()>100
    order = np.argsort(lum[core]);rank=np.empty(order.size);rank[order]=(np.arange(order.size)+.5)/order.size
    ids = indices[(pg[indices]==channel)&(ps[indices]>.25)&(pv[indices]>.06)]
    assert len(ids)>100
    targets = {}
    for name,pid in variants.items():
        colors = RV.srgb_to_linear(palettes[pid][ids]);colors=colors[np.argsort(colors@RV.LUMA)]
        # Avoid the sprite's outline extremes while retaining its native per-region shading distribution.
        q = .06+.91*rank
        target=graded.copy();target[core]=encode(np.clip(colors[np.minimum((q*len(colors)).astype(int),len(colors)-1)]*1.4,0,1))
        targets[name]=target
    fitted,report = RV.fit_ramps(graded,targets,mask[...,channel])
    for name in variants:
        ramps[name].append(fitted[name])
    reports.append(report)
config=dict(variants=list(variants),palettes=variants,regions=['blue-violet scales','red-orange markings','gold belly and feather tips','green coverts'],
    materials=[dict(base='Couatl_A',prefix='Couatl',mask='m408_region_mask.png',ramps=ramps)],report=reports)
(T/'m408_ramps.json').write_text(json.dumps(config,indent=2)+'\n')
(P/'review/texture_audit.json').write_text(json.dumps(dict(projection_spill_texels=int(spill.sum()),normal_before=before,
    normal_after=NM.measure(normal),classes=np.unique(classes).tolist(),material_11='feathers and tail fan',
    orm_red='per-texel specular mask; separate AO retained',region_fit=reports),indent=2)+'\n')
print('COMPOSED',int(spill.sum()),'spill texels; normal',before,NM.measure(normal))
