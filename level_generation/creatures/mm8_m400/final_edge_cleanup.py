from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy import ndimage
ROOT=Path(__file__).resolve().parent
reg=json.loads((ROOT/'registration.json').read_text());counts={}
for n in reg:
 counts[n]={}
 for folder in ('cleaned','aligned_2x'):
  p=ROOT/f'{folder}/{n}.png';a=np.array(Image.open(p).convert('RGBA'));c=a[:,:,:3].astype(float);alpha=a[:,:,3]
  band=(alpha>0)&((ndimage.distance_transform_edt(alpha>=250)<=3)|(alpha<255))
  maximum=c.max(axis=2);minimum=c.min(axis=2);pale=(c@np.array([.2126,.7152,.0722])>110)&((maximum-minimum)/np.maximum(maximum,1)<.30)
  excess=c[:,:,1]-np.maximum(c[:,:,0],c[:,:,2]);selected=band&pale&(excess>0)
  a[:,:,1][selected]=np.maximum(a[:,:,0],a[:,:,2])[selected]
  counts[n][folder]=int(selected.sum());Image.fromarray(a).save(p)
report={'method':'Neutralize demonstrated green compensation cast only on pale low-chroma pixels in the 3px alpha contour; cap G at max(R,B). Alpha, colored garment interiors and dark teal skin remain unchanged.','luminance_min':110,'relative_chroma_max':.30,'band_px':3,'changed_pixels':counts}
(ROOT/'review/final_edge_cleanup.json').write_text(json.dumps(report,indent=2)+'\n')
print('Neutralized pale contour pixels:',sum(sum(v.values()) for v in counts.values()))
