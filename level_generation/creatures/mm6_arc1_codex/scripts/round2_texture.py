"""Transfer the accepted leather surface by mirrored 3D position into the right bracer's UV island."""
import json,numpy as np
from pathlib import Path
from PIL import Image
from scipy.spatial import cKDTree
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';B=P/'review/round2/baseline/textures'
m=np.load(P/'work/uvraster_UVMap.npz');part=m['piece'];xyz=m['pos'];right=part==11;left=part==12
src=np.argwhere(left);target=xyz[right].copy();target[:,0]*=-1;distance,index=cKDTree(xyz[left]).query(target);lookup=src[index]
_,pad=ndimage.distance_transform_edt(part<0,return_indices=True);near=right[tuple(pad)]&(part<0);near &= ndimage.distance_transform_edt(~right)<12
for filename in ['arc1_basecolor_1k.png','arc1_metal_rough_1k.png']:
 im=np.array(Image.open(B/filename));im[right]=im[lookup[:,0],lookup[:,1]];im[near]=im[tuple(pad[:,near])];Image.fromarray(im).save(T/filename)
cl=np.array(Image.open(B/'arc1_material_classes.png'));cl[right|near]=8;Image.fromarray(cl).save(T/'arc1_material_classes.png')
mask=np.array(Image.open(B/'arc1_region_mask.png'));mask[right|near]=0;Image.fromarray(mask).save(T/'arc1_region_mask.png')
report={'right_texels':int(right.sum()),'left_texels':int(left.sum()),'mirrored_surface_distance_m':{'mean':float(distance.mean()),'max':float(distance.max())},'tiers':'shared maps, excluded from cloth colour ramp','reference_note':'HD front omitted the right bracer; explicit review round 2 corrects that omission using the existing left leather.'}
(P/'review/round2/bracer_transfer.json').write_text(json.dumps(report,indent=2));print(report)

# Skin highlights must not undershoot the native face. Fade the grade out at the neck seam.
d=np.load(P/'work/uvraster_HeadUV.npz');rgb=np.array(Image.open(B/'arc1_head_basecolor_1k.png').convert('RGB'),float)/255;skin=d['piece']==0
weight=skin*np.clip((d['pos'][:,:,2]-1.47)/.025,0,1);rgb*=1+.085*weight[:,:,None]
covered=d['piece']>=0;_,pad=ndimage.distance_transform_edt(~covered,return_indices=True);rgb[~covered]=rgb[tuple(pad[:,~covered])];Image.fromarray((np.clip(rgb,0,1)*255+.5).astype('uint8')).save(T/'arc1_head_basecolor_1k.png')
