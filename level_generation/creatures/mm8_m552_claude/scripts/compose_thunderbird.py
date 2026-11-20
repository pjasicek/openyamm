"""Shared bird materials; two luminance ramps retain the native brown/olive palette distinction."""
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
base=C.load(S/'texture_urls_0_base_color.png');h,s,v=C.hsv(base)
eye=np.isin(part,[3,5]);beak=(part==0)&(xyz[...,1]<-.178)
feet=(part>=100)|((part==0)&(xyz[...,1]>.075)&(xyz[...,2]<.06))
protected=eye|beak|feet
# Native beak has a warm red tip; retain the generated horn shading and the ochre cere.
tip=beak&(xyz[...,1]<-.197)
base[tip]*=np.array([1.,.28,.20])
ao=np.asarray(Image.open(T/'m552_ao.png').convert('L'),np.float32)/255
base*=.8+.2*ndimage.gaussian_filter(ao,1)[...,None]
lum0=base@RV.LUMA
smooth=ndimage.gaussian_filter(lum0,1.5)
base*=((smooth+.5*(lum0-smooth))/np.maximum(lum0,1e-4))[...,None]
base=np.clip(base,0,1)
nearest=ndimage.distance_transform_edt(~valid,return_distances=False,return_indices=True)
region=(h>=55).astype(np.int32)
weights=[]
for index in range(4):
 mask=((region==index)&valid&~protected).astype(np.float32)
 mask[~valid]=mask[tuple(nearest[:,~valid])]
 weights.append(ndimage.gaussian_filter(mask,.65))
RV.write_mask(weights,T/'m552_region_mask.png')
classes=np.zeros(part.shape,np.uint8);classes[valid]=11;classes[feet|beak]=4;classes[eye]=6
Image.fromarray(classes).resize((1024,1024),Image.Resampling.NEAREST).save(T/'m552_material_classes.png')
padded=classes.copy();padded[~valid]=padded[tuple(nearest[:,~valid])]
rough=np.array([.8,.82,.85,.87,.48,.38,.18,.72,.8,.3,.8,.9],np.float32)[padded]
spec=np.array([0,.04,.02,.02,.55,.65,.9,.12,.04,1,.02,.025],np.float32)[padded]
orm=np.dstack([spec,rough,np.zeros_like(rough)])
Image.fromarray((orm*255+.5).astype(np.uint8)).resize((1024,1024),Image.Resampling.LANCZOS).save(T/'m552_metal_rough.png')
Image.fromarray((base*255+.5).astype(np.uint8)).save(T/'m552_basecolor.png')
normal=np.array(Image.open(S/'texture_urls_0_normal.png').convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS));before=NM.measure(normal)
if before<-.1:normal[...,1]=255-normal[...,1]
Image.fromarray(normal).save(T/'m552_normal.png')
source=json.loads((P/'references/native_sources.json').read_text())
palettes={int(pid):np.frombuffer((REPO/e['path']).read_bytes()[:768],np.uint8).reshape(256,3)/255 for pid,e in source['palette_sources'].items()}
indices=np.concatenate([np.asarray(Image.open(REPO/source['sources'][f'm552sa{view}']['path'])).ravel() for view in range(5)]);indices=indices[indices!=0]
ph,ps,pv=C.hsv(palettes[553]);changed=np.any(abs(palettes[554]-palettes[553])>.01,axis=1)|np.any(abs(palettes[555]-palettes[553])>.01,axis=1)
pg=(ph>=55).astype(int)
graded=RV.load_srgb(T/'m552_basecolor.png',1024);lum=RV.luminance(graded)
mask=np.stack([np.asarray(ch,np.float32)/255 for ch in Image.open(T/'m552_region_mask.png').split()],-1)
variants={'m552_a':553,'m552_b':554,'m552_c':555};ramps={name:[] for name in variants};reports=[]
encode=lambda x:np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055)
for channel in range(2):
 core=mask[...,channel]>=.9;assert core.sum()>100
 order=np.argsort(lum[core]);rank=np.empty(order.size);rank[order]=(np.arange(order.size)+.5)/order.size
 ids=indices[(pg[indices]==channel)&(ps[indices]>.12)&(pv[indices]>.08)&((channel==1)|(ps[indices]<.75))];assert len(ids)>100
 targets={}
 for name,pid in variants.items():
  colors=RV.srgb_to_linear(np.clip(palettes[pid][ids]*(1.45 if channel==0 else 1.10),0,1));colors=colors[np.argsort(colors@RV.LUMA)]
  q=.06+.91*rank;target=graded.copy();target[core]=encode(np.clip(colors[np.minimum((q*len(colors)).astype(int),len(colors)-1)],0,1));targets[name]=target
 fitted,report=RV.fit_ramps(graded,targets,mask[...,channel])
 for name in variants:ramps[name].append(fitted[name])
 reports.append(report)
config=dict(variants=list(variants),palettes=variants,regions=['brown body plumage','olive flight feathers'],materials=[dict(base='Thunderbird_A',prefix='Thunderbird',mask='m552_region_mask.png',ramps=ramps)],report=reports)
(T/'m552_ramps.json').write_text(json.dumps(config,indent=2)+'\n')
(P/'review/texture_audit.json').write_text(json.dumps(dict(normal_before=before,normal_after=NM.measure(normal),classes=np.unique(classes).tolist(),material_11='body plumage, flight feathers and tail fan',orm_red='specular mask; AO retained separately',region_fit=reports),indent=2)+'\n')
print('COMPOSED',before,NM.measure(normal))
