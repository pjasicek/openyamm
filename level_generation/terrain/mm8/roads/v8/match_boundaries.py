"""Harmonize boundary colours using original diagonal endpoint samples, without spatial warping."""
import sys,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from common import *
b=json.loads((HERE/'build.json').read_text())
profiles={}
for prefix in ('drsr','gdrd'):
 for axis,sides in [('vertical','NS'),('horizontal','WE')]:
  samples=[]
  for r in b['tiles']:
   if not r['name'].startswith(prefix) or r['name'][-3:] not in ('ne1','ne2','nw1','nw2'):continue
   im=read(HERE/'runtime'/(r['name']+'.png'))
   for s in sides:
    if r['topology'][s]:samples.append({'N':im[0],'S':im[-1],'W':im[:,0],'E':im[:,-1]}[s])
  profiles[prefix,axis]=np.mean(samples,axis=0)
for r in b['tiles']:
 im=read(HERE/'runtime'/(r['name']+'.png'))
 for side,opened in r['topology'].items():
  if not opened:continue
  view=im.transpose(1,0,2) if side in 'EW' else im
  if side in 'ES':view=view[::-1]
  profile=profiles[r['name'][:4],'horizontal' if side in 'EW' else 'vertical']
  delta=profile-view[0]
  for d in range(12):
   t=d/12
   view[d]+=delta*(1-t*t*(3-2*t))
 save(HERE/'runtime'/(r['name']+'.png'),im)
 r['runtime_sha256']=sha(HERE/'runtime'/(r['name']+'.png'))
b['boundary_method']='Average native diagonal endpoint RGB; smooth colour delta over12 runtime pixels; no coordinate warping or donor strips'
(HERE/'build.json').write_text(json.dumps(b,indent=2)+'\n')
