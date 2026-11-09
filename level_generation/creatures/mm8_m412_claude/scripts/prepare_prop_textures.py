from pathlib import Path
import json,numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
p=Path('level_generation/creatures/mm8_m412_claude');d=p/'textures/props';d.mkdir(parents=True,exist_ok=True)
im=Image.open(p/'references_props/cutlass.png').convert('RGBA');a=np.array(im);mask=a[:,:,3]>128
rows={}
for y in [25,50,85,130,190,260,340,420,500,580,660,740,820,900,970,1030,1080,1110,1140]:
 xs=np.where(mask[y])[0];splits=np.split(xs,np.where(np.diff(xs)>1)[0]+1);run=max(splits,key=lambda x:x[-1]);rows[y]=[int(run[0]),int(run[-1])]
rows[1140]=[453,542]
# One crop retains the entire sword; transparent exterior bleeds the nearest valid colour for mip filtering.
box=(285,12,740,1465);crop=a[box[1]:box[3],box[0]:box[2]];valid=crop[:,:,3]>128
inds=distance_transform_edt(~valid,return_distances=False,return_indices=True);rgb=crop[:,:,:3][tuple(inds)]
tex=Image.fromarray(rgb).resize((320,1024),Image.Resampling.LANCZOS);tex.save(d/'cutlass_basecolor.png')
hsv=np.array(tex.convert('HSV'));green=(hsv[:,:,0]>35)&(hsv[:,:,0]<80)&(hsv[:,:,1]>80)
region=np.zeros((1024,320,4),np.uint8);region[:,:,0]=green*255;Image.fromarray(region).save(d/'cutlass_region_mask.png')
orm=np.empty((1024,320,3),np.uint8);orm[:]=[210,90,0];orm[green]=[50,175,0];Image.fromarray(orm).save(d/'cutlass_orm.png')
Image.new('RGB',(320,1024),(128,128,255)).save(d/'cutlass_normal.png')
(d/'cutlass_profile.json').write_text(json.dumps({'rows':rows,'crop':box,'grip_centre':[477,1300],'metres_per_pixel':.72/(1140-25)},indent=2))
print('PROP textures',tex.size,'green texels',int(green.sum()),'blade samples',len(rows))
