"""Padding from an explicit white ray-hit bake, never guessing coverage from dark artwork."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
P=Path(__file__).resolve().parents[1];T=P/'textures/round2';report={}
for prefix in ['lch','lch_head']:
 coverage=np.array(Image.open(T/f'{prefix}_coverage.png').convert('RGB'))[:,:,0]>250
 assert .1<coverage.mean()<1,coverage.mean()
 _,indices=distance_transform_edt(~coverage,return_indices=True)
 for suffix in ['basecolor_1k','normal_1k','metal_rough_1k','region_mask']:
  f=T/f'{prefix}_{suffix}.png';a=np.array(Image.open(f).convert('RGBA'));a[~coverage]=a[indices[0][~coverage],indices[1][~coverage]]
  if suffix=='region_mask':a[:,:,1:]=0
  else:a[:,:,3]=255
  Image.fromarray(a).save(f)
 report[prefix]={'valid_fraction':float(coverage.mean()),'padded_fraction':float((~coverage).mean())}
(P/'review/triangle_rebake/padding.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
