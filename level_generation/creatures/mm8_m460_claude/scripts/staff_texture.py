"""Bake the selected prop reference into a narrow padded texture and silhouette profile."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
p=Path('level_generation/creatures/mm8_m460_claude');out=p/'textures/props';out.mkdir(exist_ok=True)
im=Image.open(p/'references_props/staff_front.png').convert('RGBA');a=np.array(im);solid=a[:,:,3]>200
indices=distance_transform_edt(~solid,return_distances=False,return_indices=True)
rgb=a[:,:,:3][tuple(indices)]
Image.fromarray(rgb[:,464:560]).resize((128,1024),Image.Resampling.LANCZOS).save(out/'staff_basecolor.png')
rows={}
for y in range(30,1500):
    xs=np.where(solid[y])[0]
    assert len(xs),y
    rows[y]=[int(xs.min()),int(xs.max())]
profile={'rows':rows,'crop_x0':464,'crop_width':96,'source_height':1536,'top_row':30,'bottom_row':1499,'length_m':1.8,'grip_from_butt_m':1.2,'radius_scale':.65,'source':'references_props/staff_front.png'}
(out/'staff_profile.json').write_text(json.dumps(profile,indent=2)+'\n')
print('Staff texture padded and silhouette profiled; no extra paid generation.')
