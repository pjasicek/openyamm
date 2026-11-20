"""Replace v8 blurry stone interiors; retain its approved silhouette and exact boundary pixels."""
import sys,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from common import *
from scipy.ndimage import distance_transform_edt
names=['drsrne1','drsrne2','drsrnw1','drsrnw2']
raw=['exec-2eeb9472-af81-42fa-8641-43b497799b7f.png','exec-fbe1c0c7-57d6-4591-9dde-5136e2eeaac5.png','exec-7e507750-c110-4310-a2a7-ebb877182da4.png','exec-b6a4d7fb-4493-4558-80b5-8401af250035.png']
for d in ['runtime','masks']:
 (HERE/d).mkdir(exist_ok=True)
 for f in (HERE.parent/'v8'/d).glob('*.png'):shutil.copy2(f,HERE/d/f.name)
receipts=[]
for n,r in zip(names,raw):
 f=HERE/'raw'/(n+'.png')
 if not f.exists():shutil.copy2(Path('/home/pjasicek/.codex/generated_images/01a07fff-d641-78c1-a58a-4501f7c594bd')/r,f)
 generated=read(f,256)
 alpha=read(HERE.parent/'v8/masks'/(n+'.png'),256)[:,:,0]/255
 distance=distance_transform_edt(alpha>.5)
 coverage=np.clip((distance-.5)/1.5,0,1)*alpha
 for prefix in ['drsr','gdrd']:
  target=prefix+n[4:];old=read(HERE.parent/'v8/runtime'/(target+'.png'))
  result=old+(generated-old)*coverage[:,:,None]
  # Preserve the established ports, feathering their colour correction over
  # four runtime pixels. Full generated stone artwork remains elsewhere.
  for side in 'NSEW':
   view=result.transpose(1,0,2) if side in 'EW' else result
   original=old.transpose(1,0,2) if side in 'EW' else old
   if side in 'SE':view=view[::-1];original=original[::-1]
   delta=original[0]-view[0]
   for d in range(4):
    t=d/4;view[d]+=delta*(1-t*t*(3-2*t))
  result[0]=old[0];result[-1]=old[-1];result[:,0]=old[:,0];result[:,-1]=old[:,-1]
  save(HERE/'runtime'/(target+'.png'),result)
 receipts.append(dict(name=n,raw_sha256=sha(f),input_sha256=sha(HERE/'inputs'/(n+'.png'))))
build=json.loads((HERE.parent/'v8/build.json').read_text())
for r in build['tiles']:r['runtime_sha256']=sha(HERE/'runtime'/(r['name']+'.png'))
build['method']='Full generated stone artwork matched to accepted drsrns; approved v8 masks, dirt, shading and exact boundary RGB retained'
build.pop('boundary_method',None)
(HERE/'build.json').write_text(json.dumps(build,indent=2)+'\n')
(HERE/'generation.json').write_text(json.dumps(dict(tool='built-in imagegen',calls=4,prompt_sha256=sha(HERE/'prompts/material.txt'),material_reference_sha256=sha(HERE/'inputs/drsrns.png'),images=receipts),indent=2)+'\n')
