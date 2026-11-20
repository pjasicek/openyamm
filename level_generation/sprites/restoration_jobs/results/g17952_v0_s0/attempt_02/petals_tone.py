from pathlib import Path
import json,numpy as np
from PIL import Image
p=Path(__file__).resolve().parent;k=next(iter(json.loads((p/'checks.json').read_text())['frames']))
a=np.array(Image.open(p/f'{k}.png').convert('RGBA'));n=np.array(Image.open(p.parents[2]/'native'/f'{k}.png').convert('RGBA'));Image.fromarray(a).save(p/f'{k}.before_petals.png')
rgb=a[:,:,:3].astype(float);nr=n[:,:,:3].astype(float)
w=np.clip((rgb[:,:,0]-rgb[:,:,1]-4)/20,0,1);nw=np.clip((nr[:,:,0]-nr[:,:,1]-4)/20,0,1)
s=rgb[(w>.9)&(a[:,:,3]>=192)]/255;t=nr[(nw>.9)&(n[:,:,3]>=192)].mean(0)/255;gam=[]
for c in range(3):
 lo,hi=.1,5.
 for _ in range(40):
  mid=(lo+hi)/2
  if (s[:,c]**mid).mean()>t[c]:lo=mid
  else:hi=mid
 gam.append((lo+hi)/2)
g=(rgb/255)**np.array(gam)*255
a[:,:,:3]=np.clip(np.rint(rgb*(1-w[:,:,None])+g*w[:,:,None]),0,255).astype(np.uint8)
Image.fromarray(a).save(p/f'{k}.png');(p/'petals_tone.json').write_text(json.dumps({'gamma':gam,'native_mean':(t*255).tolist(),'alpha':'unchanged'},indent=2)+'\n')
