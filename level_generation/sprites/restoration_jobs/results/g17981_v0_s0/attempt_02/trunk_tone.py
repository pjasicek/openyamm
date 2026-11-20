from pathlib import Path
import numpy as np,json
from PIL import Image
p=Path(__file__).resolve().parent
k=next(iter(json.loads((p/'checks.json').read_text())['frames']))
a=np.array(Image.open(p/f'{k}.png').convert('RGBA'));n=np.array(Image.open(p.parents[2]/'native'/f'{k}.png').convert('RGBA'))
Image.fromarray(a).save(p/f'{k}.before_trunk.png')
y=np.arange(a.shape[0])[:,None]/a.shape[0];ny=np.arange(n.shape[0])[:,None]/n.shape[0]
s=a[:,:,:3][(a[:,:,3]>=192)&(y>.77)]/255;t=n[:,:,:3][(n[:,:,3]>=192)&(ny>.77)].mean(0)/255
gam=[]
for c in range(3):
 lo,hi=.1,5.
 for _ in range(40):
  mid=(lo+hi)/2
  if (s[:,c]**mid).mean()>t[c]:lo=mid
  else:hi=mid
 gam.append((lo+hi)/2)
rgb=a[:,:,:3].astype(float);graded=(rgb/255)**np.array(gam)*255
w=np.clip((y-.70)/.05,0,1)[:,:,None]
a[:,:,:3]=np.clip(np.rint(rgb*(1-w)+graded*w),0,255).astype(np.uint8)
Image.fromarray(a).save(p/f'{k}.png')
(p/'trunk_tone.json').write_text(json.dumps({'gamma':gam,'native_mean':(t*255).tolist(),'region':'lower trunk y>.77; blend .70-.75','alpha':'unchanged'},indent=2)+'\n')
