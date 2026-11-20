from pathlib import Path
import json
import numpy as np
from PIL import Image
p=Path(__file__).resolve().parent
root=p.parents[2]
keys=list(json.loads((p/'checks.json').read_text())['frames'])
pairs=[]
for k in keys:
 f=p/f'{k}.png';b=p/f'{k}.before_tone.png'
 if not b.exists():b.write_bytes(f.read_bytes())
 a=np.array(Image.open(b).convert('RGBA'));n=np.array(Image.open(root/'native'/f'{k}.png').convert('RGBA'));pairs.append((k,a,n))
reports={}
for label, start, end in [('crystal',0,50),('base',50,65)]:
 target=np.concatenate([n[start:end,:,:3][n[start:end,:,3]>=192] for _,a,n in pairs]).mean(axis=0)/255
 sample=np.concatenate([a[start*2:end*2,:,:3][a[start*2:end*2,:,3]>=192] for _,a,n in pairs])/255
 gammas=[]
 for c in range(3):
  lo,hi=.1,5.
  for _ in range(40):
   mid=(lo+hi)/2
   if (sample[:,c]**mid).mean()>target[c]:lo=mid
   else:hi=mid
  gammas.append((lo+hi)/2)
 for k,a,n in pairs:
  a[start*2:end*2,:,:3]=np.rint((a[start*2:end*2,:,:3]/255)**np.array(gammas)*255).astype(np.uint8)
 reports[label]={'native_opaque_rgb':(target*255).tolist(),'gamma':gammas}
for k,a,n in pairs: Image.fromarray(a).save(p/f'{k}.png')
(p/'tone.json').write_text(json.dumps({'regions':reports,'split_native_y':50,'alpha':'unchanged'},indent=2)+'\n')
