"""Normalize generated master fidelity, make periodic boundaries, and preserve variant base phase."""
import json
import cv2
import numpy as np
from scipy.ndimage import gaussian_filter,binary_dilation,distance_transform_edt
from PIL import Image,ImageDraw
from common import *
from inventory import GROUPS

def main():
 report=[];masters={}
 for g in ('dirt','grass','sand','snow','swamp','waste','roads'):
  native=read(P/'references'/((GROUPS[g][0] or '7drsrcros')+'.png'),512)
  raw=M/'raw'/('roads_v2.png' if g=='roads' else f'{g}.png')
  a=read(raw,512)
  if g=='roads':
   chroma=(native[:,:,0]-native[:,:,2])/np.maximum(native.mean(2),1)
   target=native[chroma<.3].reshape(-1,1,3)
  else:target=native
  a=tone(a,target);a=seams.periodic(a);masters[g]=a
  save(M/'materials'/f'{g}.png',a)
  runtime=seams.reduce(seams.pad(a,'wrap'));save(M/'runtime'/f'{g}.png',runtime)
  if GROUPS[g][0]:save(OUT/(GROUPS[g][0]+'.png'),runtime)
  repeat=np.tile(runtime,(3,3,1));save(M/'reviews'/f'{g}_repeat.png',repeat)
  save(M/'reviews'/f'{g}_offset.png',np.roll(runtime,(128,128),(0,1)))
  report.append(dict(material=g,raw=str(raw.relative_to(P)),raw_sha256=sha(raw),authoring_sha256=sha(M/'materials'/f'{g}.png'),mean_rgb=runtime.mean((0,1)).tolist(),native_mean_rgb=target.mean((0,1)).tolist()))
 for name,g in [('7dirt1','dirt'),('7dirt2','dirt'),('7swtylv1','swamp'),('7swtylv2','swamp')]:
  a=read(M/'raw'/f'{name}.png',512);original=read(P/'references'/f'{name}.png',512)
  a=tone(a,original)
  base=read(P/'references'/(GROUPS[g][0]+'.png'))
  old=read(P/'references'/f'{name}.png')
  changed=np.max(abs(old-base),2)>3
  changed=binary_dilation(changed,iterations=2)
  coverage=np.clip(up(changed.astype(float)),0,1)
  # Register generated details before inserting only native variant regions.
  flow=cv2.calcOpticalFlowFarneback(cv2.cvtColor(seams.byte(original),cv2.COLOR_RGB2GRAY),cv2.cvtColor(seams.byte(a),cv2.COLOR_RGB2GRAY),None,.5,4,41,7,7,1.5,0)
  yy,xx=np.mgrid[:512,:512].astype('float32')
  a=cv2.remap(a.astype('float32'),xx+flow[:,:,0],yy+flow[:,:,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_WRAP)
  distance=np.minimum.reduce([xx,yy,511-xx,511-yy]);weight=np.clip((distance-16)/16,0,1)
  coverage=gaussian_filter(coverage,2)*weight
  result=seams.srgb(seams.linear(masters[g])*(1-coverage[:,:,None])+seams.linear(a)*coverage[:,:,None])
  save(M/'variants'/f'{name}.png',result);save(OUT/f'{name}.png',seams.reduce(seams.pad(result,'wrap')))
  save(M/'variant_masks'/f'{name}.png',coverage*255)
 sheet=Image.new('RGB',(1024,7*280),'#202933');draw=ImageDraw.Draw(sheet)
 for row,g in enumerate(masters):
  for col,im in enumerate([Image.open(P/'references'/((GROUPS[g][0] or '7drsrcros')+'.png')).resize((256,256)),Image.open(M/'runtime'/f'{g}.png'),Image.open(M/'reviews'/f'{g}_offset.png')]):
   sheet.paste(im,(col*256,row*280+24));draw.text((col*256+5,row*280+5),g+' '+['original','x2','half-offset'][col],fill='white')
 sheet.save(M/'reviews/comparison.png')
 (M/'report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
