"""Check authoring joins and preserve native shore coverage away from repaired tile borders."""
from pathlib import Path
import json,numpy as np
from PIL import Image
P=Path(__file__).resolve().parent;L=P.parent/'mm6_new_sorpigal_transitions';C=P.parent/'mm6_new_sorpigal'
r=json.loads((P/'reports/validation_v1.json').read_text())
land={f.stem:np.array(Image.open(f).convert('RGB'),dtype=int) for f in (L/'composites/v5').glob('*.png')}
shore={f.stem:np.array(Image.open(f),dtype=int) for f in (P/'authoring/v1').glob('6wtrdr*.png')}
fail=[]
for frame in range(14):
 water=np.array(Image.open(P/'authoring/v1'/f'6hdwtr{frame:03}.png'),dtype=int)
 images={**land,'6wtrtyl':water}
 for n,rgba in shore.items():
  a=rgba[:,:,3:]/255;images[n]=np.rint(rgba[:,:,:3]*a+water*(1-a)).astype(int)
 for check in r['checks']:
  a,b=images[check['a']],images[check['b']]
  d=abs(a[:,-1]-b[:,0]) if check['side']=='E' else abs(a[-1]-b[0])
  if d.max()>1:fail.append({'frame':frame,**check})
assert not fail,fail
for n,a in shore.items():
 source=np.array(Image.open(C/'alpha/shore_visible'/f'{n}.png').resize((512,512),Image.Resampling.NEAREST))>127
 assert np.array_equal((a[:,:,3]>127)[64:-64,64:-64],source[64:-64,64:-64])
r['authoring_checks']={'size':512,'joins_per_frame':len(r['checks']),'frames':14,'failures':fail,'central_384px_native_coverage_unchanged':True}
(P/'reports/validation_v1.json').write_text(json.dumps(r,indent=2)+'\n')
print('Authoring joins and native interior coverage verified.')
