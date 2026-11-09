"""Insert imagegen's narrow seam repairs, retain accepted master interiors, and constrain shared samples."""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parent
S=P.parent/'mm6_new_sorpigal_master_study'
D=json.loads((S/'material_decisions.json').read_text())
out=P/'material_seams/connected_v2';out.mkdir(exist_ok=True)
records=[]
for name in ['grass','dirt','volcano','cobbles']:
 source=S/D[name]['master_png'];original=np.asarray(Image.open(source).convert('RGB'),dtype=float)
 a=original.copy()
 if name not in ('grass','dirt'):
  shifted=np.roll(np.roll(a,256,0),256,1)
  raw=P/'material_seams'/(name+'_repair_raw.png')
  with Image.open(raw) as im:repair=np.asarray(im.convert('RGB').resize((512,512),Image.Resampling.LANCZOS),dtype=float)
  y,x=np.mgrid[:512,:512];distance=np.minimum(abs(x-255.5),abs(y-255.5))
  t=np.clip((32-distance)/16,0,1);alpha=(t*t*(3-2*t))[:,:,None]
  shifted=shifted*(1-alpha)+repair*alpha
  a=np.roll(np.roll(shifted,-256,0),-256,1)
 # A shared symmetric 8px sample strip makes clamped Lanczos exports agree across opposite edges.
 # Fade this mechanical sampling constraint out by16px; no interior recolouring.
 for axis in [0,1]:
  for i in range(16):
   weight=1 if i<8 else (16-i)/8
   if axis==0:
    average=(a[i]+a[-1-i])/2;a[i]=a[i]*(1-weight)+average*weight;a[-1-i]=a[-1-i]*(1-weight)+average*weight
   else:
    average=(a[:,i]+a[:,-1-i])/2;a[:,i]=a[:,i]*(1-weight)+average*weight;a[:,-1-i]=a[:,-1-i]*(1-weight)+average*weight
 a=np.rint(a).astype('uint8');assert np.array_equal(a[32:-32,32:-32],original[32:-32,32:-32])
 image=Image.fromarray(a);image.save(out/(name+'.png'))
 small=image.resize((256,256),Image.Resampling.LANCZOS);small.save(out/(name+'_256.png'))
 pixels=np.asarray(small,dtype=int)
 assert np.array_equal(pixels[:,0],pixels[:,-1]) and np.array_equal(pixels[0],pixels[-1])
 repeat=Image.new('RGB',(1280,1280))
 for y in range(5):
  for x in range(5):repeat.paste(small,(x*256,y*256))
 repeat.save(out/(name+'_repeat.png'))
 records.append({'material':name,'source':str(source.relative_to(S)),
                 'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                 'output_sha256':hashlib.sha256((out/(name+'.png')).read_bytes()).hexdigest(),
                 'central_448x448_pixels_unchanged':True,'runtime_opposite_edges_exact':True,
                 'imagegen_repair':None if name in ('grass','dirt') else 'material_seams/'+name+'_repair_raw.png',
                 'method':'Imagegen boundary repair inserted within32px of outer edges; shared symmetric8px sampling strip faded by16px.'})
(P/'reports/material_seams_v2.json').write_text(json.dumps(records,indent=2)+'\n')
print('Prepared four seam-constrained derivatives; all accepted central448x448 interiors unchanged.')
